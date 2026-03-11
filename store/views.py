from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Product, Sale, Claim, SaleDetail, Employee, Customer

# Dashboard
def dashboard(request):
    total_products = Product.objects.count()
    total_sales_dict = Sale.objects.aggregate(Sum('total_amount'))
    total_sales = total_sales_dict['total_amount__sum'] or 0
    total_claims = Claim.objects.filter(status='Processing').count()
    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_claims': total_claims,
    }
    return render(request, 'store/dashboard.html', context)

# Product List
def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

# Claim List
def claim_list(request):
    claims = Claim.objects.all().order_by('-claim_date')
    return render(request, 'store/claim_list.html', {'claims': claims})

# Add Claim
def add_claim(request):
    if request.method == "POST":
        pro_id = request.POST.get('pro_id')
        cus_id = request.POST.get('cus_id')
        problem = request.POST.get('problem')
        
        product = get_object_or_404(Product, pro_id=pro_id)
        customer = get_object_or_404(Customer, cus_id=cus_id)
        
        # สร้างรหัสเคลมอัตโนมัติ
        claim_id = f"CLM{int(timezone.now().timestamp())}"
        
        Claim.objects.create(
            claim_id=claim_id,
            pro=product,
            cus=customer,
            problem_description=problem,
            status='Processing'
        )
        return redirect('claim_list')
    
    products = Product.objects.all()
    customers = Customer.objects.all()
    return render(request, 'store/add_claim.html', {'products': products, 'customers': customers})

# POS Page (ຈັດການທັງສະແດງສິນຄ້າ ແລະ ຄິດໄລ່ເງິນລວມ)
def pos(request):
    products = Product.objects.filter(qty__gt=0)
    cart = request.session.get('cart', {})
    
    total_price = 0
    for item in cart.values():
        total_price += item['price'] * item['quantity']
        
    context = {
        'products': products,
        'total_price': total_price,
    }
    return render(request, 'store/pos.html', context)

# Add to cart
def add_to_cart(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    cart = request.session.get('cart', {})
    if pro_id in cart:
        cart[pro_id]['quantity'] += 1
    else:
        cart[pro_id] = {
            'name': product.pro_name,
            'price': float(product.price_sale),
            'quantity': 1
        }
    request.session['cart'] = cart
    return redirect('pos')

# Clear cart
def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('pos')

# Checkout and save to Database
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('pos')
    
    # ສົມມຸດໃຊ້ພະນັກງານຄົນທຳອິດໃນລະບົບ (ທ່ານຄວນແລກເພີ່ມ Employee ໃນ Admin ກ່ອນເດີ້)
    emp = Employee.objects.first() 
    if not emp:
        # ຖ້າຍັງບໍ່ມີພະນັກງານໃນ DB ໃຫ້ສ້າງຕົວຈຳລອງຂຶ້ນມາເພື່ອບໍ່ໃຫ້ Error
        emp = Employee.objects.create(emp_id="EMP001", emp_name="Admin")
    
    total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
    sale_id = f"S{int(timezone.now().timestamp())}"
    
    new_sale = Sale.objects.create(
        sale_id=sale_id,
        total_amount=total_amount,
        emp=emp,
        status='Paid'   
    )
    
    for pro_id, item in cart.items():
        product = Product.objects.get(pro_id=pro_id)
        SaleDetail.objects.create(
            sale=new_sale,
            pro=product,
            qty=item['quantity'],
            price=item['price']
        )
        product.qty -= item['quantity']
        product.save()
        
    request.session['cart'] = {}
    
    # ສົ່ງໄປໜ້າໃບບິນຫຼັງຈາກຂາຍສຳເລັດ
    return redirect('receipt', sale_id=new_sale.sale_id)

# Receipt View
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    details = SaleDetail.objects.filter(sale=sale)
    return render(request, 'store/receipt.html', {
        'sale': sale,
        'details': details
    })
    
def sales_report(request):
    # ດຶງລາຍການຂາຍທັງໝົດ ແລະ ລຽງຈາກໃໝ່ຫາເກົ່າ
    sales = Sale.objects.all().order_by('-sale_date')
    
    # ຄິດໄລ່ຍອດລວມ
    total_sales_amount = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Sale.objects.count()

    context = {
        'sales': sales,
        'total_sales_amount': total_sales_amount,
        'total_orders': total_orders,
    }
    return render(request, 'store/sales_report.html', context)