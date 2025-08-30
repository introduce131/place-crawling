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

USER_AGENT_SETS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/126.0.6478.127 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Not A(Brand";v="99", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-platform": '"Windows"'
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Not A(Brand";v="99", "Safari";v="16", "AppleWebKit";v="605"',
        "sec-ch-ua-platform": '"macOS"'
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/125.0.6422.141 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        "sec-ch-ua": '"Not A(Brand";v="99", "Chromium";v="125", "Google Chrome";v="125"',
        "sec-ch-ua-platform": '"Linux"'
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"iOS";v="17", "Safari";v="17", "AppleWebKit";v="605"',
        "sec-ch-ua-platform": '"iOS"'
    },
    {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918N) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/126.0.6478.127 Mobile Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Not A(Brand";v="99", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-platform": '"Android"'
    }
]

def fix_encoding(s: str) -> str:
    try:
        return s.encode('latin1').decode('utf-8')
    except:
        return s

def log_message(msg: str):
    print(f"[{datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def fetch_data(business_id: str) -> dict:
    import requests
    
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"
    session = requests.Session()
    max_retries = 3
    ua_set = random.choice(USER_AGENT_SETS)

    for attempt in range(max_retries):
        headers = {
            "authority": "pcmap.place.naver.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "User-Agent": ua_set["User-Agent"],
            "Referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/home",
            "Accept-Language": ua_set["Accept-Language"],
            "Connection": "keep-alive",
            "sec-ch-ua": ua_set["sec-ch-ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": ua_set["sec-ch-ua-platform"],
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

                keyword_pattern = re.compile(r'"keywordList"\s*:\s*\[(.*?)\]', re.DOTALL)
                keyword_match = keyword_pattern.search(response.text)
                
                if keyword_match:
                    try:
                        keywords_raw = "[" + keyword_match.group(1) + "]"
                        keyword_list = json.loads(keywords_raw)
                        keyword_list = [fix_encoding(k) for k in keyword_list]
                    except json.JSONDecodeError:
                        keyword_list = []
                else:
                    keyword_list = []
                    
                return {
                    "lat": lat,
                    "lng": lng,
                    "road_address": road_address,
                    "review_total": reviewTotal,
                    "review_score": reviewScore,
                    "keyword_list": keyword_list,
                }
            else:
                log_message(f"Attempt {attempt+1}: PlaceDetailBase 데이터 없음 - 재시도 합니다.")
                time.sleep(2)

        except Exception as e:
            log_message(f"Attempt {attempt+1}: 에러 발생 - {e}")
            time.sleep(2)

    return {"error": "최대 재시도 후에도 데이터를 가져오지 못했습니다."}

def update_missing_coordinates():
    limit = 1000
    offset = 0
    total_count = 0

    while True:
        # 1000개씩 가져오기
        query = (
            supabase.table("restaurant_missing_data")
            .select("place_id")
            .range(offset, offset + limit - 1)
            .execute()
        )

        if not query.data:  # 더 이상 데이터 없으면 종료
            break

        place_ids = [item["place_id"] for item in query.data]
        log_message(f"Batch {offset//limit + 1}: {len(place_ids)}개 place_id 조회됨")
        total_count += len(place_ids)

        for i, pid in enumerate(place_ids, start=1):
            info = fetch_data(pid)
            if "error" not in info:
                # restaurant 업데이트
                update_data = {
                    "latitude": info.get("lat"),
                    "longitude": info.get("lng"),
                    "road_address": info.get("road_address", ""),
                    "review_count": info.get("review_total"),
                    "review_score": info.get("review_score"),
                    "updated_at": datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
                }
                response = (
                    supabase.table("restaurant")
                    .update(update_data)
                    .eq("place_id", pid)
                    .execute()
                )

                # place_keyword 업서트
                keyword_data = {
                    "place_id": pid,
                    "keywords": info.get("keyword_list", []),
                    "updated_at": datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
                }
                response2 = supabase.table("place_keyword").upsert(keyword_data).execute()

                if response.data is None:
                    log_message(f"[{offset+i}/{total_count}] {pid} 업데이트 실패")
                else:
                    log_message(f"[{offset+i}/{total_count}] {pid} 업데이트 완료")

                if response2.data is None:
                    log_message(f"[{offset+i}/{total_count}] {pid} 키워드 업서트 실패")
                else:
                    log_message(f"[{offset+i}/{total_count}] {pid} 키워드 업서트 완료")

            else:
                log_message(f"[{offset+i}/{total_count}] {pid} 재수집 실패")

            time.sleep(random.uniform(1.5, 3.0))

        offset += limit  # 다음 페이지로 이동

if __name__ == "__main__":
    update_missing_coordinates()
