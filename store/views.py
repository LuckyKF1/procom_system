import random
from urllib import request
from django.db import models
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from .models import Product, Sale, Claim, SaleDetail, Employee, Customer, ShopInfo, Supplier, StockImport, ImportDetail, Category, Brand, Unit


# ຟັງຊັນເຂົ້າສູ່ລະບົບ (Login)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        user = authenticate(request, username=u, password=p)

        if user is not None:
            # ກວດສອບວ່າເປັນພະນັກງານ (Staff Status) ຫຼື Admin ຫຼືບໍ່
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"ສະບາຍດີ {user.username}!")
                return redirect("dashboard")
            else:
                messages.error(request, "ຂໍອະໄພ, ບັນຊີຂອງທ່ານບໍ່ມີສິດເຂົ້າເຖິງລະບົບນີ້.")
        else:
            messages.error(request, "ຊື່ຜູ້ໃຊ້ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ!")

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
    total_sales_dict = Sale.objects.filter(sale_date__date=today).aggregate(
        Sum("total_amount")
    )
    total_sales = total_sales_dict["total_amount__sum"] or 0

    # 2. ຈຳນວນບິນມື້ນີ້ (ໃຊ້ໃຫ້ກົງກັບ HTML: total_orders)
    total_orders = Sale.objects.filter(sale_date__date=today).count()

    # 3. ຈຳນວນລາຍການສິນຄ້າໃນຄັງ (ໃຊ້ໃຫ້ກົງກັບ HTML: total_products)
    # ຖ້າຢາກໄດ້ຈຳນວນ "ລາຍການ" ໃຫ້ໃຊ້ .count() ຈະເບິ່ງສົມຈິງກວ່າ
    total_products = Product.objects.count()

    # 4. ສິນຄ້າລໍຖ້າເຄມ (ໃຊ້ໃຫ້ກົງກັບ HTML: total_claims)
    # ກວດສອບວ່າໃນ Database ໃຊ້ຄຳວ່າ 'ລໍຖ້າກວດສອບ' ແທ້ຫຼືບໍ່
    total_claims = Claim.objects.filter(status="ລໍຖ້າກວດສອບ").count()

    context = {
        "total_sales": total_sales,
        "total_orders": total_orders,  # ສົ່ງໄປຫາ {{ total_orders }}
        "total_products": total_products,  # ສົ່ງໄປຫາ {{ total_products }}
        "total_claims": total_claims,  # ສົ່ງໄປຫາ {{ total_claims }}
        "recent_sales": Sale.objects.all().order_by("-sale_date")[:5],
        "low_stock_products": Product.objects.filter(qty__lt=5).order_by("qty"),
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
    # ເລືອກສະເພາະສິນຄ້າທີ່ມີໃນສະຕັອກ (qty > 0)
    products = Product.objects.filter(qty__gt=0).order_by("pro_name")

    if search_query:
        products = products.filter(
            Q(pro_name__icontains=search_query)
            | Q(pro_id__icontains=search_query)
            | Q(cat__cat_name__icontains=search_query)
            | Q(brand__brand_name__icontains=search_query)
        ).distinct()

    customers = Customer.objects.all()
    cart = request.session.get("cart", {})

    total_price = sum(item["price"] * item["quantity"] for item in cart.values())
    total_items = sum(item["quantity"] for item in cart.values())

    context = {
        "products": products,
        "customers": customers,
        "total_price": total_price,
        "total_items": total_items,
        "search_query": search_query,
    }
    return render(request, "store/pos.html", context)


# Add to cart
@login_required(login_url="login")
def add_to_cart(request, pro_id):
    product = get_object_or_404(Product, pro_id=pro_id)
    cart = request.session.get("cart", {})

    # ດຶງຈຳນວນສິນຄ້າທີ່ຢູ່ໃນ cart ແລະ ກວດສອບວ່າ ສິນຄ້າໃນ stock ພໍແລ້ວ ຫຼື ຍັງ
    current_qty = cart.get(str(pro_id), {}).get("quantity", 0)

    if product.qty > current_qty:
        if str(pro_id) in cart:
            cart[str(pro_id)]["quantity"] += 1
        else:
            cart[str(pro_id)] = {
                "name": product.pro_name,
                "price": float(product.price_sale),
                "quantity": 1,
            }
        request.session["cart"] = cart
    else:
        # ສິນຄ້າໃນ stock ບໍ່ພໍແລ້ວ ແລະ ສະແດງແຈ້ງເຕືອນ
        messages.error(
            request, f"ແຈ້ງເຕືອນ: ສິນຄ້າ {product.pro_name} ໃນສະຕັອກມີພຽງ {product.qty} ຊິ້ນ!"
        )

    return redirect("pos")


# Remove from cart
@login_required(login_url="login")
def remove_from_cart(request, pro_id):
    cart = request.session.get("cart", {})
    if str(pro_id) in cart:
        del cart[str(pro_id)]
        request.session["cart"] = cart
    return redirect("pos")


# Clear cart
@login_required(login_url="login")
def clear_cart(request):
    if "cart" in request.session:
        del request.session["cart"]
    return redirect("pos")


# Checkout and save to Database (ສະບັບປັບປຸງ: ຮອງຮັບ Quotation, VAT, Discount)
@login_required(login_url="login")
def checkout(request):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        if not cart:
            return redirect("pos")

        # 1. ຮັບຄ່າຈາກຟອມ (ເພີ່ມ Discount ແລະ Status)
        amount_paid = float(request.POST.get("amount_paid", 0))
        cus_id = request.POST.get("cus_id")
        discount = float(request.POST.get("discount", 0)) # ສ່ວນຫຼຸດ
        status = request.POST.get("status", "Paid") # ຮັບຄ່າວ່າຈະເປັນ 'Quotation' ຫຼື 'Paid'
        
        # 2. ຄິດໄລ່ເງິນຕາມແບບຟອມທີ່ທ່ານ Lucky ສົ່ງມາ
        sub_total = sum(item["price"] * item["quantity"] for item in cart.values())
        total_after_discount = sub_total - discount
        vat = total_after_discount * 0.07  # VAT 7%
        grand_total = total_after_discount + vat

        # 3. ກວດສອບເງິນທີ່ຮັບມາ (ສະເພາະກໍລະນີຂາຍສົດ 'Paid')
        if status == "Paid" and amount_paid < grand_total:
            messages.error(request, "ຈຳນວນເງິນທີ່ຮັບມາບໍ່ພຽງພໍ!")
            return redirect("pos")

        # 4. ດຶງຂໍ້ມູນພະນັກງານທີ່ Login ຢູ່
        emp, created = Employee.objects.get_or_create(
            emp_name=request.user.username,
            defaults={"emp_id": f"EMP{random.randint(100,999)}"})

        customer = Customer.objects.filter(cus_id=cus_id).first() if cus_id else None
        sale_id = f"S{str(int(timezone.now().timestamp()))[-8:]}"

        # 5. ສ້າງ Record ໃນ Sale (ເພີ່ມ VAT ແລະ Discount)
        new_sale = Sale.objects.create(
            sale_id=sale_id,
            total_amount=grand_total, # ຍອດລວມສຸດທິ
            discount=discount,        # ເກັບສ່ວນຫຼຸດໄວ້
            vat=vat,                  # ເກັບຄ່າ VAT ໄວ້
            emp=emp,
            cus=customer,
            status=status
        )

        # 6. ສ້າງ SaleDetail ແລະ ຈັດການ Stock
        for pid, item in cart.items():
            product = Product.objects.get(pro_id=pid)
            SaleDetail.objects.create(
                sale=new_sale,
                pro=product,
                qty=item["quantity"],
                price=item["price"]
            )
            
            # [ສຳຄັນ] ຖ້າເປັນ Quotation ຈະ "ບໍ່ຕັດສະຕັອກ"
            if status == "Paid":
                product.qty -= item["quantity"]
                product.save()

        # 7. ເຄຼຍ Cart ແລະ ສົ່ງໄປໜ້າໃບບິນ
        request.session["cart"] = {}
        request.session["payment_info"] = {
            "amount_paid": amount_paid,
            "change_amount": amount_paid - grand_total if status == "Paid" else 0
        }

        return redirect("receipt", sale_id=new_sale.sale_id)

    return redirect("pos")


@login_required(login_url="login")
@user_passes_test(is_admin, login_url="dashboard")
def sales_report(request):
    today = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status')
    search_query = request.GET.get("search", "")

    sales = Sale.objects.all().order_by("-sale_date")

    if start_date and end_date:
        sales = sales.filter(sale_date__date__range=[start_date, end_date])
    elif not search_query:
        sales = sales.filter(sale_date__year=today.year, sale_date__month=today.month)
    if status_filter:
        sales = sales.filter(status=status_filter)
    
    if search_query:
        sales = sales.filter(
            Q(sale_id__icontains=search_query) | 
            Q(cus__cus_name__icontains=search_query)
        ).distinct()

    total_revenue = sales.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
    total_bills = sales.count()

    return render(request, "store/sales_report.html", {
        "sales": sales,
        "total_revenue": total_revenue,
        "total_bills": total_bills,
        "start_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
        "search_query": search_query
    })

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
        # ຮັບຄ່າຈາກຟອມ
        sale_detail_id = request.POST.get("sale_detail_id")
        symptom = request.POST.get("symptom")
        status = request.POST.get("status")

        # ສ້າງລະຫັດເຄມແບບສຸ່ມ ເຊັ່ນ CLM1024
        claim_id = f"CLM{int(timezone.now().timestamp())}"

        try:
            # ດຶງຂໍ້ມູນການຂາຍທີ່ລູກຄ້າເອົາມາເຄມ
            from .models import (
                SaleDetail,
                Employee,
                Claim,
            )  # Import model ຖ້າຍັງບໍ່ໄດ້ import

            sale_detail = get_object_or_404(SaleDetail, pk=sale_detail_id)

            # ສົມມຸດວ່າດຶງພະນັກງານຄົນທຳອິດມາເປັນຜູ້ຮັບເຄມ (ສຳລັບ Mock Data)
            emp = Employee.objects.first()

            if not emp:
                messages.error(request, "ກະລຸນາເພີ່ມຂໍ້ມູນພະນັກງານ (Employee) ໃນ Admin ກ່ອນ!")
                return redirect("add_claim")

            # ບັນທຶກລົງຖານຂໍ້ມູນຂອງທ່ານ
            Claim.objects.create(
                claim_id=claim_id,
                sale_detail=sale_detail,
                emp=emp,
                symptom=symptom,
                status=status,
            )
            messages.success(request, "ບັນທຶກລາຍການເຄມສຳເລັດແລ້ວ!")
            return redirect("claim_list")

        except Exception as e:
            messages.error(request, f"ເກີດຂໍ້ຜິດພາດ: {str(e)}")
            return redirect("add_claim")

    # ສຳລັບສະແດງໜ້າຟອມ ໃຫ້ດຶງເອົາສະເພາະລາຍການທີ່ເຄີຍ "ຂາຍແລ້ວ" ມາໃຫ້ເລືອກເຄມ
    from .models import SaleDetail

    sale_details = SaleDetail.objects.all().order_by("-sale__sale_date")

    return render(request, "store/add_claim.html", {"sale_details": sale_details})

@login_required(login_url="login")
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, sale_id=sale_id)
    details = SaleDetail.objects.filter(sale=sale)
    
    # ໄລ່ Sub Total ກ່ອນມີ VAT ແລະ ສ່ວນຫຼຸດ ເພື່ອສະແດງໃນ Form
    sub_total = sum(item.price * item.qty for item in details)

    payment_info = request.session.pop("payment_info", None)

    return render(
        request,
        "store/receipt.html", # ໃຊ້ Receipt ໜ້າເວັບປົກກະຕິ
        {
            "sale": sale,
            "details": details,
            "payment_info": payment_info,
            "sub_total": sub_total
        },
    )


