import random
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
import asyncio
from graphql.categories_graphql import fetch_categories_graphql
from graphql.orderBizItemSchedule import get_slot_id

# 환경 변수 로드
load_dotenv()
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.77 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

today_str = datetime.now().strftime("%Y-%m-%d")

def extract_category_ids(categories):
    ids = set()
    for cat in categories:
        ids.add(cat.get("id"))
    return list(ids)

# 메뉴 중복 제거 (이름 + 가격 기준)
def deduplicate_menus(menus: list):
    seen = set()
    unique_menus = []
    for m in menus:
        key = (m.get("name", "").strip(), m.get("price"))
        if key not in seen:
            seen.add(key)
            unique_menus.append(m)
    return unique_menus

# 2. 메뉴 유효 여부 체크
def is_valid_menu(menu: dict) -> bool:
    schedules = menu.get("schedules", {})
    today_schedule = schedules.get(today_str)
    if not today_schedule:
        return False
    stock = today_schedule.get("stock", 0)
    remain = today_schedule.get("remainStock", 0)
    return stock > 0 and remain > 0

# 4. 메뉴 가져오기
async def fetch_menu_graphql(place_id: str, booking_id: str, naverorder_id: str):
    url = "https://m.booking.naver.com/graphql?opName=menu"
    headers = {
        "accept": "*/*",
        "accept-encoding": "identity",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://m.booking.naver.com",
        "referer": f"https://m.booking.naver.com/order/bizes/{booking_id}/items/{naverorder_id}",
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
                    titleImageUrl
                    schedules
                    categoryIds
                }
            }
        }"""
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code != 200:
                print(f"❌ 메뉴 요청 실패: HTTP {resp.status_code}")
                return []

            data = resp.json()
            menu_list = data.get("data", {}).get("menu", {}).get("menus", [])
            menus = []
            for idx, m in enumerate(menu_list):
                if is_valid_menu(m):
                    menus.append(m)
            return menus
    except Exception as e:
        print(f"⚠️ 메뉴 GraphQL 실패: {e}")
        return []

# 5. 카테고리 기반 메뉴 필터링
def filter_menus_by_category(menu_list: list, valid_category_ids: list):
    filtered = []
    for menu in menu_list:
        menu_category_ids = menu.get("categoryIds", [])
        if any(cid in valid_category_ids for cid in menu_category_ids):
            filtered.append(menu)
    return filtered

# 여기가 메인이지
async def fetch_menu_for_place(place_id: str, booking_id: str, naverorder_id: str):
    slot_id = get_slot_id(place_id, booking_id, naverorder_id)

    print(f"place_id:{place_id}, booking_id:{booking_id}, naverorder_id:{naverorder_id}, slot_id:{slot_id}")

    valid_category_ids = await fetch_categories_graphql(place_id, booking_id, naverorder_id, slot_id)
    menus = await fetch_menu_graphql(place_id, booking_id, naverorder_id)

    menus = filter_menus_by_category(menus, valid_category_ids)
    menus = deduplicate_menus(menus)

    return [{
        "menu_id": f"{place_id}_{idx}",
        "place_id": place_id,
        "menu_name": m.get("name", "").strip(),
        "menu_price": int(m["price"]) if m.get("price") not in (None, "") else 0,
        "description": m.get("desc", ""),
        "image_url": m.get("titleImageUrl", ""),
    } for idx, m in enumerate(menus)]
