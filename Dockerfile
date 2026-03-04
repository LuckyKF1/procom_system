# ใช้ Python เวอร์ชั่น 3.10
FROM python:3.10-slim

# ตั้งค่าไม่ให้ Python สร้างไฟล์ .pyc และให้แสดง log ทันที
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ติดตั้งเครื่องมือที่จำเป็นสำหรับ MySQLclient
RUN apt-get update \
    && apt-get install -y pkg-config libmariadb-dev-compat libmariadb-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# ตั้งค่าโฟลเดอร์ทำงานใน Docker
WORKDIR /app

# ก๊อปปี้ไฟล์ requirements.txt และติดตั้ง
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดทั้งหมดลงใน Docker
COPY . /app/