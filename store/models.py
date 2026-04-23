from django.db import models
import datetime

# D1: ຕາຕະລາງພະນັກງານ
class Employee(models.Model):
    emp_id = models.CharField(max_length=10, primary_key=True)
    emp_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)
    position = models.CharField(max_length=30)
    password = models.CharField(max_length=255)

    class Meta: db_table = 'tb_employees'

# D2: ຕາຕະລາງລູກຄ້າ
class Customer(models.Model):
    cus_id = models.CharField(max_length=10, primary_key=True)
    cus_name = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)
    address = models.TextField()

    class Meta: db_table = 'tb_customers'

# D3: ຕາຕະລາງຜູ້ສະໜອງ (Supplier)
class Supplier(models.Model):
    sup_id = models.CharField(max_length=10, primary_key=True)
    company_name = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)
    address = models.TextField()

    class Meta: db_table = 'tb_suppliers'

# D4: ຕາຕະລາງປະເພດສິນຄ້າ
class Category(models.Model):
    cat_id = models.CharField(max_length=10, primary_key=True)
    cat_name = models.CharField(max_length=50)

    class Meta: db_table = 'tb_categories'

# D5: ຕາຕະລາງຍີ່ຫໍ້
class Brand(models.Model):
    brand_id = models.CharField(max_length=10, primary_key=True)
    brand_name = models.CharField(max_length=50)

    class Meta: db_table = 'tb_brands'

# D6: ຕາຕະລາງຫົວໜ່ວຍ
class Unit(models.Model):
    unit_id = models.CharField(max_length=10, primary_key=True)
    unit_name = models.CharField(max_length=50)

    class Meta: db_table = 'tb_units'

# D7: ຕາຕະລາງສິນຄ້າ
class Product(models.Model):
    pro_id = models.CharField(max_length=10, primary_key=True)
    pro_name = models.CharField(max_length=100)
    price_buy = models.FloatField()
    price_sale = models.FloatField()
    qty = models.IntegerField(default=0)
    cat = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='cat_id')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, db_column='brand_id')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_column='unit_id')
    pro_img = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return self.pro_name

    class Meta: db_table = 'tb_products'

# D8: ຕາຕະລາງຂໍ້ມູນຮ້ານ
class ShopInfo(models.Model):
    shop_id = models.CharField(max_length=10, primary_key=True)
    shop_name = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)
    address = models.TextField()
    logo = models.ImageField(upload_to='shop_logo/', null=True, blank=True)

    class Meta: db_table = 'tb_shop_info'

# D9: ຕາຕະລາງນຳເຂົ້າສິນຄ້າ
class StockImport(models.Model):
    imp_id = models.CharField(max_length=10, primary_key=True)
    imp_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField()
    sup = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_column='sup_id')
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='emp_id')

    class Meta: db_table = 'tb_stock_imports'

# D10: ຕາຕະລາງລາຍລະອຽດການນຳເຂົ້າ
class ImportDetail(models.Model):
    imp = models.ForeignKey(StockImport, on_delete=models.CASCADE, db_column='imp_id')
    pro = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='pro_id')
    qty = models.IntegerField()
    price = models.FloatField()

    class Meta: db_table = 'tb_import_details'

def generate_sale_id():
    import datetime
    today = datetime.date.today()
    prefix = f"INV-{today.strftime('%y%m')}"  # ເອົາແຕ່ 2 ຫຼັກທ້າຍຂອງປີ
    # ຫາປີ ແລະ ເດືອນປັດຈຸບັນ ເຊັ່ນ: 2604 (2026 / ເດືອນ 04)
    now = datetime.datetime.now()
    date_prefix = now.strftime("%y%m") # ໃຊ້ %y ເພື່ອເອົາແຕ່ 2 ຫຼັກທ້າຍຂອງປີ
    
    # ຫາ Sale ລ່າສຸດໃນ Database
    last_sale = Sale.objects.filter(sale_id__icontains=prefix).order_by('-sale_id').first()
    
    if last_sale and last_sale.sale_id.startswith(f"INV-{date_prefix}"):
        # ດຶງເລກ 4 ຫຼັກທ້າຍມາບວກ 1
        last_no = int(last_sale.sale_id[-4:])
        new_no = last_no + 1
    elif last_sale and last_sale.sale_id.startswith(f"QT-{date_prefix}"):
        # ກໍລະນີມີ QT ຢູ່ແລ້ວ ກໍໃຫ້ນັບຕໍ່ (ຫຼື ຈະແຍກ Logic ກໍໄດ້)
        last_no = int(last_sale.sale_id[-4:])
        new_no = last_no + 1
    else:
        new_no = 1

    # ສົ່ງຄ່າກັບເປັນ Format: INV-26040001 (04d ຄືໃຫ້ມີເລກ 0 ທາງໜ້າ 4 ໂຕ)
    return f"INV-{date_prefix}{new_no:04d}"

# D11: ຕາຕະລາງການຂາຍ
class Sale(models.Model):
    sale_id = models.CharField(max_length=15, primary_key=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField()
    cus = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='cus_id', null=True)
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='emp_id')
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # ເກັບ % ພາສີ
    STATUS_CHOICES = [
        ('Quotation', 'ໃບສະເໜີລາຄາ'),
        ('Paid', 'ຊຳລະແລ້ວ'),
        ('Unpaid', 'ຄ້າງຊຳລະ'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Paid')

    class Meta: db_table = 'tb_sales'

# D12: ຕາຕະລາງລາຍລະອຽດການຂາຍ (ມີ warranty_end ຕາມທີ່ລົມກັນ)
class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, db_column='sale_id')
    pro = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='pro_id')
    qty = models.IntegerField()
    price = models.FloatField()
    warranty_end = models.DateField(null=True, blank=True)

    class Meta: db_table = 'tb_sale_details'

# D13: ຕາຕະລາງການຈັດສົ່ງ
class Shipping(models.Model):
    ship_id = models.CharField(max_length=10, primary_key=True)
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, db_column='sale_id')
    ship_date = models.DateTimeField(auto_now_add=True)
    tracking_no = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=30, default='Pending')

    class Meta: 
        db_table = 'tb_shippings'

    def save(self, *args, **kwargs):
        if not self.ship_id:
            # Logic: ດຶງ ID ຫຼ້າສຸດມາແລ້ວບວກ 1
            last_ship = Shipping.objects.all().order_by('ship_id').last()
            if last_ship:
                last_id = int(last_ship.ship_id[2:]) # ຕັດ SH ອອກແລ້ວແປງເປັນຕົວເລກ
                self.ship_id = 'SH' + str(last_id + 1).zfill(5)
            else:
                self.ship_id = 'SH00001'
        super(Shipping, self).save(*args, **kwargs)

# D14: ຕາຕະລາງການເຄມສິນຄ້າ
class Claim(models.Model):
    claim_id = models.CharField(max_length=10, primary_key=True)
    claim_date = models.DateTimeField(auto_now_add=True)
    sale_detail = models.ForeignKey(SaleDetail, on_delete=models.CASCADE)
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='emp_id')
    symptom = models.TextField()
    status = models.CharField(max_length=30, default='Processing')

    class Meta: db_table = 'tb_claims'