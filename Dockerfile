# 1. Playwright 포함 Python 이미지 사용 (최신 안정 버전)
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 2. 앱 디렉토리 설정
WORKDIR /app

# 3. 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 4. 코드 복사
COPY . .

# 5. 캐시 무시하고 브라우저 재설치
RUN rm -rf /ms-playwright/.local-browsers && playwright install --with-deps

# 6. 포트 노출
EXPOSE 8000

# 7. 앱 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
