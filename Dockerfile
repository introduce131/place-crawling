# 1. Playwright 포함된 Python 환경 이미지 사용 (최신 버전 사용 시 안정 확인 필요)
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 복사 후 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 4. 나머지 코드 복사
COPY . .

# 5. Playwright 브라우저 설치 (필수)
RUN playwright install --with-deps

# 6. 포트 노출
EXPOSE 8000

# 7. FastAPI 앱 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
