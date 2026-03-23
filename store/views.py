from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib import messages
from .models import Product, Sale, Claim, SaleDetail, Employee, Customer, ShopInfo, Supplier, StockImport, ImportDetail, Category, Brand, Unit

# ຟັງຊັນເຂົ້າສູ່ລະບົບ (Login)
def login_view(request):
    # ຖ້າລັອກອິນແລ້ວ ໃຫ້ປັດໄປໜ້າຫຼັກເລີຍ
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        # ກວດສອບຊື່ຜູ້ໃຊ້ ແລະ ລະຫັດຜ່ານ
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'ຍິນດີຕ້ອນຮັບ {user.username} ເຂົ້າສູ່ລະບົບ!')
            return redirect('dashboard')
        else:
            messages.error(request, 'ຊື່ຜູ້ໃຊ້ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ! ກະລຸນາລອງໃໝ່.')

    # ສົ່ງໜ້າຮ້ານໄປສະແດງໂລໂກ້ຢູ່ໜ້າ Login (ຖ້າມີ)
    shop = ShopInfo.objects.first()
    return render(request, 'store/login.html', {'shop': shop})

# ຟັງຊັນອອກຈາກລະບົບ (Logout)
def logout_view(request):
    logout(request)
    messages.success(request, 'ທ່ານໄດ້ອອກຈາກລະບົບແລ້ວ.')
    return redirect('login')

# Dashboard
def dashboard(request):
    total_products = Product.objects.count()
    total_sales_dict = Sale.objects.aggregate(Sum('total_amount'))
    total_sales = total_sales_dict['total_amount__sum'] or 0
    total_orders = Sale.objects.count()
    total_claims = Claim.objects.filter(status='Processing').count()
    
    # ດຶງລາຍການຂາຍ 5 ລາຍການລ່າສຸດ ແລ້ວເກັບໄວ້ໃນ recent_sales ແລະ ສະແດງໃນ dashboard.html
    recent_sales = Sale.objects.all().order_by('-sale_date')[:5]
    
    # ດຶງລາຍການສິນຄ້າທີ່ stock ຕໍ່ມານ້ອຍ ແລ້ວເກັັບໄວ້ໃນ low_stock_products ແລະ ສະແດງໃນ dashboard.html
    low_stock_products = Product.objects.filter(qty__lt=5).order_by('qty')

    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_claims': total_claims,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'store/dashboard.html', context)

# Product List
def product_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        product = Product.objects.filter(
            pro_name__icontains=search_query
            ) | Product.objects.filter(
                pro_id_icontains=search_query
            )
    else:
        product = product = Product.objects.all()
    return render(request=request, template_name='store/product_list.html',
        context={'products': product,
                'search_query': search_query
        })

def add_product(request):
    if request.method == "POST":
        # ຮັບຄ່າຈາກຟອມ
        pro_id = request.POST.get('pro_id')
        pro_name = request.POST.get('pro_name')
        price_buy = float(request.POST.get('price_buy', 0))
        price_sale = float(request.POST.get('price_sale', 0))
        qty = int(request.POST.get('qty', 0))
        cat_id = request.POST.get('cat_id')
        brand_id = request.POST.get('brand_id')
        unit_id = request.POST.get('unit_id')

        # ກວດສອບວ່າລະຫັດສິນຄ້າຊ້ຳກັນຫຼືບໍ່
        if Product.objects.filter(pro_id=pro_id).exists():
            messages.error(request, 'ລະຫັດສິນຄ້ານີ້ມີໃນລະບົບແລ້ວ! ກະລຸນາໃຊ້ລະຫັດອື່ນ.')
            return redirect('add_product')

        # ດຶງຂໍ້ມູນ Object ຂອງ ໝວດໝູ່, ຍີ່ຫໍ້, ຫົວໜ່ວຍ
        cat = get_object_or_404(Category, cat_id=cat_id)
        brand = get_object_or_404(Brand, brand_id=brand_id)
        unit = get_object_or_404(Unit, unit_id=unit_id)

        # ບັນທຶກລົງຖານຂໍ້ມູນ
        Product.objects.create(
            pro_id=pro_id,
            pro_name=pro_name,
            price_buy=price_buy,
            price_sale=price_sale,
            qty=qty,
            cat=cat,
            brand=brand,
            unit=unit
        )
        messages.success(request, f'ເພີ່ມສິນຄ້າ {pro_name} ສຳເລັດແລ້ວ!')
        return redirect('product_list') # ກັບໄປໜ້າລາຍການສິນຄ້າ

    # ສຳລັບສະແດງໜ້າຟອມ ດຶງຂໍ້ມູນ Dropdown ມາສະແດງ
    categories = Category.objects.all()
    brands = Brand.objects.all()
    units = Unit.objects.all()

    return render(request, 'store/add_product.html', {
        'categories': categories,
        'brands': brands,
        'units': units
    })

