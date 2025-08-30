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
    "카페, 디저트": [
        "카페", "디저트", "베이커리", "도넛", "케이크", "빙수", "브런치", "와플", "차",
        "베이글", "아이스크림", "과일", "블루보틀", "북카페", "갤러리카페", "바나프레소",
        "테이크아웃커피", "토스트", "호두과자", "한방카페", "브런치카페", "케이크전문",
        "라이브카페", "떡카페", "홍차전문점", "초콜릿전문점", "찐빵", "고양이카페", "플라워카페",
        "크레페", "커피번", "테마카페", "스터디카페"
    ],
    "한식": [
        "한식", "백반", "가정식", "보리밥", "찌개", "전골", "순대", "감자탕", "냉면",
        "국밥", "갈비탕", "곰탕", "설렁탕", "한정식", "닭볶음탕", "닭발", "닭갈비", 
        "쌈밥", "육류", "보쌈", "족발", "김밥", "사철", "영양탕", "기사식당", 
        "정육식당", "막국수", "죽", "해장국", "향토음식", "신의주부대찌개", "국수",
        "두부요리", "라면", "마실", "만두", "칼국수,만두", "바른생갈비", "백숙,삼계탕",
        "비빔밥", "생선구이", "샤브샤브", "찜닭", "추어탕", "해담채", "한식뷔페",
    ],
    "중식": [
        "중식", "마라탕", "딤섬", "중식만두", "중식당", "양꼬치"
    ],
    "일식": [
        "일식", "초밥", "롤", "일본식라면", "이자카야", "우동", 
        "소바", "덮밥", "일식당", "일식튀김", "일식,초밥뷔페", "카레",
    ],
    "양식": [
        "양식", "스파게티", "파스타", "이탈리아", "프랑스", "스테이크", 
        "립", "피자", "그리스", "스페인", "패밀리레스토랑", "돈가스",
        "독일음식", "이탈리아음식", "그리스음식", "스페인음식", "프랑스음식"
    ],
    "고기": [
        "강화통통생고기", "고기뷔페", "곱창,막창,양", "돼지고기구이", "소고기구이",
        "육류", "보쌈", "족발", "정육식당", "양갈비", "오리요리", "양꼬치",
    ],
    "분식": [
        "떡볶이", "분식", "오뎅", "꼬치", "전", "빈대떡", "종합분식",
    ],
    "치킨": [
        "치킨", "닭강정", "닭장수후라이드", "닭요리", "일도씨닭갈비",
    ],
    "패스트푸드": [
        "햄버거", "핫도그", "샌드위치", "피자", "서오릉피자"
    ],
    "다이어트식": [
        "샐러드", "다이어트", "채식"
    ],
    "아시아음식": [
        "베트남", "태국", "아시아", "인도", "터키", "카레", "터키음식", "인도음식",
        "아시아음식", "베트남음식", "태국음식", 
    ],
    "세계음식": [
        "멕시코,남미음식", "이북음식",
    ],
    "해산물": [
        "게요리", "굴요리", "낙지요리", "대게나라", "대게요리", "바닷가재요리",
        "복어요리", "생선구이", "생선회", "오징어요리", "장어,먹장어요리", "조개요리",
        "주꾸미요리", "킹크랩요리", "해물,생선요리", "해산물뷔페", "해우리", "전복요리",
    ],
    "간편식": [
        "도시락,컵밥", "도시락", "컵밥", "밀키트"
    ],
    "찜,탕": [
        "매운탕,해물탕", "아귀찜,해물찜", "찜닭"
    ],
    "주류, 요리주점": [
        "맥주,호프", "바(BAR)", "술집", "와인", "요리주점", "전통,민속주점", "단란주점"
        "강남맥주", 
    ],
}

# 2. restaurant 테이블에서 카테고리 가져오기
response = supabase.table("distinct_restaurant_categories").select("category").execute()

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
                        "category_type": "food"
                    }).execute()
                    
                    print(f"Inserted {cat} into {group} group.")  # 삽입된 정보 확인
                
                matched_groups.append(group)  # 매칭된 그룹 추가
                break  # 해당 키워드로 매칭되었으면 더 이상 다른 키워드로 확인하지 않음

    if not matched_groups:  # 아무 그룹에도 매칭되지 않으면 "기타" 그룹에 삽입
        supabase.table("category_groups").upsert({
            "category": cat,
            "category_group": "기타",
            "category_type": "food"
        }).execute()

print("카테고리 그룹화 작업 완료!")
