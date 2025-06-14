from fastapi import FastAPI, Query
from typing import Dict, List, Optional
import requests
import re
import urllib.parse
import json

app = FastAPI()

# -------------------------------
# 공통: 메뉴 텍스트 파싱
# -------------------------------
def parse_menu_to_dict(menu_info: Optional[str]) -> List[Dict[str, str]]:
    if not menu_info:
        return []

    items = [item.strip() for item in menu_info.split("|") if item.strip()]
    menu_list = []
    for item in items:
        match = re.search(r"(.+?)\s*(\d{1,3}(?:,\d{3})*원?)$", item)
        if match:
            name = match.group(1).strip()
            price = match.group(2).strip()
        else:
            name = item
            price = ""
        menu_list.append({"name": name, "price": price})
    return menu_list

# -------------------------------
# 유틸: 문자열 인코딩 복원
# -------------------------------
def fix_encoding(s: str) -> str:
    try:
        return s.encode('latin1').decode('utf-8')
    except:
        return s

def clean_image_url(img_url: str) -> str:
    try:
        fixed = fix_encoding(img_url)
        parts = fixed.rsplit("/", 1)
        if len(parts) == 2:
            base, filename = parts
            encoded_filename = urllib.parse.quote(filename)
            return f"{base}/{encoded_filename}"
        return fixed
    except:
        return img_url


# -------------------------------
# SEARCH API
# -------------------------------
@app.get("/search")
def search_places(
    query: str = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...)
) -> Dict[str, dict]:
    coord = f"{longitude};{latitude}"
    url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord={coord}"

    headers = {
        "referer": "https://map.naver.com/",
        "user-agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {"error": "네이버 요청 실패", "status": res.status_code}

    try:
        raw_places = res.json()["result"]["place"]["list"]
        result = {}

        for place in raw_places:
            place_id = place.get("id")
            if not place_id:
                continue

            result[place_id] = {
                "index": place.get("index"),
                "id": place_id,
                "name": place.get("name"),
                "tel": place.get("tel"),
                "virtualTel": place.get("virtualTel"),
                "virtualTelDisplay": place.get("virtualTelDisplay"),
                "ppc": place.get("ppc"),
                "category": place.get("category"),
                "businessStatus": place.get("businessStatus"),
                "address": place.get("address"),
                "roadAddress": place.get("roadAddress"),
                "abbrAddress": place.get("abbrAddress"),
                "shortAddress": place.get("shortAddress"),
                "display": place.get("display"),
                "telDisplay": place.get("telDisplay"),
                "context": place.get("context"),
                "reviewCount": place.get("reviewCount"),
                "placeReviewCount": place.get("placeReviewCount"),
                "thumUrl": place.get("thumUrl"),
                "thumUrls": place.get("thumUrls"),
                "x": place.get("x"),
                "y": place.get("y"),
                "homePage": place.get("homePage"),
                "bizhourInfo": place.get("bizhourInfo"),
                "menuInfo": parse_menu_to_dict(place.get("menuInfo")),
                "hasNaverBooking": place.get("hasNaverBooking"),
                "naverBookingUrl": place.get("naverBookingUrl"),
                "hasBroadcastInfo": place.get("hasBroadcastInfo"),
                "broadcastInfo": place.get("broadcastInfo") if place.get("hasBroadcastInfo") else None,
                "distance": place.get("distance")
            }

        return result

    except KeyError as e:
        return {"error": "'list' 항목이 없습니다", "detail": str(e)}
    
# -------------------------------
# 메뉴 API (스크립트 기반)
# -------------------------------
@app.get("/menu")
def fetch_menu_from_script(business_id: str = Query(...)) -> List[Dict]:
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/menu/list"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/menu",
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return [{"error": f"Failed to fetch: {response.status_code}"}]

    raw_bytes = response.content
    pattern = rb'"Menu:%b_\d+"\s*:\s*\{.*?\}(?=,|\s*[\r\n]+\s*"|\s*\})' % business_id.encode()
    matches = re.findall(pattern, raw_bytes, re.DOTALL)

    menu_items = []

    for m in matches:
        try:
            text = m.decode("utf-8")
            text = text.encode().decode("unicode_escape")
            text = urllib.parse.unquote(text)

            key_value_match = re.match(r'"Menu:[^"]*"\s*:\s*(\{.*\})', text, re.DOTALL)
            if not key_value_match:
                continue

            raw_json = key_value_match.group(1)
            obj = json.loads(raw_json)

            menu_items.append({
                "name": fix_encoding(obj.get("name", "")),
                "price": obj.get("price", ""),
                "description": fix_encoding(obj.get("description", "")),
                "images": [clean_image_url(img) for img in obj.get("images", [])]
            })

        except Exception as e:
            continue

    return menu_items

# -------------------------------
# 리스트 API
# -------------------------------
@app.get("/list")
def get_place_list(
    query: str = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...)
):
    coord = f"{longitude};{latitude}"
    url = f"https://map.naver.com/p/api/search/allSearch?query={query}&type=all&searchCoord={coord}"

    headers = {
        "referer": "https://map.naver.com/",
        "user-agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {"error": "네이버 요청 실패", "status": res.status_code}

    try:
        raw_places = res.json()["result"]["place"]["list"]
        result = []

        for place in raw_places:
            result.append({
                "id": place.get("id"),
                "title": place.get("name"),
                "category": place.get("category"),
                "thumbnail": place.get("thumUrl"),
                "reviewCount": place.get("reviewCount"),
                "distance": place.get("distance")
            })

        return result

    except KeyError as e:
        return {"error": "list 항목이 없습니다", "detail": str(e)}
