FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# 필요 파일 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Uvicorn 실행 (host 바인딩 필요)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
