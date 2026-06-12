# CLAUDE Instructions for Procom POS

ไฟล์นี้เป็นเอกสารสรุปข้อมูลโปรเจกต์ เพื่อให้ Claude หรือผู้พัฒนาที่เข้ามาใหม่เข้าใจโปรเจกต์ได้เร็วขึ้น

## ภาพรวมโปรเจกต์
- ชื่อโปรเจกต์: Procom POS
- เทคโนโลยีหลัก: Django 5, MySQL 8.0, Docker Compose
- ฟังก์ชันหลัก: ระบบขายหน้าร้าน, ตะกร้าสินค้า POS, รายการสินค้า, การนำเข้าสินค้า, ลูกค้า, ผู้จำหน่าย, พนักงาน, การเคลมสินค้า
- โฟลเดอร์หลัก: `store/` เป็นแอปหลักของระบบ

## สภาพแวดล้อม Docker
- `docker-compose.yml` มี service:
  - `db`: mysql:8.0, root password `1111111a`, database `procom_db`
  - `web`: Django app ที่รันด้วย `python manage.py runserver 0.0.0.0:8000`
- MySQL ถูกแมปพอร์ต `3307:3306` สำหรับโฮสต์
- volume ชื่อ `mysql_data` เก็บข้อมูล MySQL

## วิธีรันโปรเจกต์
1. เปิด Docker Desktop ให้พร้อมใช้งาน
2. จากโฟลเดอร์โปรเจกต์:
   ```bash
   docker compose up --build
   ```
3. ถ้าเป็นครั้งแรกหรือเปลี่ยน schema:
   ```bash
   docker-compose exec web python manage.py migrate
   ```
4. สร้าง superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
5. เข้าใช้งานเว็บผ่าน:
   - `http://0.0.0.0:8000/login/`

## Database & models สำคัญ
- ตารางหลักใน `store/models.py`:
  - `ShopInfo` → `tb_shop_info`
  - `Employee` → `tb_employees`
  - `Customer` → `tb_customers`
  - `Supplier` → `tb_suppliers`
  - `Category` → `tb_categories`
  - `Brand` → `tb_brands`
  - `Unit` → `tb_units`
  - `Product` → `tb_products`
  - `StockImport` → `tb_stock_imports`
  - `ImportDetail` → `tb_import_details`
  - `Sale` → `tb_sales`
  - `SaleDetail` → `tb_sale_details`
  - `Shipping` → `tb_shippings`
  - `Claim` → `tb_claims`

## ระบบล็อกอินและสิทธิ์
- `store/views.py` มี `login_view`
- ถ้า username/password ตรงกับ Django superuser จะล็อกอินเข้า `dashboard`
- ถ้าไม่ใช่ admin จะตรวจสอบใน table `Employee` โดยใช้ plain text password
- ถ้าพบพนักงาน จะสร้าง Django `User` ชั่วคราวเพื่อให้ session ทำงาน
- `login_view` ยังโหลดข้อมูล `ShopInfo.objects.first()` เพื่อแสดงข้อมูลร้านบนหน้า login

## โครงสร้างไฟล์หลัก
- `docker-compose.yml` — กำหนดคอนเทนเนอร์และ environment
- `procom_pos/settings.py` — ตั้งค่าฐานข้อมูล, static/media, app
- `store/models.py` — schema ของข้อมูลทั้งหมด
- `store/views.py` — ฟังก์ชันหลักของระบบ
- `store/urls.py` — เส้นทาง URL ของระบบ
- `store/templates/store/` — หน้า HTML ของแต่ละฟังก์ชัน
- `store/forms.py` — ฟอร์มสำหรับพนักงาน / สินค้า

## เส้นทางสำคัญ (routes)
- `/login/` — เข้าสู่ระบบ
- `/logout/` — ออกจากระบบ
- `/` — dashboard
- `/pos/` — หน้า POS
- `/products/` — รายการสินค้า
- `/shop-settings/` — ตั้งค่าร้าน
- `/claims/` — ระบบเคลม
- `/employees/` — จัดการพนักงาน
- `/categories/`, `/brands/`, `/units/` — จัดการหมวดหมู่/ยี่ห้อ/หน่วย
- `/customers/` — จัดการลูกค้า
- `/suppliers/` — จัดการผู้จำหน่าย

## ปัญหาที่พบบ่อย
- `ProgrammingError: Table 'procom_db.tb_shop_info' doesn't exist` → ยังไม่ได้รัน `migrate`
- ถ้า Docker ไม่มี Compose plugin ให้ติดตั้งและใช้ `docker-compose` หรือรัน `docker compose`
- ถ้า `docker compose up --build` ขึ้น socket error ให้ตรวจสอบ Docker Desktop และ context

## ถาม Claude ได้อย่างไร
- "ช่วยอธิบาย `login_view` ใน `store/views.py` ว่าทำงานอย่างไร"
- "ช่วยตรวจสอบ `ShopInfo` model กับ table `tb_shop_info` ว่าถูกต้องไหม"
- "ช่วยดูว่ามี security issue ในการเก็บรหัสพนักงานเป็น plain text หรือไม่"
- "ช่วยสรุป schema ของฐานข้อมูลจาก `store/models.py` เป็นตาราง"
- "ช่วยเพิ่ม route ใหม่สำหรับจัดการโปรโมชั่นหรือส่วนลดสินค้า"
- "ช่วยเขียน Django view และ template สำหรับฟีเจอร์ `sale_detail` หรือ `checkout`"

## ข้อเสนอแนะการใช้งาน
- ถ้าเจอ bug ให้เริ่มจาก:
  1. รัน `docker compose up --build`
  2. รัน `docker-compose exec web python manage.py migrate`
  3. ตรวจสอบ log ของ container ใน terminal
- เก็บข้อมูลสำคัญเช่นรหัสผ่านไว้ใน environment หรือ secret แทน hardcode ถ้าเป็น production
- ถ้าจะเพิ่มฟีเจอร์ใหม่ ให้ดู `store/views.py` และ `store/templates/store/` ก่อน

