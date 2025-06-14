from fastapi import FastAPI, Query
from typing import Dict, List, Optional
import requests
import re
from playwright.sync_api import sync_playwright

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
# IMAGE API
# -------------------------------
@app.get("/image")
def image_menu(place_id: str = Query(...)):
    url = f"https://map.naver.com/p/entry/place/{place_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url)
        page.wait_for_timeout(1000)

        page.wait_for_selector("iframe#entryIframe", timeout=5000)
        entry_frame = page.frame(name="entryIframe") or page.frames[1]

        # 메뉴 탭 진입
        try:
            menu_btn = entry_frame.wait_for_selector(
                "//a[span[contains(@class, 'veBoZ') and contains(text(), '메뉴')]]",
                timeout=2000
            )
            menu_btn.click()
        except:
            pass

        # 더보기 반복 클릭
        prev_count = -1
        while True:
            try:
                current_menu_items = entry_frame.query_selector_all("li.E2jtL")
                current_count = len(current_menu_items)

                more_btn = entry_frame.query_selector(
                    "//a[contains(@class, 'fvwqf')][.//span[contains(@class, 'TeItc') and contains(text(), '더보기')]]"
                )

                if more_btn and more_btn.is_visible():
                    if current_count == prev_count:
                        break
                    more_btn.click()
                    entry_frame.wait_for_timeout(5)
                    prev_count = current_count
                else:
                    break
            except:
                break

        # 메뉴 항목 이미지
        menus = []
        try:
            entry_frame.wait_for_selector("li.E2jtL", timeout=3000)
            for menu in entry_frame.query_selector_all("li.E2jtL"):
                try:
                    name = menu.query_selector("a.xPf1B .lPzHi")
                    desc = menu.query_selector("a.xPf1B .kPogF")
                    price = menu.query_selector("a.xPf1B .GXS1X em")
                    img = menu.query_selector("a.xPf1B .place_thumb img")

                    menus.append({
                        "name": name.inner_text().strip() if name else "",
                        "desc": desc.inner_text().strip() if desc else "",
                        "price": price.inner_text().strip() if price else "",
                        "image": img.get_attribute("src") if img else ""
                    })
                except:
                    continue
        except:
            pass

        # 메뉴판 이미지
        menu_board_images = []
        try:
            entry_frame.wait_for_selector("li.sQTXy", timeout=3000)
            for li in entry_frame.query_selector_all("li.sQTXy"):
                try:
                    img = li.query_selector("div.WKvXd a.place_thumb[role='button'] img.K0PDV")
                    if img:
                        src = img.get_attribute("src")
                        if src:
                            menu_board_images.append(src)
                except:
                    continue
        except:
            pass

    return {
        "menus": menus,
        "menuBoardImages": menu_board_images
    }
