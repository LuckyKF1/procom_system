from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
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


class EmployeeLoginSecurityTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            emp_id='E900',
            emp_name='cashier',
            surname='User',
            tel='0777777777',
            position='Cashier',
            password='plain-legacy-pw',
        )

    def test_legacy_plain_text_password_is_accepted_once_and_upgraded_to_a_hash(self):
        response = self.client.post(reverse('login'), {'username': 'cashier', 'password': 'plain-legacy-pw'})

        self.assertRedirects(response, reverse('dashboard'))
        self.employee.refresh_from_db()
        self.assertNotEqual(self.employee.password, 'plain-legacy-pw')
        self.assertTrue(check_password('plain-legacy-pw', self.employee.password))

    def test_hashed_employee_password_is_accepted(self):
        self.employee.password = make_password('hashed-pw')
        self.employee.save(update_fields=['password'])

        response = self.client.post(reverse('login'), {'username': 'cashier', 'password': 'hashed-pw'})

        self.assertRedirects(response, reverse('dashboard'))

    def test_employee_with_empty_password_cannot_log_in(self):
        self.employee.password = ''
        self.employee.save(update_fields=['password'])

        response = self.client.post(reverse('login'), {'username': 'cashier', 'password': ''})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_employee_login_cannot_take_over_a_superuser_account(self):
        get_user_model().objects.create_superuser(username='cashier', password='admin-only-pw')

        response = self.client.post(reverse('login'), {'username': 'cashier', 'password': 'plain-legacy-pw'})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_session_user_created_for_an_employee_has_no_privileges(self):
        self.client.post(reverse('login'), {'username': 'cashier', 'password': 'plain-legacy-pw'})

        user = get_user_model().objects.get(username='cashier')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())


class ViewPermissionTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username='boss', password='secret123')
        self.staff_user = get_user_model().objects.create_user(username='clerk', password='secret123')
        self.category = Category.objects.create(cat_id='C900', cat_name='Electronics')
        self.employee = Employee.objects.create(
            emp_id='E901',
            emp_name='victim',
            surname='User',
            tel='0777777777',
            position='Cashier',
            password=make_password('original-pw'),
        )

    def test_anonymous_user_cannot_edit_an_employee(self):
        response = self.client.post(reverse('employee_edit', args=[self.employee.emp_id]), {
            'emp_name': 'victim',
            'surname': 'User',
            'tel': '0777777777',
            'position': 'Cashier',
            'password': 'hacked',
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.headers['Location'])
        self.employee.refresh_from_db()
        self.assertTrue(check_password('original-pw', self.employee.password))

    def test_non_admin_user_cannot_edit_an_employee(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(reverse('employee_edit', args=[self.employee.emp_id]), {
            'emp_name': 'victim',
            'surname': 'User',
            'tel': '0777777777',
            'position': 'Cashier',
            'password': 'hacked',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].startswith(reverse('dashboard')))
        self.employee.refresh_from_db()
        self.assertTrue(check_password('original-pw', self.employee.password))

    def test_admin_editing_an_employee_stores_a_hashed_password(self):
        self.client.force_login(self.admin)

        self.client.post(reverse('employee_edit', args=[self.employee.emp_id]), {
            'emp_name': 'victim',
            'surname': 'User',
            'tel': '0777777777',
            'position': 'Cashier',
            'password': 'brand-new-pw',
        })

        self.employee.refresh_from_db()
        self.assertTrue(check_password('brand-new-pw', self.employee.password))

    def test_editing_an_employee_without_a_new_password_keeps_the_current_one(self):
        self.client.force_login(self.admin)

        self.client.post(reverse('employee_edit', args=[self.employee.emp_id]), {
            'emp_name': 'victim renamed',
            'surname': 'User',
            'tel': '0777777777',
            'position': 'Cashier',
            'password': '',
        })

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.emp_name, 'victim renamed')
        self.assertTrue(check_password('original-pw', self.employee.password))

    def test_anonymous_user_cannot_delete_master_data(self):
        response = self.client.post(reverse('delete_category', args=[self.category.cat_id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.headers['Location'])
        self.assertTrue(Category.objects.filter(cat_id='C900').exists())

    def test_delete_is_rejected_over_get(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('delete_category', args=[self.category.cat_id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Category.objects.filter(cat_id='C900').exists())

    def test_delete_works_over_post_for_a_logged_in_user(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('delete_category', args=[self.category.cat_id]))

        self.assertRedirects(response, reverse('category_list'))
        self.assertFalse(Category.objects.filter(cat_id='C900').exists())

    def test_adding_an_employee_stores_a_hashed_password(self):
        self.client.force_login(self.admin)

        self.client.post(reverse('add_employee'), {
            'emp_id': 'E902',
            'emp_name': 'newbie',
            'surname': 'User',
            'tel': '0777777777',
            'position': 'Cashier',
            'password': 'new-employee-pw',
        })

        employee = Employee.objects.get(emp_id='E902')
        self.assertTrue(check_password('new-employee-pw', employee.password))
