from django.contrib import admin
from .models import (
    Employee, Customer, Supplier, Category, Brand, Unit, 
    Product, ShopInfo, StockImport, ImportDetail, 
    Sale, SaleDetail, Shipping, Claim
)
from django.urls import path, include

#ລົງທະບຽນແບບສະແດງລາຍລະອຽດໃນຕາຕະລາງ Admin ໃຫ້ເບິ່ງສວຍງາມ
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('pro_id', 'pro_name', 'price_sale', 'qty', 'cat', 'brand')
    search_fields = ('pro_id', 'pro_name')
    list_filter = ('cat', 'brand')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'sale_date', 'total_amount', 'emp', 'status')
    list_filter = ('status', 'sale_date')

@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    list_display = ('shop_id', 'shop_name', 'tel')

#ລົງທພບຽນຕາຕະລາງອື່ນໆ ແບບທົ່ວໄປ
admin.site.register(Employee)
admin.site.register(Customer)
admin.site.register(Supplier)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Unit)
admin.site.register(StockImport)
admin.site.register(ImportDetail)
admin.site.register(SaleDetail)
admin.site.register(Shipping)
admin.site.register(Claim)

