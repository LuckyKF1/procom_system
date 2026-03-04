from django.contrib import admin
from .models import (Employee, Customer, Supplier, Category, Brand, Unit, 
                     Product, ShopInfo, StockImport, ImportDetail, 
                     Sale, SaleDetail, Shipping, Claim)
from django.urls import path, include

# เปลี่ยนชื่อหัวเว็บ Admin ให้ดูเป็นโปรเจกต์ของเรา
admin.site.site_header = "Procom System Admin"
admin.site.site_title = "Procom Admin Portal"
admin.site.index_title = "ຍິນດີຕ້ອນຮັບສູ່ລະບົບຈັດການຮ້ານ Procom"

# นำตารางทั้งหมดไปลงทะเบียน
admin.site.register(Employee)
admin.site.register(Customer)
admin.site.register(Supplier)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Unit)
admin.site.register(Product)
admin.site.register(ShopInfo)
admin.site.register(StockImport)
admin.site.register(ImportDetail)
admin.site.register(Sale)
admin.site.register(SaleDetail)
admin.site.register(Shipping)
admin.site.register(Claim)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),  # เชื่อมต่อกับ URLs ของแอปพลิเคชัน store
]