from fastapi import FastAPI, Query, Path
from typing import Optional, Dict, List
from supabase import create_client, Client
import os
import httpx
import re
import json
import requests
import random

app = FastAPI()

SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

# ---------------------------------
# 공통적으로 사용하는 변수, 함수는 이곳에
# ---------------------------------
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

def _extract_array_after_pos(html: str, pos: int) -> str | None:
    br = html.find('[', pos)
    if br == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(br, len(html)):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return html[br:i+1]
    return None

def _find_business_hours_array(html: str):
    m = re.search(r'"newBusinessHours\([^)]*\)"\s*:\s*\[', html)
    if m:
        arr_str = _extract_array_after_pos(html, m.start())
        if arr_str:
            try:
                arr = json.loads(arr_str)
                for obj in arr:
                    if isinstance(obj, dict) and isinstance(obj.get("businessHours"), list):
                        return obj["businessHours"]
            except Exception:
                pass

    for mm in re.finditer(r'"businessHours"\s*:\s*\[', html):
        arr_str = _extract_array_after_pos(html, mm.start())
        if not arr_str:
            continue
        try:
            arr = json.loads(arr_str)
        except Exception:
            continue
        if (
            isinstance(arr, list) and arr and isinstance(arr[0], dict)
            and "day" in arr[0] and "businessHours" in arr[0]
        ):
            return arr
    return None

def sort_business_hours(bh_list: list) -> list:
    weekday_order = ["월", "화", "수", "목", "금", "토", "일"]
    def get_index(item):
        day = item.get("day")
        if day == "매일":
            return -1
        try:
            return weekday_order.index(day)
        except ValueError:
            return 100
    return sorted(bh_list, key=get_index)

async def fetch_business_hours(business_id: str):
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"

    headers = {
            "authority": "pcmap.place.naver.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": url,
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

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
        except Exception:
            return []
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception:
        return []  # 요청 실패 시 빈 리스트 반환

    html = r.text
    bh_list = _find_business_hours_array(html)
    if not bh_list:
        return []  # businessHours 없으면 빈 리스트 반환

    results = []
    for info in bh_list:
        if not isinstance(info, dict):
            continue
        bh = info.get("businessHours") or {}
        last_orders = []
        for lo in info.get("lastOrderTimes") or []:
            if isinstance(lo, dict) and "time" in lo:
                last_orders.append(lo["time"])
        results.append({
            "day": fix_encoding(info.get("day")),
            "start": bh.get("start"),
            "end": bh.get("end"),
            "lastOrder": last_orders
        })

    return sort_business_hours(results)

# -------------------------------
# restaurant API
# -------------------------------
@app.get("/restaurant/{place_id}")
def get_restaurant_detail(
    place_id: str = Path(..., description="가게 고유 ID")) -> Dict:
    
    res = supabase.table("restaurant").select("*").eq("place_id", place_id).single().execute()
    if res.data is None:
        return {"error": "해당 place_id가 존재하지 않습니다."}
    restaurant = res.data

    # 메뉴
    menu_res = supabase.table("menu")\
        .select("menu_id, place_id, menu_name, menu_price, description, image_url")\
        .eq("place_id", place_id)\
        .order("index", desc=False)\
        .execute()
    menu = menu_res.data if menu_res.data else []

    # 네이버 주문 메뉴
    booking_menu_res = supabase.table("booking_menu")\
        .select("menu_id, place_id, menu_name, menu_price, description, image_url")\
        .eq("place_id", place_id)\
        .order("index", desc=False)\
        .execute()
    booking_menu = booking_menu_res.data if booking_menu_res.data else []

    # 메뉴판 이미지
    board_res = supabase.table("menu_board").select("image_url").eq("place_id", place_id).execute()
    menu_board = board_res.data if board_res.data else []

    # 식당 키워드
    keyword_res = supabase.table("place_keyword").select("keywords").eq("place_id", place_id).single().execute()
    keywords = keyword_res.data["keywords"] if keyword_res.data else []

    # 결과 합치기
    return {
        "restaurant": restaurant,
        "menu": menu,
        "booking_menu": booking_menu,
        "menu_board": menu_board,
        "keywords": keywords
    }

@app.get("/restaurant/{business_id}/hours", response_model=List[Dict])
async def get_business_hours(
    business_id: str = Path(..., description="네이버 플레이스 가게 고유 ID")
):
    return await fetch_business_hours(business_id)
    
@app.get("/restaurants", response_model=List[Dict])
def search_restaurants(
    lat: float = Query(..., description="사용자 위도"),
    lng: float = Query(..., description="사용자 경도"),
    category_group: Optional[str] = Query(None, description="대분류 카테고리, 없으면 전체 조회"),
    radius: int = Query(5000, description="반경(m), 기본 5km")
):
    # get_restaurants() 함수를 RPC로 호출
    response = supabase.rpc(
        "get_restaurants",
        {
            "p_lat": lat,
            "p_lng": lng,
            "p_category_group": category_group,
            "p_radius": radius
        }
    ).execute()

    if response.data is None:
        return {"error": "Supabase RPC 호출 실패"}

    return response.data

# -------------------------------
# MENU API
# -------------------------------
@app.get("/menu")
def fetch_menu_from_script(business_id: str = Query(...)) -> List[Dict]:
    pass  # 실제 구현은 삭제
