from datetime import timedelta
from multiprocessing import context
import random
from urllib import request
from django.db import models
from django.db.models import Q, Sum, F, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from .forms import EmployeeForm
from .models import Product, Sale, Claim, SaleDetail, Employee, Customer, ShopInfo, Supplier, StockImport, ImportDetail, Category, Brand, Unit, Shipping, generate_sale_id

@login_required(login_url="login")
def shop_settings(request):
    shop = ShopInfo.objects.first()
    
    if request.method == "POST":
        if not shop:
            shop = ShopInfo()
            
        shop.shop_name = request.POST.get("shop_name")
        shop.address = request.POST.get("address")
        shop.tel = request.POST.get("tel")
        shop.email = request.POST.get("email")
        
        if request.FILES.get("logo"):
            shop.logo = request.FILES.get("logo")
            
        shop.save()
        messages.success(request, "ບັນທຶກຂໍ້ມູນຮ້ານສຳເລັດແລ້ວ!")
        return redirect("shop_settings")

    return render(request, "store/shop_settings.html", {"shop": shop})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")

        # 1. ລອງ Login ແບບ Standard Django ກ່ອນ (ສຳລັບ Superuser ທີ່ສ້າງຜ່ານ Docker)
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"ສະບາຍດີ Admin {user.username}!")
            return redirect("dashboard")
        
        # 2. ຖ້າບໍ່ແມ່ນ Admin, ໃຫ້ລອງກວດໃນ Table Employee (ສຳລັບພະນັກງານທຳມະດາ)
        try:
            emp = Employee.objects.get(emp_name=u)
            if emp.password == p:  # ທຽບລະຫັດ 8 ຕົວແບບ Plain Text ຕາມທີ່ Lucky ຕ້ອງການ
                # ສ້າງ Django User ໃຫ້ອັດຕະໂນມັດເພື່ອໃຫ້ລະບົບຈຳ Session ໄດ້
                from django.contrib.auth.models import User
                django_user, created = User.objects.get_or_create(username=emp.emp_name)
                
                auth_login(request, django_user)
                messages.success(request, f"ສະບາຍດີພະນັກງານ {emp.emp_name}!")
                return redirect("dashboard")
            else:
                messages.error(request, "ລະຫັດຜ່ານພະນັກງານບໍ່ຖືກຕ້ອງ!")
        except Employee.DoesNotExist:
            messages.error(request, "ບໍ່ມີຊື່ຜູ້ໃຊ້ນີ້ໃນລະບົບ!")

    shop = ShopInfo.objects.first()
    return render(request, "store/login.html", {"shop": shop})


def is_admin(user):
    return user.is_superuser


# ຟັງຊັນອອກຈາກລະບົບ (Logout)
@login_required(login_url="login")
def logout_view(request):
    logout(request)
    messages.success(request, "ທ່ານໄດ້ອອກຈາກລະບົບແລ້ວ.")
    return redirect("login")


# Dashboard
# Dashboard (ປັບປຸງໃໝ່ໃຫ້ຕົວເລກຂຶ້ນຄົບ)
@login_required(login_url="login")
def dashboard(request):
    today = timezone.now().date()

    # 1. ຍອດຂາຍມື້ນີ້
    total_sales_dict = Sale.objects.filter(sale_date__date=today).aggregate(Sum("total_amount"))
    total_sales = total_sales_dict["total_amount__sum"] or 0

    # 2. ຈຳນວນບິນມື້ນີ້
    total_orders = Sale.objects.filter(sale_date__date=today).count()

    # 3. ຈຳນວນລາຍການສິນຄ້າໃນຄັງ
    total_products = Product.objects.count()

    # 4. ສິນຄ້າລໍຖ້າເຄມ
    total_claims = Claim.objects.filter(status="ລໍຖ້າກວດສອບ").count()

    # --- ສ່ວນທີ່ເພີ່ມໃໝ່ສຳລັບກຣາຟ ---
    sales_labels = []
    sales_data = []
    for i in range(6, -1, -1):  # ດຶງຂໍ້ມູນຍ້ອນຫຼັງ 7 ວັນ
        date = today - timedelta(days=i)
        daily_total = Sale.objects.filter(sale_date__date=date).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_labels.append(date.strftime('%d/%m')) # ວັນທີ/ເດືອນ
        sales_data.append(float(daily_total))

    context = {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_claims": total_claims,
        "recent_sales": Sale.objects.all().order_by("-sale_id")[:5],
        "low_stock_products": Product.objects.filter(qty__lt=5).order_by("qty")[:5],
        "sales_labels": sales_labels,
        "sales_data": sales_data,
    }
    return render(request, "store/dashboard.html", context)


