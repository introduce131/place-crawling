import random
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import json
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
        key = (m.get("menu_name", "").strip(), m.get("menu_price"))
        if key not in seen:
            seen.add(key)
            unique_menus.append(m)
    return unique_menus

def get_restaurant_by_place_id(place_id: str):
    res = (
        supabase.table("restaurant")
        .select("place_id, booking_id, naverorder_id")
        .eq("place_id", place_id)
        .single()
        .execute()
    )
    return res.data if res.data else None

# 5. 카테고리 기반 메뉴 필터링
def filter_menus_by_category(menu_list: list, valid_category_ids: list):
    filtered = []
    for menu in menu_list:
        # menu_category_id가 문자열이면 리스트로 변환
        menu_category_ids = [menu.get("categoryId", "")]

        if any(cid in valid_category_ids for cid in menu_category_ids):
            filtered.append(menu)
    return filtered

def fetch_menu_groups(place_id: str, booking_id: str, naverorder_id: str):
    url = "https://m.booking.naver.com/graphql?opName=menuGroups"
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
        "operationName": "menuGroups",
        "variables": {
            "withMenuGroupOptions": False,
            "withMenuGroups": True,
            "withPopularMenuGroups": False,
            "withOrderDetails": False,
            "menuGroupsInput": {
                "businessId": booking_id,
                "withReviewScore": False,
                "withBookingCount": False,
                "lang": "ko",
                "fallback": {}
            }
        },
        "query": """query menuGroups($menuGroupsInput: MenuGroupParams) {
            menuGroups(input: $menuGroupsInput) @include(if: true) {
                menus {
                    id
                    categoryId
                    name
                    price
                    impPrice
                    titleImageUrl
                    desc
                }
            }
        }"""
    }

    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"⚠️ GraphQL 호출 실패: {e}")
        return []

    menu_groups = data.get("data", {}).get("menuGroups", [])
    if not menu_groups:
        print("⚠️ menuGroups 데이터 없음")
        return []

    menus = []
    for m in menu_groups.get("menus", []):
        menus.append({
            "menu_id": f"{place_id}_{m.get('id', '0')}",
            "place_id": place_id,
            "categoryId": m.get("categoryId", ""),
            "menu_name": m.get("name", "").strip(),
            "menu_price": m.get("price") or m.get("impPrice"),
            "description": m.get("desc", ""),
            "image_url": m.get("titleImageUrl", "")
        })
    return menus

async def fetch_menu_groups_for_place(place_id: str):
    restaurant = get_restaurant_by_place_id(place_id)
    if not restaurant:
        print(f"❌ place_id {place_id} 해당 데이터 없음")
        return []

    booking_id = restaurant["booking_id"]
    naverorder_id = restaurant["naverorder_id"]
    slot_id = get_slot_id(place_id, booking_id, naverorder_id)

    valid_category_ids = await fetch_categories_graphql(place_id, booking_id, naverorder_id, slot_id)
    menus = await fetch_menu_groups(place_id, booking_id, naverorder_id)
    
    menus = filter_menus_by_category(menus, valid_category_ids)
    menus = deduplicate_menus(menus)

    return menus