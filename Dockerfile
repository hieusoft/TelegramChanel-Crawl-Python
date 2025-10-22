# Sử dụng Python nhẹ
FROM python:3.13-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements.txt trước để tận dụng cache
COPY requirements.txt .

# Cài đặt thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ dự án
COPY . .

# Biến môi trường để Python in log ngay lập tức
ENV PYTHONUNBUFFERED=1

# Chạy file chính
CMD ["python", "main.py"]