# Product List
@login_required(login_url="login")
def product_list(request):
    search_query = request.GET.get("search", "")
    # ດຶງຂໍ້ມູນສິນຄ້າທັງໝົດອອກມາກ່ອນ
    products = Product.objects.all().order_by("-pro_id")

    if search_query:
        # Filter ຫາ ຊື່, ລະຫັດ, ຊື່ໝວດໝູ່ ຫຼື ຊື່ຍີ່ຫໍ້
        products = products.filter(
            Q(pro_name__icontains=search_query)
            | Q(pro_id__icontains=search_query)
            | Q(cat__cat_name__icontains=search_query)
            | Q(brand__brand_name__icontains=search_query)
        ).distinct()

    return render(
        request,
        "store/product_list.html",
        {"products": products, "search_query": search_query},
    )

# POS Page (ຈັດການທັງສະແດງສິນຄ້າ ແລະ ຄິດໄລ່ເງິນລວມ)
@login_required(login_url="login")
def pos(request):
    search_query = request.GET.get("search", "")
    products = Product.objects.filter(qty__gt=0).order_by("pro_name")

    if search_query:
        products = products.filter(
            Q(pro_name__icontains=search_query) |
            Q(pro_id__icontains=search_query) |
            Q(cat__cat_name__icontains=search_query) |
            Q(brand__brand_name__icontains=search_query)
        ).distinct()

    customers = Customer.objects.all()
    
    # ດຶງຂໍ້ມູນ Cart ມາຄິດໄລ່ຍອດລວມເພື່ອສົ່ງໄປ Dashboard ນ້ອຍໆໃນ POS
    cart = request.session.get("cart", {})
    total_price = sum(item["price"] * item["quantity"] for item in cart.values())
    total_items = sum(item["quantity"] for item in cart.values())

    context = {
        "products": products,
        "customers": customers,
        "cart": cart,  # ສົ່ງ cart ໄປໃຫ້ {% if cart %} ໃນ HTML ເຮັດວຽກໄດ້
        "total_price": total_price,
        "total_items": total_items,
        "search_query": search_query,
    }
    return render(request, "store/pos.html", context)

