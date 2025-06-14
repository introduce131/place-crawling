# ✅ 최신 이미지 사용
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# ✅ 환경변수 설정 (Render에서 종종 필요함)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# ✅ 작업 디렉토리
WORKDIR /app

# ✅ 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ✅ 앱 복사
COPY . .

# ✅ 명시적으로 설치 (캐시 무효화)
RUN rm -rf /ms-playwright/.local-browsers && playwright install --with-deps

# ✅ 포트
EXPOSE 8000

# ✅ 서버 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