# Claim List
def claim_list(request):
    # ດຶງຂໍ້ມູນການເຄມທັງໝົດ ລຽງຈາກໃໝ່ໄປເກົ່າ
    claims = Claim.objects.all().order_by('-claim_date')
    
    # ຄົ້ນຫາ (Search) ຖ້າມີການພິມຄົ້ນຫາ
    search_query = request.GET.get('search', '')
    if search_query:
        claims = claims.filter(pro__pro_name__icontains=search_query) | claims.filter(claim_id__icontains=search_query)

    context = {
        'claims': claims,
        'search_query': search_query
    }
    return render(request, 'store/claim_list.html', context)

# Add Claim (ອັບເດດໃໝ່ ໃຫ້ເຊື່ອມກັບ SaleDetail)
def add_claim(request):
    if request.method == 'POST':
        cus_id = request.POST.get('cus_id')
        pro_id = request.POST.get('pro_id')
        detail = request.POST.get('detail')
        status = request.POST.get('status')
        
        # ສ້າງລະຫັດເຄມອັດຕະໂນມັດ (ຂຶ້ນຕົ້ນດ້ວຍ C ຕາມດ້ວຍເລກ 8 ໂຕ)
        claim_id = f"C{str(int(timezone.now().timestamp()))[-8:]}"
        
        # ດຶງ Object ຂອງລູກຄ້າ ແລະ ສິນຄ້າ
        customer = get_object_or_404(Customer, cus_id=cus_id)
        product = get_object_or_404(Product, pro_id=pro_id)
        
        # ບັນທຶກລົງຖານຂໍ້ມູນ
        Claim.objects.create(
            claim_id=claim_id,
            cus=customer,
            pro=product,
            detail=detail,
            status=status
        )
        
        messages.success(request, f'ບັນທຶກການຮັບເຄມລະຫັດ {claim_id} ສຳເລັດແລ້ວ!')
        return redirect('claim_list')

    # ຖ້າເປັນ GET (ເປີດໜ້າເວັບທຳມະດາ) ໃຫ້ດຶງຂໍ້ມູນລູກຄ້າ ແລະ ສິນຄ້າມາສະແດງໃນ Dropdown
    customers = Customer.objects.all()
    products = Product.objects.all()
    
    return render(request, 'store/add_claim.html', {
        'customers': customers,
        'products': products
    })

# POS Page (ຈັດການທັງສະແດງສິນຄ້າ ແລະ ຄິດໄລ່ເງິນລວມ)
def pos(request):
    search_query = request.GET.get('search', '')
    if search_query:
        products = Product.objects.filter(pro_name__icontains=search_query, qty__gt=0)
    else:
        products = Product.objects.filter(qty__gt=0)
        
    customers = Customer.objects.all()
    cart = request.session.get('cart', {})
    
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    total_items = sum(item['quantity'] for item in cart.values())
        
    context = {
        'products': products,
        'customers': customers,
        'total_price': total_price,
        'total_items': total_items,
        'search_query': search_query,
    }
    return render(request, 'store/pos.html', context)

