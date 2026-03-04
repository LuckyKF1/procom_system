from django.shortcuts import render, redirect, get_object_or_404 # เช็คสะกดชื่อดีๆ นะครับ
from django.db.models import Sum
from .models import Product, Sale, Claim

#Dashboard
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

def pos(request):
    products = Product.objects.filter(qty__gt=0)
    return render(request, 'store/pos.html', {'products': products})

# add to cart
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

# clear cart
def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('pos')