# Add to cart
@login_required(login_url="login")
def add_to_cart(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    # ດຶງ Cart ຈາກ Session (ຖ້າບໍ່ມີໃຫ້ເປັນ Dictionary ວ່າງ)
    cart = request.session.get("cart", {})

    # Session key ຕ້ອງເປັນ String ສະເໝີ
    p_id = str(pro_id)
    current_qty_in_cart = cart.get(p_id, {}).get("quantity", 0)

    # ກວດສອບ Stock ກ່ອນເພີ່ມ
    if product.qty > current_qty_in_cart:
        if p_id in cart:
            cart[p_id]["quantity"] += 1
        else:
            cart[p_id] = {
                "name": product.pro_name,
                "price": float(product.price_sale),
                "quantity": 1,
            }
        
        # [ສຳຄັນທີ່ສຸດ] ຕ້ອງບອກ Django ວ່າ Session ມີການປ່ຽນແປງ
        request.session["cart"] = cart
        request.session.modified = True 
        
        messages.success(request, f"ເພີ່ມ {product.pro_name} ລົງກະຕ່າແລ້ວ!")
    else:
        messages.error(request, f"ຂໍໂທດ! ສິນຄ້າ {product.pro_name} ໃນສະຕັອກບໍ່ພໍ.")

    # ກັບໄປໜ້າ POS (ຈະ Redirect ໄປບ່ອນເກົ່າທີ່ກົດ)
    return redirect("pos")


# Remove from cart
@login_required(login_url="login")
def remove_from_cart(request, pro_id):
    cart = request.session.get("cart", {})
    p_id = str(pro_id)
    
    if p_id in cart:
        del cart[p_id]
        request.session["cart"] = cart
        request.session.modified = True
        messages.success(request, "ລຶບສິນຄ້າອອກຈາກກະຕ່າແລ້ວ.")
        
    return redirect("pos")


# Clear cart
@login_required(login_url="login")
def clear_cart(request):
    if "cart" in request.session:
        del request.session["cart"]
        request.session.modified = True
    return redirect("pos")


# Checkout and save to Database (ສະບັບປັບປຸງ: ຮອງຮັບ Quotation, VAT, Discount)
@login_required(login_url="login")
def checkout(request):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        if not cart: return redirect("pos")

        amount_paid = float(request.POST.get("amount_paid", 0))
        cus_id = request.POST.get("cus_id")
        discount = float(request.POST.get("discount", 0))
        status = request.POST.get("status", "Paid")
        
        sub_total = sum(item["price"] * item["quantity"] for item in cart.values())
        total_after_discount = sub_total - discount
        vat = total_after_discount * 0.07
        grand_total = total_after_discount + vat

        if status == "Paid" and amount_paid < grand_total:
            messages.error(request, "ຈຳນວນເງິນທີ່ຮັບມາບໍ່ພຽງພໍ!")
            return redirect("pos")

        emp, _ = Employee.objects.get_or_create(
            emp_name=request.user.username,
            defaults={"emp_id": f"EMP{random.randint(100,999)}"})

        customer = Customer.objects.filter(cus_id=cus_id).first()
        sale_id = f"S{str(int(timezone.now().timestamp()))[-8:]}"

        new_sale = Sale.objects.create(
            sale_id=sale_id, total_amount=grand_total, discount=discount,
            vat_rate=7.00, emp=emp, cus=customer, status=status
        )

        for pid, item in cart.items():
            product = Product.objects.get(pro_id=pid)
            SaleDetail.objects.create(sale=new_sale, pro=product, qty=item["quantity"], price=item["price"])
            if status == "Paid":
                product.qty -= item["quantity"]
                product.save()

        request.session["cart"] = {}
        return redirect("receipt", sale_id=new_sale.sale_id)
    return redirect("pos")

@login_required(login_url="login")
def edit_claim(request, claim_id):
    claim = get_object_or_404(Claim, claim_id=claim_id)

    if request.method == "POST":
        claim.symptom = request.POST.get("symptom")
        claim.status = request.POST.get("status")
        claim.save()
        messages.success(request, f"ແກ້ໄຂຂໍ້ມູນການເຄມ {claim.claim_id} ສຳເລັດແລ້ວ!")
        return redirect("claim_list")

    return render(request, "store/edit_claim.html", {"claim": claim})


# ຟັງຊັນສຳລັບແກ້ໄຂສິນຄ້າ
@login_required(login_url="login")
def edit_product(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)

    if request.method == "POST":
        product.pro_name = request.POST.get("pro_name")
        product.price_buy = float(request.POST.get("price_buy", 0))
        product.price_sale = float(request.POST.get("price_sale", 0))
        product.qty = int(request.POST.get("qty", 0))

        cat_id = request.POST.get("cat_id")
        brand_id = request.POST.get("brand_id")
        unit_id = request.POST.get("unit_id")

        product.cat = get_object_or_404(Category, cat_id=cat_id)
        product.brand = get_object_or_404(Brand, brand_id=brand_id)
        product.unit = get_object_or_404(Unit, unit_id=unit_id)

        product.save()
        messages.success(request, f"ແກ້ໄຂຂໍ້ມູນສິນຄ້າ {product.pro_name} ສຳເລັດແລ້ວ!")
        return redirect("product_list")

    # ດຶງຂໍ້ມູນມາສະແດງໃນ Dropdown
    categories = Category.objects.all()
    brands = Brand.objects.all()
    units = Unit.objects.all()

    return render(
        request,
        "store/edit_product.html",
        {
            "product": product,
            "categories": categories,
            "brands": brands,
            "units": units,
        },
    )


# ຟັງຊັນສຳລັບລຶບສິນຄ້າ
@login_required(login_url="login")
def delete_product(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    pro_name = product.pro_name  # ເກັບຊື່ໄວ້ສະແດງແຈ້ງເຕືອນກ່ອນລຶບ
    product.delete()
    messages.success(request, f"ລຶບສິນຄ້າ {pro_name} ອອກຈາກຄັງສຳເລັດແລ້ວ!")
    return redirect("product_list")

@login_required(login_url="login")
def add_product(request):
    if request.method == "POST":
        # ຮັບຄ່າຈາກຟອມ
        pro_id = request.POST.get("pro_id")
        pro_name = request.POST.get("pro_name")
        price_buy = float(request.POST.get("price_buy", 0))
        price_sale = float(request.POST.get("price_sale", 0))
        qty = int(request.POST.get("qty", 0))

        cat_id = request.POST.get("cat")
        brand_id = request.POST.get("brand")
        unit_id = request.POST.get("unit")

        pro_img = request.FILES.get("pro_img")

        # ກວດສອບວ່າລະຫັດສິນຄ້າຊ້ຳກັນຫຼືບໍ່
        if Product.objects.filter(pro_id=pro_id).exists():
            messages.error(request, "ລະຫັດສິນຄ້ານີ້ມີໃນລະບົບແລ້ວ! ກະລຸນາໃຊ້ລະຫັດອື່ນ.")
            return redirect("add_product")

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
            unit=unit,
            pro_img=pro_img,
        )
        messages.success(request, f"ເພີ່ມສິນຄ້າ {pro_name} ສຳເລັດແລ້ວ!")
        return redirect("product_list")

    # ສຳລັບສະແດງໜ້າຟອມ ດຶງຂໍ້ມູນ Dropdown ມາສະແດງ
    categories = Category.objects.all()
    brands = Brand.objects.all()
    units = Unit.objects.all()

    return render(
        request,
        "store/add_product.html",
        {"categories": categories, "brands": brands, "units": units},
    )


# Add Claim (ອັບເດດໃໝ່ ໃຫ້ເຊື່ອມກັບ SaleDetail)
@login_required(login_url="login")
def add_claim(request):
    if request.method == "POST":
        sale_detail_id = request.POST.get("sale_detail_id")
        symptom = request.POST.get("symptom")
        status = request.POST.get("status", "ລໍຖ້າກວດສອບ") # ຕັ້ງຄ່າ Default ໄວ້ເລີຍ

        # 1. ດຶງຂໍ້ມູນ SaleDetail ມາເຊັກກ່ອນ
        sale_detail = get_object_or_404(SaleDetail, pk=sale_detail_id)

        # 2. [Logic ເພີ່ມໃໝ່] ກວດສອບປະກັນສິນຄ້າ
        today = timezone.now().date()
        if sale_detail.warranty_end and sale_detail.warranty_end < today:
            messages.error(request, f"ບໍ່ສາມາດເຄມໄດ້! ສິນຄ້ານີ້ໝົດປະກັນແລ້ວເມື່ອວັນທີ {sale_detail.warranty_end.strftime('%d/%m/%Y')}")
            return redirect("add_claim")

        # 3. ດຶງຂໍ້ມູນພະນັກງານທີ່ Login ຢູ່ (ຄືກັບທີ່ Lucky ເຮັດໃນ checkout)
        emp = Employee.objects.filter(emp_name=request.user.username).first()
        
        if not emp:
            # ຖ້າບໍ່ມີໃນ Employee Model ໃຫ້ດຶງ Admin ຄົນທຳອິດມາແທນເພື່ອປ້ອງກັນ Error
            emp = Employee.objects.first()

        # 4. ສ້າງລະຫັດເຄມ
        claim_id = f"CLM{int(timezone.now().timestamp())}"

        try:
            Claim.objects.create(
                claim_id=claim_id,
                sale_detail=sale_detail,
                emp=emp,
                symptom=symptom,
                status=status,
            )
            messages.success(request, f"ບັນທຶກການເຄມ {claim_id} ສຳເລັດແລ້ວ! (ຍັງເຫຼືອປະກັນຮອດ: {sale_detail.warranty_end})")
            return redirect("claim_list")

        except Exception as e:
            messages.error(request, f"ເກີດຂໍ້ຜິດພາດ: {str(e)}")
            return redirect("add_claim")

    # --- ສ່ວນສະແດງໜ້າຟອມ (GET Request) ---
    # ດຶງສະເພາະລາຍການທີ່ "ຍັງບໍ່ໝົດປະກັນ" ມາໃຫ້ເລືອກ (ເພື່ອຄວາມສະດວກຂອງ User)
    from .models import SaleDetail
    today = timezone.now().date()
    
    # ດຶງສິນຄ້າທີ່ຂາຍແລ້ວ ແລະ ວັນທີໝົດປະກັນ ຍັງຫຼາຍກວ່າ ຫຼື ເທົ່າກັບ ມື້ນີ້
    sale_details = SaleDetail.objects.filter(
        Q(warranty_end__gte=today) | Q(warranty_end__isnull=True)
    ).order_by("-sale__sale_date")

    return render(request, "store/add_claim.html", {"sale_details": sale_details})

@login_required(login_url="login")
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    details = SaleDetail.objects.filter(sale=sale)
    
    # ຕັ້ງຄ່າອັດຕາແລກປ່ຽນ (ອັນນີ້ Lucky ອາດຈະດຶງຈາກ Database ກໍໄດ້ໃນອະນາຄົດ)
    ex_thb = 750    # 1 THB = 750 LAK
    ex_usd = 21500  # 1 USD = 21,500 LAK
    
    for item in details:
        # ໄລ່ຍອດລວມກີບຂອງແຕ່ລະ Line
        item.total_line_lak = item.qty * item.price
        
        # ແປງລາຄາຕໍ່ໜ່ວຍ ແລະ ຍອດລວມເປັນ THB ເພື່ອໄປໂຊໃນ Template
        item.price_thb = item.price / ex_thb
        item.total_line_thb = item.qty * item.price_thb

    # ຄິດໄລ່ຍອດລວມທັງໝົດຂອງບິນ
    total_lak = sale.total_amount
    total_thb = total_lak / ex_thb
    total_usd = total_lak / ex_usd # ເພີ່ມການແປງເປັນ USD
    
    # ຄິດໄລ່ VAT (ຖ້າມີ)
    vat_amount = 0
    if sale.vat_rate > 0:
        # ສູດຫາ VAT ຈາກຍອດລວມ (ຖ້າຍອດນັ້ນລວມ vat ແລ້ວ ໃຫ້ໃຊ້ສູດອື່ນ)
        vat_amount = (total_lak * float(sale.vat_rate)) / 100

    context = {
        "sale": sale,
        "details": details,
        "total_thb": total_thb,
        "total_usd": total_usd, # ສົ່ງຄ່າ USD ໄປ Template
        "vat_amount": vat_amount,
        "exchange_rate_thb": ex_thb,
        "exchange_rate_usd": ex_usd,
        "shop": ShopInfo.objects.first(),
    }
    
    # ເລືອກ Template ຕາມ Status (ປັບໃຫ້ Support ທັງພາສາລາວ ແລະ ອັງກິດ)
    status = str(sale.status).strip()
    if status in ['Quotation', 'ໃບສະເໜີລາຄາ']:
        template_name = "store/quotation.html"
    else:
        template_name = "store/invoice.html"

    return render(request, template_name, context)


@login_required(login_url="login")
def import_stock(request):
    suppliers = Supplier.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        sup_id = request.POST.get("sup_id")
        pro_id = request.POST.get("pro_id")
        # ດຶງຄ່າໃຫ້ກົງກັບ name="qty" ແລະ name="price" ໃນ HTML
        qty = int(request.POST.get("qty", 0))
        price = float(request.POST.get("price", 0))

        if qty > 0 and sup_id and pro_id:
            supplier = get_object_or_404(Supplier, sup_id=sup_id)
            product = get_object_or_404(Product, pro_id=pro_id)

            # ດຶງຂໍ້ມູນພະນັກງານທີ່ Login ຢູ່ (ຖ້າບໍ່ມີໃຫ້ໃຊ້ຄົນທຳອິດ)
            emp = Employee.objects.filter(emp_name=request.user.username).first()
            if not emp:
                emp = Employee.objects.first()

            # ສ້າງ Record ການນຳເຂົ້າ
            ts_short = str(int(timezone.now().timestamp()))[-6:]
            imp_id = f"IMP{ts_short}"
            stock_imp = StockImport.objects.create(
                imp_id=imp_id,
                total_amount=qty * price,
                sup=supplier,
                emp=emp
            )

            # ບັນທຶກລາຍລະອຽດ
            ImportDetail.objects.create(
                imp=stock_imp, pro=product, qty=qty, price=price
            )

            # ອັບເດດ Stock ແລະ ລາຄາຕົ້ນທຶນ
            product.qty += qty
            product.price_buy = price
            product.save()

            messages.success(request, f"ນຳເຂົ້າ {product.pro_name} +{qty} ສຳເລັດ!")
            return redirect("import_stock")
        else:
            messages.error(request, "ກະລຸນາເລືອກຂໍ້ມູນ ແລະ ປ້ອນຈຳນວນໃຫ້ຄົບຖ້ວນ!")

    return render(request, "store/import_stock.html", {
        "suppliers": suppliers, 
        "products": products
    })

# Claim List
@login_required(login_url="login")
def claim_list(request):
    today = timezone.now().date()
    last_week = today - timezone.timedelta(days=7)

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    claims = Claim.objects.all().order_by("-claim_date")

    if not (search_query or status_filter):
        claims = claims.filter(
            Q(claim_date__date__gte=last_week) |
            Q(status__in=["Processing", "Repairing", "ລໍຖ້າກວດສອບ", "ກຳລັງສ້ອມແປງ"])
        )

    if search_query:
        claims = claims.filter(
            Q(claim_id__icontains=search_query) |
            Q(sale_detail__pro__pro_name__icontains=search_query)
        ).distinct()

    if status_filter:
        claims = claims.filter(status=status_filter)

    return render(request, "store/claim_list.html", {
        "claims": claims,
        "search_query": search_query,
        "status_filter": status_filter,
    })
    
@login_required(login_url="login")
@user_passes_test(is_admin, login_url="dashboard")
def employee_list(request):
    search_query = request.GET.get("search", "")
    employees = Employee.objects.all().order_by("emp_id")
    
    if search_query:
        employees = employees.filter(
            Q(emp_name__icontains=search_query) |
            Q(emp_id__icontains=search_query)
        )
    
    return render(request, "store/employee_list.html", {
        "employees": employees,
        "search_query": search_query
    })

@login_required(login_url="login")
@user_passes_test(is_admin, login_url="dashboard")
def add_employee(request):
    if request.method == "POST":
        emp_id = request.POST.get("emp_id")
        emp_name = request.POST.get("emp_name")
        surname = request.POST.get("surname")
        tel = request.POST.get("tel")
        position = request.POST.get("position")
        password = request.POST.get("password") # ໃນລະບົບຈິງຄວນ Hash Password ກ່ອນ

        if Employee.objects.filter(emp_id=emp_id).exists():
            messages.error(request, "ລະຫັດພະນັກງານນີ້ມີໃນລະບົບແລ້ວ!")
            return redirect("add_employee")

        Employee.objects.create(
            emp_id=emp_id,
            emp_name=emp_name,
            surname=surname,
            tel=tel,
            position=position,
            password=password
        )
        messages.success(request, f"ເພີ່ມພະນັກງານ {emp_name} ສຳເລັດ!")
        return redirect("employee_list")

    return render(request, "store/add_employee.html")

@login_required(login_url="login")
@user_passes_test(is_admin, login_url="dashboard")
def delete_employee(request, emp_id):
    emp = get_object_or_404(Employee, emp_id=emp_id)
    emp.delete()
    messages.success(request, "ລຶບຂໍ້ມູນພະນັກງານສຳເລັດ!")
    return redirect("employee_list")

@login_required(login_url="login")
def category_list(request):
    categories = Category.objects.all()
    if request.method == "POST":
        cat_id = request.POST.get("cat_id")
        cat_name = request.POST.get("cat_name")
        Category.objects.create(cat_id=cat_id, cat_name=cat_name)
        messages.success(request, "ເພີ່ມໝວດໝູ່ສຳເລັດ!")
        return redirect("category_list")
    return render(request, "store/category_list.html", {"categories": categories})

@login_required(login_url="login")
def brand_list(request):
    brands = Brand.objects.all()
    if request.method == "POST":
        brand_id = request.POST.get("brand_id")
        brand_name = request.POST.get("brand_name")
        Brand.objects.create(brand_id=brand_id, brand_name=brand_name)
        messages.success(request, "ເພີ່ມຍີ່ຫໍ້ສຳເລັດ!")
        return redirect("brand_list")
    return render(request, "store/brand_list.html", {"brands": brands})

@login_required(login_url="login")
def unit_list(request):
    units = Unit.objects.all()
    if request.method == "POST":
        unit_id = request.POST.get("unit_id")
        unit_name = request.POST.get("unit_name")
        Unit.objects.create(unit_id=unit_id, unit_name=unit_name)
        messages.success(request, "ເພີ່ມຫົວໜ່ວຍສຳເລັດ!")
        return redirect("unit_list")
    return render(request, "store/unit_list.html", {"units": units})

def delete_category(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    return redirect('category_list')

def delete_brand(request, pk):
    get_object_or_404(Brand, pk=pk).delete()
    return redirect('brand_list')

def delete_unit(request, pk):
    get_object_or_404(Unit, pk=pk).delete()
    return redirect('unit_list')

# ແກ້ໄຂຜູ້ສະໜອງ
def edit_supplier(request, pk):
    instance = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        instance.company_name = request.POST.get("sup_name")
        instance.tel = request.POST.get("tel")
        instance.address = request.POST.get("address")
        instance.save()
        messages.success(request, "ແກ້ໄຂຜູ້ສະໜອງສຳເລັດ!")
    return redirect('supplier_list')

# --- Edit Category ---
def edit_category(request, pk):
    instance = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        instance.cat_name = request.POST.get("cat_name")
        instance.save()
        messages.success(request, "ແກ້ໄຂໝວດໝູ່ສຳເລັດ!")
    return redirect('category_list')

# --- Edit Brand ---
def edit_brand(request, pk):
    instance = get_object_or_404(Brand, pk=pk)
    if request.method == "POST":
        instance.brand_name = request.POST.get("brand_name")
        instance.save()
        messages.success(request, "ແກ້ໄຂຍີ່ຫໍ້ສຳເລັດ!")
    return redirect('brand_list')

# --- Edit Unit ---
def edit_unit(request, pk):
    instance = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        instance.unit_name = request.POST.get("unit_name")
        instance.save()
        messages.success(request, "ແກ້ໄຂຫົວໜ່ວຍສຳເລັດ!")
    return redirect('unit_list')

def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            emp_data = form.save(commit=False)
            
            emp_data.password = form.cleaned_data.get('password')
            emp_data.save()
            
            messages.success(request, f'ແກ້ໄຂຂໍ້ມູນ {employee.emp_name} ສຳເລັດແລ້ວ!')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'store/edit_employee.html', {
        'form': form,
        'employee': employee
    })

@login_required(login_url="login")
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('sup_id')
    if request.method == "POST":
        sup_id = request.POST.get("sup_id")
        sup_name = request.POST.get("sup_name")
        tel = request.POST.get("tel")
        address = request.POST.get("address")
        
        Supplier.objects.create(
            sup_id=sup_id,
            company_name=sup_name,
            tel=tel,
            address=address
        )
        messages.success(request, "ເພີ່ມຂໍ້ມູນຜູ້ສະໜອງສຳເລັດ!")
        return redirect("supplier_list")
    return render(request, "store/supplier_list.html", {"suppliers": suppliers})

def delete_supplier(request, pk):
    get_object_or_404(Supplier, pk=pk).delete()
    return redirect('supplier_list')

@login_required(login_url="login")
def customer_list(request):
    customers = Customer.objects.all().order_by('-cus_id')
    
    if request.method == "POST":
        cus_name = request.POST.get("cus_name")
        tel = request.POST.get("tel")
        address = request.POST.get("address")
        
        # ສ້າງ ID ແບບອັດຕະໂນມັດ (CUS001, CUS002, ...)
        last_cus = Customer.objects.all().order_by('cus_id').last()
        if not last_cus:
            new_id = "CUS001"
        else:
            # ດຶງຕົວເລກມາບວກ 1
            cus_int = int(last_cus.cus_id[3:]) + 1
            new_id = f"CUS{cus_int:03d}"
            
        Customer.objects.create(
            cus_id=new_id,
            cus_name=cus_name,
            tel=tel,
            address=address
        )
        messages.success(request, f"ເພີ່ມລູກຄ້າ {cus_name} ສຳເລັດແລ້ວ!")
        return redirect("customer_list")

    return render(request, "store/customer.html", {"customers": customers})

@login_required(login_url="login")
def edit_customer(request, cus_id):
    customer = get_object_or_404(Customer, cus_id=cus_id)
    if request.method == "POST":
        customer.cus_name = request.POST.get("cus_name")
        customer.tel = request.POST.get("tel")
        customer.address = request.POST.get("address")
        customer.save()
        messages.success(request, "ແກ້ໄຂຂໍ້ມູນລູກຄ້າສຳເລັດ!")
    return redirect("customer_list")

# ແຖມຟັງຊັນ Delete ໃຫ້ພ້ອມເພື່ອບໍ່ໃຫ້ Error ຮອບໜ້າ
@login_required(login_url="login")
def delete_customer(request, cus_id):
    customer = get_object_or_404(Customer, cus_id=cus_id)
    customer.delete()
    messages.warning(request, "ລຶບຂໍ້ມູນລູກຄ້າຮຽບຮ້ອຍແລ້ວ.")
    return redirect("customer_list")


@login_required(login_url="login")
@user_passes_test(is_admin, login_url="dashboard")
def all_reports(request):
    today = timezone.now().date()
    
    # 1. ຮັບຄ່າ Filter ຈາກ Request
    report_type = request.GET.get('type', 'sales')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_month = request.GET.get('month')
    search_query = request.GET.get("search", "")

    # 2. ສ້າງລາຍຊື່ເດືອນຍ້ອນຫຼັງ 6 ເດືອນ (ສຳລັບ Dropdown ທາງລັດ)
    month_options = []
    for i in range(6):
        # ໃຊ້ timedelta ຖອຍຫຼັງເທື່ອລະ 30 ວັນເພື່ອຫາເດືອນກ່ອນໆ
        d = (today.replace(day=1) - timezone.timedelta(days=i*28)).replace(day=1)
        month_options.append({'val': d.strftime('%Y-%m'), 'lab': d.strftime('%m/%Y')})

    # 3. ກຽມ Context ເບື້ອງຕົ້ນ
    context = {
        'report_type': report_type,
        'month_options': month_options,
        'selected_month': selected_month,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
    }

    # --- 5.2 ລາຍງານການຂາຍ (Sales) ---
    if report_type == 'sales':
        sales = Sale.objects.all()
        latest_sales = Sale.objects.all().order_by('-sale_date')[:10]
        
        # Logic ການກັ່ນຕອງ: ເລືອກເດືອນ > ກອກວັນທີ > ເດືອນປັດຈຸບັນ
        if selected_month:
            year, month = map(int, selected_month.split('-'))
            sales = sales.filter(sale_date__year=year, sale_date__month=month)
        elif start_date and end_date:
            sales = sales.filter(sale_date__date__range=[start_date, end_date])
        elif not search_query:
            # ຖ້າບໍ່ໄດ້ Search ແລະ ບໍ່ໄດ້ Filter ໃຫ້ໂຊເດືອນປັດຈຸບັນ
            sales = sales.filter(sale_date__year=today.year, sale_date__month=today.month)
        
        if search_query:
            sales = sales.filter(Q(sale_id__icontains=search_query) | Q(cus__cus_name__icontains=search_query))
            
        context['sales'] = sales
        context['total_revenue'] = sales.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        context['total_bills'] = sales.count()

    # --- 5.1 ລາຍງານຂໍ້ມູນພື້ນຖານ ---
    elif report_type == 'basic':
        context['products'] = Product.objects.all()
        context['suppliers'] = Supplier.objects.all()
        context['customers'] = Customer.objects.all()

    # --- 5.4 & 5.5 ລາຍງານຄັງສິນຄ້າ ---
    elif report_type == 'inventory':
        context['inventory'] = Product.objects.all().order_by('qty')
        context['low_stock_count'] = Product.objects.filter(qty__lt=5).count()

# --- 5.8 ລາຍງານການເຄມ (Claims) ---
    elif report_type == 'claims':
        claims = Claim.objects.all().order_by("-claim_date")
        
        if selected_month:
            year, month = map(int, selected_month.split('-'))
            claims = claims.filter(claim_date__year=year, claim_date__month=month)
        elif start_date and end_date:
            claims = claims.filter(claim_date__date__range=[start_date, end_date])
        
        context['claims'] = claims
    return render(request, "store/all_reports.html", context)

def create_sale(request):
    if request.method == 'POST':
        status_selected = request.POST.get('status') # ຮັບຄ່າຈາກ Form
        
        # ຖ້າເປັນໃບສະເໜີລາຄາ ໃຫ້ປ່ຽນ Prefix ເປັນ QT
        new_id = generate_sale_id()
        if status_selected == 'Quotation':
            new_id = new_id.replace('INV-', 'QT-')
        
        new_sale = Sale(
            sale_id = new_id,
            status = status_selected,
            # ... ຂໍ້ມູນອື່ນໆ ...
        )
        new_sale.save()
        
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, sale_id=pk)
    details = SaleDetail.objects.filter(sale=sale)
    
    # ເພີ່ມ Logic ອັດຕາແລກປ່ຽນ (ເພື່ອໃຫ້ໜ້າ Detail ເບິ່ງຄືໜ້າ Invoice)
    ex_thb = 750
    ex_usd = 21500
    
    context = {
        'sale': sale,
        'details': details,
        'total_thb': sale.total_amount / ex_thb,
        'total_usd': sale.total_amount / ex_usd,
        'shop': ShopInfo.objects.first(),
    }
    return render(request, 'store/sale_detail.html', context)

