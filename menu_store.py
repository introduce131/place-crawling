import requests
import re
import json
import random
import time
import pytz
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import os

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.67",
]

# 메뉴가 하나도 없는 place_id만 가져오기
def get_place_ids_without_menu():
    limit = 1000
    offset = 0
    all_place_ids = []

    while True:
        response = (
            supabase.rpc("get_restaurants_without_menu")
            .range(offset, offset + limit - 1)
            .execute()
        )
        data = response.data
        if not data:
            break

        all_place_ids.extend(row['place_id'] for row in data)

        if len(data) < limit:
            break
        offset += limit

    return all_place_ids

def fix_encoding(text: str) -> str:
    try:
        return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        return text

def clean_image_url(url: str) -> str:
    return url.replace('\\u002F', '/').replace('\\/', '/')

def extract_menu_images(script_text: str):
    menu_images = []
    pattern = r'"menuImages"\s*:\s*(\[[\s\S]*?\])'
    match = re.search(pattern, script_text)

    if not match:
        print("❌ menuImages 블록을 찾을 수 없음")
        return []

    try:
        raw_array_text = match.group(1)
        raw_array_text = raw_array_text.replace('\n', '').replace('\r', '')
        menu_image_objs = json.loads(raw_array_text)
        for image in menu_image_objs:
            url = image.get("imageUrl")
            if url:
                menu_images.append(clean_image_url(url))
    except Exception as e:
        print(f"⚠️ menuImages 파싱 에러: {e}")

    return menu_images

def fetch_menu_from_script(business_id: str):
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/menu/list"
    headers = {
        "authority": "pcmap.place.naver.com",
        "method": "GET",  
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "user-agent": random.choice(USER_AGENTS),
        "referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/menu",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "connection": "keep-alive",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

    if response.status_code != 200:
        print(f"❌ Failed to fetch menu: HTTP {response.status_code}")
        return None

    raw_bytes = response.content
    decoded = raw_bytes.decode("utf-8", errors="ignore")

    pattern = rb'"(?:Menu:%b_\d+|PlaceDetail_BaeminMenu:\d+)"\s*:\s*\{.*?\}(?=,|\s*[\r\n]+\s*"|\s*\})' % business_id.encode()
    matches = re.findall(pattern, raw_bytes, re.DOTALL)

    menu_items = []

    for m in matches:
        try:
            text = m.decode("utf-8", errors="ignore")
            key_value_match = re.match(r'"[^"]*"\s*:\s*(\{.*\})', text, re.DOTALL)
            if not key_value_match:
                continue

            raw_json = key_value_match.group(1)
            obj = json.loads(raw_json)

            images = obj.get("images", [])
            cleaned_images = [clean_image_url(img) for img in images]

            price_raw = obj.get("price", "")
            try:
                price = int(price_raw)
            except:
                price = None

            menu_items.append({
                "name": fix_encoding(obj.get("name", "")),
                "price": price,
                "description": fix_encoding(obj.get("description", "")),
                "images": cleaned_images[0] if cleaned_images else ""
            })

        except Exception as e:
            print(f"⚠️ 메뉴 파싱 에러: {e}")
            continue

    menu_board_images = extract_menu_images(decoded)

    return {
        "menuItems": menu_items,
        "menuBoardImages": menu_board_images
    }

def insert_menu_data(place_id, menu_data):
    now = datetime.now(pytz.timezone('Asia/Seoul')).isoformat()

    # 메뉴 데이터 삽입
    for idx, item in enumerate(menu_data.get("menuItems", [])):
        menu_id = f"{place_id}_{idx}"
        data = {
            "menu_id": menu_id,
            "place_id": place_id,
            "menu_name": item["name"],
            "menu_price": item["price"],
            "description": item.get("description", ""),
            "image_url": item.get("images", ""),
            "create_dt": now
        }

        resp = supabase.table("menu").upsert(data).execute()
        if resp.data is None:
            print(f"⚠️ 메뉴 upsert 응답 없음 (menu_id={menu_id})")
        else:
            print(f"✅ 메뉴 저장 성공: {menu_id}")

    # 메뉴판 이미지 삽입
    for idx, img_url in enumerate(menu_data.get("menuBoardImages", [])):
        data = {
            "place_id": place_id,
            "image_url": img_url,
            "create_dt": now
        }

        resp = supabase.table("menu_board").upsert(data).execute()
        if resp.data is None:
            print(f"⚠️ 메뉴판 이미지 upsert 응답 없음 (place_id={place_id}, idx={idx})")
        else:
            print(f"✅ 메뉴판 이미지 저장 성공: {place_id}_{idx}")

def main():
    # 메뉴 없는 place_id 목록 가져오기
    place_ids = get_place_ids_without_menu()

    if not place_ids:
        print("✅ 모든 restaurant에 메뉴가 이미 있음")
        return

    print(f"🔍 총 {len(place_ids)}개 place_id에서 메뉴 누락됨")

    for i, place_id in enumerate(place_ids, start=1):
        print(f"[{i}/{len(place_ids)}] place_id: {place_id} 작업 시작")
        menu_data = fetch_menu_from_script(place_id)
        if menu_data:
            insert_menu_data(place_id, menu_data)
            print(f"[{i}/{len(place_ids)}] place_id: {place_id} 작업 완료")
        else:
            print(f"[{i}/{len(place_ids)}] place_id: {place_id} 메뉴 데이터 없음 또는 요청 실패")

        time.sleep(random.uniform(1.5, 3.0))

if __name__ == "__main__":
    main()
