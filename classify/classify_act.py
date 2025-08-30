import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일에서 환경 변수 로드
load_dotenv()

SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_API_KEY)

# 1. 분류 그룹 정의
group_keywords = {
    "쇼핑": [
        "쇼핑센터,할인매장", "백화점", "시장", "아울렛", "종합패션"
    ],
    "문화,예술": [
        "문화,예술회관", "복합문화공간", "문화센터", "공연,연극시설", "영화관",
        "공연장", "전시관", "미술관", "갤러리카페", "갤러리,화랑", "박물관"
    ],
    "도서,교육": [
        "아동도서", "서점", "전문도서관", "군구립도서관", "어린이도서관",
        "독립서점", "도서관"
    ],
    "공방": [
        "향수공방", "뜨개", "재봉틀,미싱", "공방", "도자기",
    ],
    "체험": [
        "체험,홍보관", "관람,체험", "체험여행", "아쿠아리움", "과학관"
    ],
    "카페,이색카페": [
        "사주카페", "운세,사주", "힐링카페", "고양이카페", "동물카페",
        "애견카페", "슬라임카페", "룸카페", "보드카페"
    ],
    "스포츠,오락": [
        "롤러,인라인스케이트장", "아이스링크", "스케이트장", "볼링장",
        "스크린야구장", "서바이벌게임", "사격장", "당구장", "수영장",
        "스포츠,오락", "오락시설"
    ],
    "게임, 멀티미디어": [
        "방탈출카페", "플레이스테이션방", "DVD방", "PC방", "멀티방",
        "게임", "오락실", "노래방", "만화방"
    ],
    "방탈출카페": [
        "방탈출카페"
    ],
    "사진,스튜디오": [
        "셀프,대여스튜디오", "프로필사진전문", "사진,스튜디오"
    ],
    "대여,서비스": [
        "임대,대여", "한복대여", "장소대여", "옷수선"
    ],
    "자연,휴양": [
        "근린공원", "천문대", "동물원"
    ],
    "여행,관광": [
        "드라이브", "유람선,관광선"
    ],
    "어린이,가족": [
        "유아,아동용품", "키즈카페,실내놀이터"
    ],
    "테마파크, 워터파크": [
        "테마파크", "워터파크"
    ],
}

# 2. restaurant 테이블에서 카테고리 가져오기
response = supabase.table("distinct_activity_categories").select("category").execute()

# 3. category_groups 테이블에 데이터 삽입
if response.data is None:
    print(f"Error: {response.error}")
else:
    restaurant_categories = response.data

for cat_record in restaurant_categories:
    cat = cat_record["category"].strip()  # 공백 제거

    # 카테고리 그룹화
    matched_groups = []  # 이미 매칭된 그룹들을 저장할 리스트

    for group, keywords in group_keywords.items():
        for keyword in keywords:
            # 정규 표현식으로 단어 경계에 맞게 매칭
            if re.search(r'\b' + re.escape(keyword) + r'\b', cat):
                # 해당 카테고리-그룹 조합이 이미 존재하는지 확인
                existing = supabase.table("category_groups").select("id").eq("category", cat).eq("category_group", group).execute()

                if not existing.data:  # 해당 카테고리-그룹 조합이 없으면 삽입
                    supabase.table("category_groups").upsert({
                        "category": cat,
                        "category_group": group,
                        "category_type": "leisure"
                    }).execute()
                    
                    print(f"Inserted {cat} into {group} group.")  # 삽입된 정보 확인
                
                matched_groups.append(group)  # 매칭된 그룹 추가
                break  # 해당 키워드로 매칭되었으면 더 이상 다른 키워드로 확인하지 않음

    if not matched_groups:  # 아무 그룹에도 매칭되지 않으면 "기타" 그룹에 삽입
        supabase.table("category_groups").upsert({
            "category": cat,
            "category_group": "기타",
            "category_type": "leisure"
        }).execute()

print("카테고리 그룹화 작업 완료!")