def update_sale_status(request, sale_id, new_status):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    
    if new_status == 'Paid':
        sale.status = 'Paid'
        sale.save()
        messages.success(request, f"ບິນ {sale_id} ຊຳລະເງິນສຳເລັດແລ້ວ!")
        
    elif new_status == 'Cancelled':
        # Logic: ຄືນສິນຄ້າເຂົ້າ Stock ເມື່ອຍົກເລີກການຂາຍ
        sale_items = SaleDetail.objects.filter(sale=sale)
        for item in sale_items:
            product = item.pro
            product.qty += item.qty  # ບວກຈຳນວນຄືນເຂົ້າສາງ
            product.save()
        
        # ປ່ຽນສະຖານະ ຫຼື ລຶບ (ໃນທີ່ນີ້ແນະນຳໃຫ້ປ່ຽນສະຖານະເພື່ອເກັບປະຫວັດ)
        sale.status = 'Unpaid' # ຫຼື ຖ້າ Lucky ມີ choice 'Cancelled' ກໍໃຊ້ໂຕນັ້ນ
        sale.save()
        messages.warning(request, f"ຍົກເລີກບິນ {sale_id} ແລະ ຄືນສິນຄ້າເຂົ້າສາງແລ້ວ.")

    # ກັບໄປໜ້າລາຍງານ ຫຼື ໜ້າທີ່ສົ່ງມາ
    return redirect('all_reports')

def add_shipping(request, sale_id):
    if request.method == "POST":
        sale_obj = get_object_or_404(Sale, sale_id=sale_id)
        
        Shipping.objects.update_or_create(
            sale=sale_obj,
            defaults={
                'tracking_no': request.POST.get('tracking_no'),
                'status': 'Shipped'
            }
        )
        
        return redirect('sale_detail', pk=sale_id)