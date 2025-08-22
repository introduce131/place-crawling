import random
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

# 1. place_id, booking_id, naverorder_id 가져오기 (테스트용 단일 ID)
def get_booking_id():
    place_id = "31316673"  # 테스트할 place_id
    response = supabase.table("restaurant")\
        .select("place_id, booking_id, naverorder_id")\
        .eq("place_id", place_id)\
        .execute()
    return response.data or []

# 2. GraphQL 호출로 카테고리 가져오기
def get_slot_id(place_id: str, booking_id: str, naverorder_id: str):
    url = "https://m.booking.naver.com/graphql?opName=orderBizItemSchedule"

    headers = {
        "authority": "m.booking.naver.com",
        "method": "POST",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "identity",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://m.booking.naver.com",
        "priority": "u=1, i",
        "referer": f"https://m.booking.naver.com/order/bizes/{booking_id}/items/{naverorder_id}",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": random.choice(USER_AGENTS)
    }
    
    payload = {
        "operationName": "orderBizItemSchedule",
        "variables": {
            "input": {
                "lang": "ko",
                "businessId": booking_id,
                "bizItemId": naverorder_id,
                "fallback": {
                    "nextStartDate": "2025-08-21"
                }
            }
        },
        "query": """
        query orderBizItemSchedule($input: OrderBizItemScheduleParams) {
          orderBizItemSchedule(input: $input) {
            id
            isClosed
            schedule {
              id
              name
              slotId
              scheduleId
              detailScheduleId
              unitStartDateTime
              unitBookingCount
              unitStock
              isBusinessDay
              isSaleDay
              isUnitSaleDay
              isUnitBusinessDay
              duration
              desc
              minBookingCount
              maxBookingCount
              __typename
            }
            __typename
          }
        }
        """
    }

    try:
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code != 200:
                print(f"❌ orderBizItemSchedule 요청 실패: HTTP {resp.status_code}")
                return None

            data = resp.json()
            schedules = data.get("data", {}).get("orderBizItemSchedule", {}).get("schedule", [])
            if not schedules:
                return None
            
            print(f"{place_id}의 slotId : {schedules.get("slotId")}")

            return schedules.get("slotId")
    except Exception as e:
        print(f"⚠️ orderBizItemSchedule 호출 실패: {e}")
        return None
