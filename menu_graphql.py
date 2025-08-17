import random
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
import time 

# 환경 변수 로드
load_dotenv()
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

# 1. place_id, booking_id, naverorder_id 가져오기
def get_booking_id():
    response = supabase.rpc("get_restaurants_missing_menu").execute()
    return response.data or []

# 2. GraphQL 호출로 메뉴 가져오기
def fetch_menu_graphql(place_id: str, booking_id: str, naverorder_id: str):
    url = "https://m.booking.naver.com/graphql?opName=menu"
    headers = {
        "authority": "m.booking.naver.com",
        "method": "POST",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://m.booking.naver.com",
        "priority": "u=1, i",
        "referer": f"https://m.booking.naver.com/order/bizes/{booking_id}/items/{naverorder_id}?theme=place&service-target=map-pc&refererCode=menutab&lang=ko&area=pll",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": random.choice(USER_AGENTS)
    }

    payload = {
        "operationName": "menu",
        "variables": {
            "input": {
                "lang": "ko",
                "businessId": booking_id,
                "bizItemType": "PICKUP",
                "projections": "order_booking_count,CATEGORY,HAS_SUB_OPTION,review_score_avg",
                "fallback": {"isToday": True}
            }
        },
        "query": """query menu($input: MenuParams) {
            menu(input: $input) {
                menus {
                    id
                    name
                    desc
                    price
                    normalPrice
                    titleImageUrl
                    discountRate
                    isTodaySoldOut
                    reviewScore
                }
            }
        }"""
    }

    try:
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code != 200:
                print(f"❌ 요청 실패: HTTP {resp.status_code}")
                return []

            data = resp.json()
            menu_list = data.get("data", {}).get("menu", {}).get("menus", [])
            
            menus = []
            for idx, m in enumerate(menu_list):
                menus.append({
                    "menu_id": f"{place_id}_{idx}",
                    "place_id": place_id,
                    "menu_name": m.get("name", "").strip(),
                    "menu_price": m.get("price"),
                    "description": m.get("desc", ""),
                    "image_url": m.get("titleImageUrl", "")
                })

            return menus
    except Exception as e:
        print(f"⚠️ GraphQL 호출 실패: {e}")
        return []

# 3. 메인 함수
def main():
    restaurants = get_booking_id()
    if not restaurants:
        print("✅ restaurant 테이블에 처리할 데이터 없음")
        return

    print(f"🔍 총 {len(restaurants)}개 restaurant에서 메뉴 수집 시작")

    for i, r in enumerate(restaurants, start=1):
        place_id = r["place_id"]
        booking_id = r["booking_id"]
        naverorder_id = r["naverorder_id"]

        print(f"[{i}/{len(restaurants)}] place_id: {place_id} 메뉴 수집 시작")
        menus = fetch_menu_graphql(place_id, booking_id, naverorder_id)

        if menus:
            for item in menus:
                supabase.table("booking_menu").upsert(item).execute()
            print(f"[{i}/{len(restaurants)}] place_id: {place_id} 메뉴 저장 완료 ({len(menus)}개)")
        else:
            print(f"[{i}/{len(restaurants)}] place_id: {place_id} 메뉴 없음 또는 요청 실패")

        time.sleep(random.uniform(1.5, 3.0))
if __name__ == "__main__":
    main()
