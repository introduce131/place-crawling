from fastapi import FastAPI, Query
from typing import Dict, List, Optional
import requests
import re

app = FastAPI()

# 🍽 메뉴 파싱 함수
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

# 🔍 search API
@app.get("/search")
def search_places(
    query: str = Query(..., description="검색 키워드"),
    latitude: float = Query(..., description="위도"),
    longitude: float = Query(..., description="경도")
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