# Add to cart
def add_to_cart(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    cart = request.session.get('cart', {})
    
    # ດຶງຈຳນວນສິນຄ້າທີ່ຢູ່ໃນ cart ແລະ ກວດສອບວ່າ ສິນຄ້າໃນ stock ພໍແລ້ວ ຫຼື ຍັງ
    current_qty = cart.get(str(pro_id), {}).get('quantity', 0)
    
    if product.qty > current_qty:
        if str(pro_id) in cart:
            cart[str(pro_id)]['quantity'] += 1
        else:
            cart[str(pro_id)] = {
                'name': product.pro_name,
                'price': float(product.price_sale),
                'quantity': 1
            }
        request.session['cart'] = cart
    else:
        # ສິນຄ້າໃນ stock ບໍ່ພໍແລ້ວ ແລະ ສະແດງແຈ້ງເຕືອນ
        messages.error(request, f'ແຈ້ງເຕືອນ: ສິນຄ້າ {product.pro_name} ໃນສະຕັອກມີພຽງ {product.qty} ຊິ້ນ!')
        
    return redirect('pos')

# Remove from cart
def remove_from_cart(request, pro_id):
    cart = request.session.get('cart', {})
    if str(pro_id) in cart:
        del cart[str(pro_id)]
        request.session['cart'] = cart
    return redirect('pos')

# Clear cart
def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('pos')

# Checkout and save to Database
def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('pos')
        
        # ດຶງຈຳນວນເງິນທີ່ຮັບມາ ແລະ ລາຍການເງິນເພາະໃນ checkout form
        amount_paid = float(request.POST.get('amount_paid', 0))
        cus_id = request.POST.get('cus_id')
        
        total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
        
        # ກວດສອບວ່າ ຈຳນວນເງິນທີ່ຮັບມາ ພໍແລ້ວ ຫຼື ຍັງບໍ່ພໍແລ້ວ
        if amount_paid < total_amount:
            messages.error(request, 'ຈຳນວນເງິນທີ່ຮັບມາບໍ່ພຽງພໍ!')
            return redirect('pos')
            
        
        change_amount = amount_paid - total_amount
        
        # ດຶງພະນັກງານຄນໍາເຂົ້າ ແລະ ລູກຄ້າ (ຖ້າມີ) มาໃຊ້ໃນການບັນທຶກການຂາຍ
        emp = Employee.objects.first() 
        if not emp:
            emp = Employee.objects.create(emp_id="EMP001", emp_name="Admin")
            
        # ດຶງຂໍ້ມູນລູກຄ້າ ຖ້າມີ cus_id ແລະ ສ້າງ sale record ແລ້ວເກັບ sale_id ໄວ້
        customer = Customer.objects.filter(cus_id=cus_id).first() if cus_id else None
        
        sale_id = f"S{str(int(timezone.now().timestamp()))[-8:]}"
        
        # ສ້າງ sale record ແລ້ວເກັບ sale_id ໄວ້
        new_sale = Sale.objects.create(
            sale_id=sale_id,
            total_amount=total_amount,
            emp=emp,
            cus=customer,
            status='Paid'
        )
        
        # ສ້າງ sale detail records ແລະ ອັບເດດ stock ໃນ product table
        for pid, item in cart.items():
            product = Product.objects.get(pro_id=pid)
            SaleDetail.objects.create(
                sale=new_sale,
                pro=product,
                qty=item['quantity'],
                price=item['price']
            )
            # ອັບເດດ stock ໃນ product table
            product.qty -= item['quantity']
            product.save()
            
        
        request.session['cart'] = {}
        
        # ກວດສອບວ່າ ຈຳນວນເງິນທີ່ຮັບມາ ພໍແລ້ວ ຫຼື ຍັງບໍ່ພໍແລ້ວ
        request.session['payment_info'] = {
            'amount_paid': amount_paid,
            'change_amount': change_amount
        }
        
        # ສົ່ງໄປຫາ receipt page ແລະ ສະແດງ messages ໃນ receipt page ກ່ອນ redirect
        return redirect('receipt', sale_id=new_sale.sale_id)
        
    return redirect('pos')

# Receipt View
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    details = SaleDetail.objects.filter(sale=sale)
    
    #ດຶງຂໍ້ມູນການຊຳລະເງິນຈາກ session ແລະ ລົບອອກຫຼັງຈາກດຶງແລ້ວ
    payment_info = request.session.pop('payment_info', None)
    
    return render(request, 'store/receipt.html', {
        'sale': sale,
        'details': details,
        'payment_info': payment_info
    })

    
def sales_report(request):
    #ດຶງລາຍການຂາຍທັງໝົດ ຮຽງຈາກໃໝ່ໄປເກົ້າ
    sales = Sale.objects.all().order_by('-sale_date')
    
    #ຄຳນວນລາຍຮັບທັງໝົດ ແລະ ຈຳນວນໃນແຕ່ລາຍການ
    total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_bills = sales.count()
    
    context = {
        'sales': sales,
        'total_revenue': total_revenue,
        'total_bills': total_bills,
    }
    return render(request, 'store/sales_report.html', context)

def shop_settings(request):
    # ດຶງຂໍ້ມູນຮ້ານມາໃຊ້ ແລະ ຖ້າບໍ່ມີ ສ້າງ record ເອງ
    shop = ShopInfo.objects.first()
    if not shop:
        shop = ShopInfo.objects.create(shop_id="SH001", shop_name="Procom Store", tel="-", address="-")
        
    if request.method == 'POST':
        # ອັບເດດຂໍ້ມູນຮ້ານ ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ
        shop.shop_name = request.POST.get('shop_name')
        shop.tel = request.POST.get('tel')
        shop.address = request.POST.get('address')
        
        # ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ ແລະ ອັບເດດ logo ຖ້າມີ
        if 'logo' in request.FILES:
            shop.logo = request.FILES['logo'] # ອັບເດດ logo ຖ້າມີ file ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ
            
        shop.save()
        messages.success(request, 'ບັນທຶກຂໍ້ມູນຮ້ານສຳເລັດແລ້ວ!')
        return redirect('shop_settings')
        
    return render(request, 'store/shop_settings.html', {'shop': shop})

def import_stock(request):
    #ດຶງຂໍ້ມູນຜູ້ສະໜອງ ແລະ ສິນຄ້າ ເພື່ອໃຊ້ໃນ import stock form
    suppliers = Supplier.objects.all()
    products = Product.objects.all()

    if request.method == 'POST':
        sup_id = request.POST.get('sup_id')
        pro_id = request.POST.get('pro_id')
        qty = int(request.POST.get('qty', 0))
        price = float(request.POST.get('price', 0))

        if qty > 0 and price >= 0:
            supplier = get_object_or_404(Supplier, sup_id=sup_id)
            product = get_object_or_404(Product, pro_id=pro_id)
            
            # ດຶງຂໍ້ມູນພນັກງານ
            emp = Employee.objects.first()
            if not emp:
                emp = Employee.objects.create(emp_id="EMP001", emp_name="Admin")

            imp_id = f"IMP{int(timezone.now().timestamp())}"
            total_amount = qty * price

            stock_imp = StockImport.objects.create(
                imp_id=imp_id,
                total_amount=total_amount,
                sup=supplier,
                emp=emp
            )

            ImportDetail.objects.create(
                imp=stock_imp,
                pro=product,
                qty=qty,
                price=price
            )

            #
            product.qty += qty
            product.price_buy = price # ອັບເດດລາຄາຊື້ໃນ product table ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ
            product.save()

            messages.success(request, f'ນຳເຂົ້າສິນຄ້າ {product.pro_name} ຈຳນວນ {qty} ຊິ້ນ ສຳເລັດແລ້ວ!')
            return redirect('import_stock')
        else:
            messages.error(request, 'ກະລຸນາປ້ອນຈຳນວນ ແລະ ລາຄາໃຫ້ຖືກຕ້ອງ!')

    return render(request, 'store/import_stock.html', {
        'suppliers': suppliers,
        'products': products
    })
    
def update_claim_status(request, claim_id):
    # ดຶງຂໍ້ມູນເຄມທີ່ຕ້ອງການອັບເດດ
    claim = get_object_or_404(Claim, claim_id=claim_id)
    
    # ປ່ຽນສະຖານະ
    if claim.status == 'Processing':
        claim.status = 'Completed'
        messages.success(request, f'ອັບເດດສະຖານະເຄມຂອງບິນ {claim.claim_id} ເປັນ "ສຳເລັດແລ້ວ" ຮຽບຮ້ອຍ!')
    # ຖ້າສະຖານະเป็น Completed ໃຫ້ປ່ຽນເປັນ Processing
    elif claim.status == 'Completed':
        claim.status = 'Processing'
        messages.success(request, f'ປ່ຽນສະຖານະເຄມ {claim.claim_id} ກັບໄປເປັນ "ກຳລັງດຳເນີນການ"!')
        
    claim.save()
    return redirect('claim_list')

# ຟັງຊັນສຳລັບແກ້ໄຂສິນຄ້າ
def edit_product(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    
    if request.method == "POST":
        product.pro_name = request.POST.get('pro_name')
        product.price_buy = float(request.POST.get('price_buy', 0))
        product.price_sale = float(request.POST.get('price_sale', 0))
        product.qty = int(request.POST.get('qty', 0))
        
        cat_id = request.POST.get('cat_id')
        brand_id = request.POST.get('brand_id')
        unit_id = request.POST.get('unit_id')
        
        product.cat = get_object_or_404(Category, cat_id=cat_id)
        product.brand = get_object_or_404(Brand, brand_id=brand_id)
        product.unit = get_object_or_404(Unit, unit_id=unit_id)
        
        product.save()
        messages.success(request, f'ແກ້ໄຂຂໍ້ມູນສິນຄ້າ {product.pro_name} ສຳເລັດແລ້ວ!')
        return redirect('product_list')

    # ດຶງຂໍ້ມູນມາສະແດງໃນ Dropdown
    categories = Category.objects.all()
    brands = Brand.objects.all()
    units = Unit.objects.all()

    return render(request, 'store/edit_product.html', {
        'product': product,
        'categories': categories,
        'brands': brands,
        'units': units
    })

# ຟັງຊັນສຳລັບລຶບສິນຄ້າ
def delete_product(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    pro_name = product.pro_name # ເກັບຊື່ໄວ້ສະແດງແຈ້ງເຕືອນກ່ອນລຶບ
    product.delete()
    messages.success(request, f'ລຶບສິນຄ້າ {pro_name} ອອກຈາກຄັງສຳເລັດແລ້ວ!')
    return redirect('product_list')