import random
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
import time
import json

# 환경 변수 로드
load_dotenv()
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

today_str = datetime.now().strftime("%Y-%m-%d")

# 재귀적으로 categoryId 뽑아내기
def extract_category_ids(category):
    ids = []
    if category.get("categoryId"):
        ids.append(category["categoryId"])
    if category.get("children"):
        for child in category["children"]:
            ids.extend(extract_category_ids(child))
    return ids

# 1. place_id, booking_id, naverorder_id 가져오기 (테스트용 단일 ID)
def get_booking_id():
    place_id = "18800388"  # 테스트할 place_id
    response = supabase.table("restaurant")\
        .select("place_id, booking_id, naverorder_id")\
        .eq("place_id", place_id)\
        .execute()
    return response.data or []

# 2. GraphQL 호출로 카테고리 가져오기
def fetch_categories_graphql(place_id: str, booking_id: str, naverorder_id: str, slot_id: str):
    url = "https://m.booking.naver.com/graphql?opName=categories"

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
        "operationName": "categories",
        "variables": {
            "input": {
                "lang": "ko",
                "businessId": booking_id,
                "bizItemId": naverorder_id,
                "isValidPopularOption": False,
                "slotId": slot_id
            }
        },
        "query": """query categories($input: MenuParams) {
            categories(input: $input) {
                id
                categoryId
                businessId
                agencyKey
                name
                depth
                order
                selectionTypeCode
                categoryTypeCode
                categoryJson
                isImp
                impOrder
                promotionType
                children {
                    id
                    agencyKey
                    brandId
                    categoryId
                    categoryTypeCode
                    categoryJson
                    deletedDateTime
                    depth
                    editedDateTime
                    editorId
                    isDeleted
                    name
                    order
                    parentCategoryId
                    regDateTime
                    selectionTypeCode
                    promotionType
                    __typename
                }
                __typename
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
            category_list = data.get("data", {}).get("categories", [])
            
            # flatten categoryId만 뽑기
            all_ids = []
            for c in category_list:
                all_ids.extend(extract_category_ids(c))

            print(f"categoryIds:{all_ids}")

            return all_ids
    except Exception as e:
        print(f"⚠️ GraphQL 호출 실패: {e}")
        return []

# 3. 메인 함수
# def main():
#     restaurants = get_booking_id()
#     if not restaurants:
#         print("✅ restaurant 테이블에 처리할 데이터 없음")
#         return

#     print(f"🔍 총 {len(restaurants)}개 restaurant에서 카테고리 수집 시작")

#     all_categories = []

#     for i, r in enumerate(restaurants, start=1):
#         place_id = r["place_id"]
#         booking_id = r["booking_id"]
#         naverorder_id = r["naverorder_id"]

#         print(f"[{i}/{len(restaurants)}] place_id: {place_id} 카테고리 수집 시작")
#         categories = fetch_categories_graphql(place_id, booking_id, naverorder_id)

#         if categories:
#             all_categories.extend(categories)
#             print(f"[{i}/{len(restaurants)}] place_id: {place_id} 카테고리 수집 완료 ({len(categories)}개)")
#         else:
#             print(f"[{i}/{len(restaurants)}] place_id: {place_id} 카테고리 없음 또는 요청 실패")

#         time.sleep(random.uniform(1.5, 3.0))

#     # 4. JSON 파일로 저장
#     with open("categories.json", "w", encoding="utf-8") as f:
#         json.dump(all_categories, f, ensure_ascii=False, indent=2)
#     print("✅ categories.json 파일 생성 완료")

# if __name__ == "__main__":
#     main()

