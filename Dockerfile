# 1. Playwright 포함된 Python 환경 이미지 사용
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 2. 작업 디렉토리 지정
WORKDIR /app

# 3. requirements.txt 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 전체 코드 복사
COPY . .

# 5. 포트 개방
EXPOSE 8000

# 6. FastAPI 실행 명령
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
