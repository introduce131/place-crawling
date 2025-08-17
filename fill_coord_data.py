import time
import random
import json
import re
import os
from supabase import create_client, Client
from datetime import datetime
import pytz
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")

# supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

USER_AGENTS = [
    # Windows - Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

    # macOS - Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",

    # Linux - Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",

    # Windows - Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",

    # macOS - Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",

    # Android - Chrome
    "Mozilla/5.0 (Linux; Android 10; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.77 Mobile Safari/537.36",

    # iPhone - Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",

    # iPad - Safari
    "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",

    # Windows 11 - Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.67",
]

def fix_encoding(s: str) -> str:
    try:
        return s.encode('latin1').decode('utf-8')
    except:
        return s

def log_message(msg: str):
    print(f"[{datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def extract_booking_id(script_text: str):
    pattern = r'"bookingBusinessId"\s*:\s*"(\d+)"'
    match = re.search(pattern, script_text)
    if match:
        return match.group(1)
    return None

def fetch_data(business_id: str) -> dict:
    import requests
    
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"
    session = requests.Session()
    max_retries = 3

    for attempt in range(max_retries):
        headers = {
            "authority": "pcmap.place.naver.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/home",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"19.0.0"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
        }
        session.headers.update(headers)

        try:
            time.sleep(random.uniform(1.8, 3.5))

            response = session.get(url)
            if response.status_code != 200:
                log_message(f"Attempt {attempt+1}: HTTP {response.status_code} - 재시도 합니다.")
                time.sleep(2)
                continue

            pattern = re.compile(r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});", re.DOTALL)
            match = pattern.search(response.text)

            if not match:
                log_message(f"Attempt {attempt+1}: __APOLLO_STATE__ 데이터 없음 - 재시도 합니다.")
                time.sleep(2)
                continue

            apollo_state = json.loads(match.group(1))
            place_data = apollo_state.get(f"PlaceDetailBase:{business_id}")
            if place_data:
                lat = float(place_data["coordinate"].get("y")) if place_data.get("coordinate") else None
                lng = float(place_data["coordinate"].get("x")) if place_data.get("coordinate") else None
                road_address = fix_encoding(place_data.get("roadAddress", ""))
                reviewTotal = place_data.get("visitorReviewsTotal", None)
                reviewScore = place_data.get("visitorReviewsScore", None)

                # bookingBusinessId(네이버 주문 고유 ID)와
                # 'pickup'(포장) 타입의 NaverOrderItem ID를 추출
                booking_id = extract_booking_id(response.text)
                naverOrderItem = None

                for key, value in apollo_state.items():
                    if isinstance(key, str) and key.startswith("NaverOrderItem:"):
                        if isinstance(value, dict) and value.get("type") == "pickup":
                            naverOrderItem = value.get("id")

                return {
                    "lat": lat,
                    "lng": lng,
                    "road_address": road_address,
                    "review_total": reviewTotal,
                    "review_score": reviewScore,
                    "booking_id" : booking_id,
                    "naverorder_id" : naverOrderItem,
                }
            else:
                log_message(f"Attempt {attempt+1}: PlaceDetailBase 데이터 없음 - 재시도 합니다.")
                time.sleep(2)

        except Exception as e:
            log_message(f"Attempt {attempt+1}: 에러 발생 - {e}")
            time.sleep(2)

    return {"error": "최대 재시도 후에도 데이터를 가져오지 못했습니다."}

def update_missing_coordinates():
    batch_size = 1000
    offset = 0

    while True:
        # 1. Supabase에서 batch_size만큼 데이터 가져오기
        query = supabase.table("restaurant")\
                .select("place_id")\
                .or_("latitude.is.null,longitude.is.null,booking_id.is.null,naverorder_id.is.null")\
                .is_("processed_at", "null")\
                .range(offset, offset + batch_size - 1)\
                .execute()

        if not query.data:  # 데이터 없으면 종료
            log_message("✅ 모든 place_id 처리 완료")
            break

        place_ids = [item["place_id"] for item in query.data]
        log_message(f"📦 Batch {offset // batch_size + 1} → {len(place_ids)}개 place_id 조회됨")

        # 2. 데이터 처리
        for i, pid in enumerate(place_ids, start=1):
            info = fetch_data(pid)
            if "error" not in info:
                update_data = {
                    "latitude": info.get("lat"),
                    "longitude": info.get("lng"),
                    "road_address": info.get("road_address", ""),
                    "review_count": info.get("review_total"),
                    "review_score": info.get("review_score"),
                    "booking_id": info.get("booking_id"),
                    "naverorder_id": info.get("naverorder_id"),
                    "updated_at": datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
                }
                response = supabase.table("restaurant")\
                    .update(update_data)\
                    .eq("place_id", pid)\
                    .execute()

                if response.data is None:
                    log_message(f"[{i}/{len(place_ids)}] place_id {pid} ❌ 업데이트 실패")
                else:
                    log_message(f"[{i}/{len(place_ids)}] place_id {pid} ✅ 업데이트 완료")
            else:
                log_message(f"[{i}/{len(place_ids)}] place_id {pid} ⚠️ 재수집 실패")

            time.sleep(random.uniform(1.5, 3.0))  # API 부담 줄이기

        # 3. 다음 배치로 이동
        offset += batch_size

if __name__ == "__main__":
    update_missing_coordinates()
