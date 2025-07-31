import requests
import re
import json
import time

def fix_encoding(s: str) -> str:
    try:
        return s.encode('latin1').decode('utf-8')
    except:
        return s

def fetch_coordinates_and_keywords(business_id: str) -> dict:
    # 요청할 URL
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"

    # 요청 헤더 설정 (브라우저와 동일한 요청 헤더)
    headers = {
        "authority": "pcmap.place.naver.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/home",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive",  # 필요 없다면 삭제 가능
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
        time.sleep(1)

        # 페이지 소스 요청
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"Failed to fetch page: {response.status_code}"}

        # 페이지 소스에서 window.__APOLLO_STATE__ 추출
        pattern = re.compile(r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});", re.DOTALL)
        match = pattern.search(response.text)

        if not match:
            return {"error": "좌표, 키워드, 카테고리, 주소 정보를 찾을 수 없습니다."}

        # __APOLLO_STATE__에서 JSON 데이터 파싱
        apollo_state = json.loads(match.group(1))

        # PlaceDetailBase에서 해당 business_id의 데이터 추출
        place_data = apollo_state.get(f"PlaceDetailBase:{business_id}")
        if place_data:
            # 좌표 정보 추출
            lat = place_data["coordinate"].get("y") if place_data.get("coordinate") else None
            lng = place_data["coordinate"].get("x") if place_data.get("coordinate") else None
            
            # 카테고리, 주소, 도로명주소 추출
            category = fix_encoding(place_data.get("category", ""))
            address = fix_encoding(place_data.get("address", ""))
            road_address = fix_encoding(place_data.get("roadAddress", ""))
            
            return {
                "lat": lat,
                "lng": lng,
                "category": category,
                "address": address,
                "road_address": road_address
            }
    except Exception as e:
        print(f"Error info : {e}")
    return {}

# 사용 예시
business_id = "33408380"  # 예시 business_id
data = fetch_coordinates_and_keywords(business_id)
print(data)