@login_required(login_url="login")
def shop_settings(request):
    # ດຶງຂໍ້ມູນຮ້ານມາໃຊ້ ແລະ ຖ້າບໍ່ມີ ສ້າງ record ເອງ
    shop = ShopInfo.objects.first()
    if not shop:
        shop = ShopInfo.objects.create(
            shop_id="SH001", shop_name="Procom Store", tel="-", address="-"
        )

    if request.method == "POST":
        # ອັບເດດຂໍ້ມູນຮ້ານ ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ
        shop.shop_name = request.POST.get("shop_name")
        shop.tel = request.POST.get("tel")
        shop.address = request.POST.get("address")

        # ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ ແລະ ອັບເດດ logo ຖ້າມີ
        if "logo" in request.FILES:
            shop.logo = request.FILES[
                "logo"
            ]  # ອັບເດດ logo ຖ້າມີ file ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ

        shop.save()
        messages.success(request, "ບັນທຶກຂໍ້ມູນຮ້ານສຳເລັດແລ້ວ!")
        return redirect("shop_settings")

    return render(request, "store/shop_settings.html", {"shop": shop})


@login_required(login_url="login")
def import_stock(request):
    # ດຶງຂໍ້ມູນຜູ້ສະໜອງ ແລະ ສິນຄ້າ ເພື່ອໃຊ້ໃນ import stock form
    suppliers = Supplier.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        sup_id = request.POST.get("sup_id")
        pro_id = request.POST.get("pro_id")
        qty = int(request.POST.get("qty", 0))
        price = float(request.POST.get("price", 0))

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
                imp_id=imp_id, total_amount=total_amount, sup=supplier, emp=emp
            )

            ImportDetail.objects.create(
                imp=stock_imp, pro=product, qty=qty, price=price
            )

            #
            product.qty += qty
            product.price_buy = (
                price  # ອັບເດດລາຄາຊື້ໃນ product table ແລະ ກວດສອບວ່າ ມີ logo ແລ້ວ ຫຼື ຍັງ
            )
            product.save()

            messages.success(
                request, f"ນຳເຂົ້າສິນຄ້າ {product.pro_name} ຈຳນວນ {qty} ຊິ້ນ ສຳເລັດແລ້ວ!"
            )
            return redirect("import_stock")
        else:
            messages.error(request, "ກະລຸນາປ້ອນຈຳນວນ ແລະ ລາຄາໃຫ້ຖືກຕ້ອງ!")

    return render(
        request,
        "store/import_stock.html",
        {"suppliers": suppliers, "products": products},
    )

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