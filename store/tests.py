from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Category, Brand, Customer, Employee, ImportDetail, Payment, Product, Sale, StockImport, Supplier, Unit


class StockImportViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.employee = Employee.objects.create(
            emp_id='E100',
            emp_name='tester',
            surname='User',
            tel='0999999999',
            position='Manager',
            password='secret',
        )
        self.category = Category.objects.create(cat_id='C001', cat_name='Electronics')
        self.brand = Brand.objects.create(brand_id='B001', brand_name='Generic')
        self.unit = Unit.objects.create(unit_id='U001', unit_name='PCS')
        self.supplier = Supplier.objects.create(
            sup_id='S001',
            company_name='Test Supplier',
            tel='0888888888',
            address='Vientiane',
        )
        self.product = Product.objects.create(
            pro_id='P001',
            pro_name='Laptop',
            price_buy=100.0,
            price_sale=150.0,
            qty=5,
            cat=self.category,
            brand=self.brand,
            unit=self.unit,
        )

    def test_manual_stock_import_creates_record_and_logs_it(self):
        self.client.force_login(self.user)

        with self.assertLogs('store.views', level='INFO') as logs:
            response = self.client.post(reverse('import_stock'), {
                'sup_id': self.supplier.sup_id,
                'pro_id': self.product.pro_id,
                'qty': 3,
                'price': 120.0,
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(StockImport.objects.count(), 1)
        self.assertEqual(ImportDetail.objects.count(), 1)
        self.assertEqual(Product.objects.get(pro_id='P001').qty, 8)
        self.assertEqual(Product.objects.get(pro_id='P001').price_buy, 120.0)
        self.assertTrue(any('Stock import completed' in message for message in logs.output))

    def test_bulk_stock_import_upload_processes_each_row(self):
        self.client.force_login(self.user)
        csv_content = StringIO('sup_id,pro_id,qty,price\nS001,P001,2,110\nS001,P001,1,115\n')
        upload = SimpleUploadedFile('imports.csv', csv_content.getvalue().encode('utf-8'), content_type='text/csv')

        with self.assertLogs('store.views', level='INFO') as logs:
            response = self.client.post(reverse('import_stock'), {
                'import_file': upload,
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(StockImport.objects.count(), 2)
        self.assertEqual(Product.objects.get(pro_id='P001').qty, 8)
        self.assertTrue(any('Bulk stock import completed' in message for message in logs.output))


class PosCartExperienceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='cashier', password='secret123')
        self.category = Category.objects.create(cat_id='C002', cat_name='Accessories')
        self.brand = Brand.objects.create(brand_id='B002', brand_name='Test Brand')
        self.unit = Unit.objects.create(unit_id='U002', unit_name='PCS')
        self.product = Product.objects.create(
            pro_id='P002',
            pro_name='Mouse',
            price_buy=20.0,
            price_sale=35.0,
            qty=5,
            cat=self.category,
            brand=self.brand,
            unit=self.unit,
        )

    def test_cart_quantity_can_be_adjusted_directly_from_pos(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('add_to_cart', args=[self.product.pro_id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][self.product.pro_id]['quantity'], 1)

        response = self.client.post(reverse('update_cart_item', args=[self.product.pro_id, 'increase']))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][self.product.pro_id]['quantity'], 2)

        response = self.client.post(reverse('update_cart_item', args=[self.product.pro_id, 'decrease']))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][self.product.pro_id]['quantity'], 1)

        response = self.client.post(reverse('update_cart_item', args=[self.product.pro_id, 'decrease']))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.product.pro_id, self.client.session.get('cart', {}))


class PaymentModelTests(TestCase):
    def test_payment_can_be_created(self):
        employee = Employee.objects.create(
            emp_id='E001',
            emp_name='Test',
            surname='User',
            tel='0999999999',
            position='Cashier',
            password='secret',
        )
        customer = Customer.objects.create(
            cus_id='C001',
            cus_name='Test Customer',
            tel='0888888888',
            address='Vientiane',
        )
        sale = Sale.objects.create(
            sale_id='INV-26040001',
            total_amount=100.0,
            emp=employee,
            cus=customer,
            discount=0,
            vat_rate=0,
        )

        payment = Payment.objects.create(
            pay_id='PAY-001',
            sale=sale,
            amount=Decimal('100.00'),
            payment_method='Cash',
        )

        self.assertEqual(payment.sale, sale)
        self.assertEqual(str(payment), 'PAY-001')

    def test_sale_payment_summary_uses_decimal_safe_balances(self):
        employee = Employee.objects.create(
            emp_id='E002',
            emp_name='Test',
            surname='User',
            tel='0999999999',
            position='Cashier',
            password='secret',
        )
        customer = Customer.objects.create(
            cus_id='C002',
            cus_name='Test Customer',
            tel='0888888888',
            address='Vientiane',
        )
        sale = Sale.objects.create(
            sale_id='INV-26040002',
            total_amount=150.0,
            emp=employee,
            cus=customer,
            discount=0,
            vat_rate=0,
        )
        Payment.objects.create(
            pay_id='PAY-002',
            sale=sale,
            amount=Decimal('100.00'),
            payment_method='Cash',
        )

        amount_paid = sum(payment.amount for payment in Payment.objects.filter(sale=sale))
        sale_total = Decimal(str(sale.total_amount))
        balance_due = max(sale_total - amount_paid, Decimal('0.00'))
        change_due = max(amount_paid - sale_total, Decimal('0.00'))

        self.assertEqual(amount_paid, Decimal('100.00'))
        self.assertEqual(balance_due, Decimal('50.00'))
        self.assertEqual(change_due, Decimal('0.00'))
