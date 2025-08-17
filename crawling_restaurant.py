from playwright.sync_api import sync_playwright
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import re
import requests
import random
import pyshorteners
import os
import pytz

start_time = time.time()
s = pyshorteners.Shortener()
load_dotenv()

SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_API_KEY = os.getenv("SUPABASE_ANON_API_KEY")

# 로그 파일 경로 설정
log_file_path = 'crawling_logs.json'

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

database_url: str = SUPABASE_PROJECT_URL
database_key: str = SUPABASE_ANON_API_KEY
supabase: Client = create_client(database_url, database_key)

results = [] # 결과를 저장할 리스트

keywords = [
    #"강남구 개포동 술집", "강남구 논현동 술집", "강남구 삼성동 술집", "강남구 역삼동 술집", "강남구 신사동 술집",
    #"강남구 청담동 술집", "강남구 압구정동 술집", "강남구 일원동 술집", "강남구 도곡동 술집", "강남구 세곡동 술집",
    
    #"강남구 대치동 술집", "강남구 수서동 술집", "강동구 길동 술집", "강동구 명일동 술집", "강동구 상일동 술집",
    #"강동구 암사동 술집", "강동구 천호동 술집", "강동구 둔촌동 술집","강동구 성내동 술집", "강동구 강일동 술집",
    #"강북구 미아동 술집", "강북구 수유동 술집", "강북구 번동 술집", "강북구 인수동 술집", "강북구 우이동 술집",
    #"강북구 삼양동 술집", "강서구 가양동 술집", "강서구 등촌동 술집", "강서구 방화동 술집", "강서구 염창동 술집",
    #"강서구 마곡동 술집", "강서구 화곡동 술집", "강서구 우장산동 술집", "강서구 내발산동 술집", "관악구 봉천동 술집",
    #"관악구 신림동 술집", "관악구 조원동 술집", "관악구 서원동 술집", "관악구 미성동 술집", "광진구 광장동 술집",
    #"광진구 구의동 술집", "광진구 자양동 술집", "광진구 능동 술집", "광진구 화양동 술집", "광진구 중곡동 술집",
    #"구로구 구로동 술집", "구로구 개봉동 술집", "구로구 고척동 술집", "구로구 오류동 술집", "구로구 궁동 술집",
    # "구로구 천왕동 술집", "구로구 항동 술집", "노원구 상계동 술집", "노원구 하계동 술집", "노원구 월계동 술집",
    # "노원구 중계동 술집", "노원구 공릉동 술집", "도봉구 도봉동 술집", "도봉구 방학동 술집", "도봉구 쌍문동 술집",
    # "도봉구 창동 술집", "동대문구 용두동 술집", "동대문구 장안동 술집", "동대문구 제기동 술집", "동대문구 회기동 술집",
    # "동대문구 휘경동 술집", "동대문구 청량리동 술집", "동대문구 전농동 술집", "마포구 공덕동 술집", "마포구 망원동 술집",
    # "마포구 상수동 술집", "마포구 서교동 술집", "마포구 합정동 술집", "마포구 대흥동 술집", "마포구 성산동 술집",
    # "서대문구 홍은동 술집", "서대문구 충정로 술집", "서대문구 무악동 술집", "서대문구 남가좌동 술집", "서대문구 북가좌동 술집",
    # "서대문구 연희동 술집", "서초구 서초동 술집", "서초구 방배동 술집", "서초구 양재동 술집", "서초구 우면동 술집",
    # "서초구 내곡동 술집", "성동구 성수동1가 술집", "성동구 성수동2가 술집", "성동구 옥수동 술집", "성동구 금호동 술집",
    #"성동구 도선동 술집","성동구 행당동 술집", "성북구 길음동 술집", "성북구 돈암동 술집", "성북구 성북동 술집",
    #"성북구 정릉동 술집", "성북구 삼선동 술집", "성북구 안암동 술집",  "송파구 잠실동 술집", "송파구 문정동 술집",
    #"송파구 가락동 술집", "송파구 송파동 술집", "송파구 방이동 술집", "송파구 석촌동 술집", "송파구 오금동 술집",
    #"양천구 목동 술집", "양천구 신정동 술집", "양천구 신월동 술집", "영등포구 여의도동 술집", "영등포구 영등포동 술집",
    #"영등포구 당산동 술집", "영등포구 문래동 술집", "영등포구 대림동 술집", "영등포구 신길동 술집", "영등포구 양평동 술집",
    # "용산구 이태원동 술집", "용산구 후암동 술집", "용산구 한남동 술집", "용산구 효창동 술집", "용산구 원효로 술집",
    # "용산구 보광동 술집", "은평구 불광동 술집", "은평구 응암동 술집", "은평구 구산동 술집", "은평구 역촌동 술집",
    # "은평구 대조동 술집", "종로구 사직동 술집", "종로구 삼청동 술집", "종로구 이화동 술집", "종로구 청운효자동 술집",
    # "종로구 혜화동 술집", "중구 남대문로 술집", "중구 명동 술집", "중구 예관동 술집", "중구 을지로동 술집",
    # "중구 신당동 술집", "중구 황학동 술집", "중랑구 면목동 술집", "중랑구 상봉동 술집", "중랑구 묵동 술집",
    # "중랑구 망우동 술집", "중랑구 신내동 술집", "중랑구 중화동 술집",
    # "홍대 술집", "연남동 술집", "망원역 술집", "상수 술집", "합정역 술집", "성수 술집", "건대입구 술집", "이태원 술집",
    # "한남동 술집", "경리단길 술집", "익선동 술집", "을지로 술집", "삼청동 술집", "북촌 술집", "서촌 술집", "가로수길 술집",
    # "신사역 술집", "압구정 술집", "청담동 술집", "여의도 술집", "광화문 술집", "종로 술집", "시청 술집", "삼성역 술집",
    # "역삼역 술집", "강남역 술집", "선릉역 술집", "잠실역 술집", "문정역 술집", "구로디지털단지역 술집", "가산디지털단지역 술집", 
    # "명동 술집","동대문 술집", "코엑스 술집", "영등포 타임스퀘어 술집", "DDP 술집", "롯데월드타워 술집"
    "효창공원앞역 술집",
    "삼각지역 술집",
    "은평구 구산동 술집",
    "은평구 역촌동 술집",
    "은평구 대조동 술집",
    "종로구 사직동 술집",
    "종로구 삼청동 술집",
    "종로구 이화동 술집",
    "종로구 청운효자동 술집",
    "종로구 혜화동 술집",
    "중구 남대문로 술집",
    "중구 명동 술집",
    "중구 예관동 술집",
    "중랑구 면목동 술집",
    "중랑구 상봉동 술집",
    "중랑구 묵동 술집",
    "중랑구 망우동 술집",
    "중랑구 신내동 술집",
    "중랑구 중화동 술집",
    "홍대 술집",
    "연남동 술집",
    "망원역 술집",
    "상수 술집",
    "합정역 술집",
    "시청역 술집",
]

# 로그 데이터를 JSON 형식으로 저장하는 함수
def save_log_to_json(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        'timestamp': timestamp,
        'message': message
    }
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            logs = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_entry)
    
    # 로그 파일에 덮어쓰기
    with open(log_file_path, 'w', encoding='utf-8') as file:
        json.dump(logs, file, ensure_ascii=False, indent=4)


# 로그를 JSON으로 저장하는 함수 호출 예시
def log_message(message):
    print(message)  # 원래 print로 찍히는 메시지
    save_log_to_json(message)  # 해당 메시지를 JSON 파일로 기록

def direct_shorten(url: str, timeout: float = 5.0) -> str:
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={url}", timeout=timeout)
        if response.status_code == 200:
            return response.text
        else:
            print(f"[WARN] TinyURL 응답 오류: HTTP {response.status_code}")
            return url
    except Exception as e:
        print(f"[WARN] TinyURL 요청 실패: {e}")
        return ""
    
def create_url(keyword: str) -> str:
    return f'https://map.naver.com/p/search/{keyword}'

# 스크롤하는 함수
def scroll_down_search_frame(search_frame):
    scroll_container = search_frame.query_selector("#_pcmap_list_scroll_container")
    for _ in range(5):  
        search_frame.evaluate("(el) => el.scrollBy(0, el.scrollHeight)", scroll_container)
        time.sleep(1.2)

# 인코딩 함수
def fix_encoding(s: str) -> str:
    try:
        return s.encode('latin1').decode('utf-8')
    except:
        return s
    
# requests로 데이터 추가요청 함수
def fetch_data(business_id: str) -> dict:
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"
    session = requests.Session()

    max_retries = 3

    for attempt in range(max_retries):
        headers = {
            "authority": "pcmap.place.naver.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": f"https://pcmap.place.naver.com/restaurant/{business_id}/home",
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
        session.headers.update(headers)

        try:
            # 요청 전 랜덤 딜레이
            time.sleep(random.uniform(1.8, 3.5))

            response = session.get(url)
            if response.status_code != 200:
                print(f"Attempt {attempt+1}: HTTP {response.status_code} - 재시도 합니다.")
                log_message(f"Attempt {attempt+1}: HTTP {response.status_code} - 재시도 합니다.")
                time.sleep(2)
                continue

            pattern = re.compile(r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});", re.DOTALL)
            match = pattern.search(response.text)

            if not match:
                print(f"Attempt {attempt+1}: __APOLLO_STATE__ 데이터 없음 - 재시도 합니다.")
                log_message(f"Attempt {attempt+1}: __APOLLO_STATE__ 데이터 없음 - 재시도 합니다.")
                time.sleep(2)
                continue

            apollo_state = json.loads(match.group(1))

            place_data = apollo_state.get(f"PlaceDetailBase:{business_id}")
            if place_data:
                lat = float(place_data["coordinate"].get("y")) if place_data.get("coordinate") else None
                lng = float(place_data["coordinate"].get("x")) if place_data.get("coordinate") else None
                road_address = fix_encoding(place_data.get("roadAddress", ""))
                reviewTotal = place_data.get("visitorReviewsTotal", None)
                reviewScore = place_data.get("visitorReviewsScore", None)

                # 키워드 추출
                keyword_pattern = re.compile(r'"keywordList"\s*:\s*\[(.*?)\]', re.DOTALL)
                keyword_match = keyword_pattern.search(response.text)
                
                if keyword_match:
                    try:
                        keywords_raw = "[" + keyword_match.group(1) + "]"
                        keyword_list = json.loads(keywords_raw)
                        keyword_list = [fix_encoding(k) for k in keyword_list]
                    except json.JSONDecodeError:
                        keyword_list = []
                else:
                    keyword_list = []
                
                return {
                    "lat": lat,
                    "lng": lng,
                    "road_address": road_address,
                    "review_total": reviewTotal,
                    "review_score": reviewScore,
                    "keyword_list": keyword_list,
                }
            else:
                print(f"Attempt {attempt+1}: PlaceDetailBase 데이터 없음 - 재시도 합니다.")
                log_message(f"Attempt {attempt+1}: PlaceDetailBase 데이터 없음 - 재시도 합니다.")
                time.sleep(2)

        except Exception as e:
            print(f"Attempt {attempt+1}: 에러 발생 - {e}")
            log_message(f"Attempt {attempt+1}: 에러 발생 - {e}")
            time.sleep(2)

    return {"error": "최대 재시도 후에도 데이터를 가져오지 못했습니다."}


# 메인 작업
def process_tab():

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)

        for keyword in keywords:
            log_message(f"[INFO] {keyword}에 대해 크롤링 작업 시작")

            results = []
            keyword_results = []
            
            url = create_url(keyword)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_timeout(3000)  

            page.wait_for_selector("iframe#searchIframe")
            search_frame = None
            for frame in page.frames:
                if frame.name == "searchIframe":
                    search_frame = frame
                    break
            if not search_frame:
                search_frame = page.frames[1]

            last_item_count = 0

            log_message("[INFO] 스크롤을 시작합니다...")
            while True:
                list_items = search_frame.query_selector_all("li.UEzoS.rTjJo")
                current_item_count = len(list_items)

                if current_item_count > last_item_count:
                    last_item_count = current_item_count
                    log_message(f"[INFO] 현재 {current_item_count}개 항목 로드됨. 계속 스크롤.")
                else:
                    log_message("[INFO] 더 이상 새 항목이 로드되지 않음. 스크롤 중지.")
                    break

                scroll_down_search_frame(search_frame)
            
            log_message(f"[INFO] 총 {last_item_count}개의 항목을 스크롤하여 로드했습니다.")

            final_list_items = search_frame.query_selector_all("li.UEzoS.rTjJo")
            log_message(f"[INFO] 최종적으로 {len(final_list_items)}개의 항목을 처리합니다.")

            for i, listitem in enumerate(final_list_items):
                try:
                    if not listitem:
                        log_message(f"[!] {i+1}번째 항목을 찾을 수 없습니다 (DOM 변경 가능성). 다음 항목으로 건너뜁니다.")
                        continue

                    title_tag = listitem.query_selector(".CHC5F .bSoi3 .place_bluelink.N_KDL.CtW3e")
                    if not title_tag:
                        log_message(f"[!] {i+1}번째 항목의 클릭 요소(제목 링크)를 찾을 수 없습니다. 다음 항목으로 건너뜁니다.")
                        continue
                    
                    title_tag.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    title_tag.click()

                    page.wait_for_selector("iframe#entryIframe")

                    entry_frame = None
                    for frame in page.frames:
                        if frame.name == "entryIframe":
                            entry_frame = frame
                            break

                    if not entry_frame:
                        entry_frame = page.frames[-1]

                    # entryIframe 로딩 대기 (확실히 로드될 때까지 대기)
                    try:
                        entry_frame.wait_for_selector("body", timeout=5000)
                        entry_frame.wait_for_selector("[role='main']", timeout=5000)
                    except Exception as e:
                        print(f"[!] {i+1}번째 항목의 상세 페이지 iframe 로딩 실패 (프레임 detach 또는 타임아웃): {e}")
                        continue

                    # entryIframe의 URL을 가져와 고유 ID 추출
                    entry_url = entry_frame.url

                    # URL에서 고유 ID 추출 (예: 'https://map.naver.com/p/place/2094027000'에서 '2094027000'을 추출)
                    match = re.search(r"restaurant/(\d+).*?home", entry_url)
                    place_id = match.group(1) if match else "unknown"

                    # 페이지에서 필요한 정보 추출
                    main = entry_frame.query_selector("[role='main']")
                    if not main:
                        print(f"[!] {i+1}번째 항목의 상세 페이지에서 main 요소를 찾을 수 없습니다. 다음 항목으로 건너뜁니다.")
                        continue

                    img_urls = []
                    try:
                        image_sections = main.query_selector_all(".CB8aP > .uDR4i > .CEX4u")
                        if image_sections:
                            if len(image_sections) > 0:
                                img = image_sections[0].query_selector(".fNygA > a > img")
                                if img:
                                    img_urls.append(img.get_attribute("src"))
                            
                            # 나머지 이미지 4개
                            """
                            if len(image_sections) > 1:
                                divs_in_second_section = image_sections[1].query_selector_all(".hEm4D")
                                for div in divs_in_second_section:
                                    nests_in_div = div.query_selector_all(".CEX4u")
                                    for nest in nests_in_div:
                                        img = nest.query_selector(".fNygA > a > img")
                                        if img:
                                            img_urls.append(img.get_attribute("src"))
                            """
                    except Exception as e:
                        log_message(f"[!] {i+1}번째 항목의 이미지 추출 중 오류 발생: {e}")

                    # 상호명, 카테고리 추출
                    title = ""
                    category = ""
                    try:
                        title_div = main.query_selector("#_title > div")
                        if title_div:
                            title_element = title_div.query_selector(".GHAhO")
                            if title_element:
                                title = title_element.inner_text()
                            category_element = title_div.query_selector(".lnJFt")
                            if category_element:
                                category = category_element.inner_text()
                    except Exception as e:
                        log_message(f"[!] {i+1}번째 항목의 타이틀/카테고리 추출 중 오류 발생: {e}")

                    # 주소, 영업시간, 전화번호, 홈페이지 추출
                    address = ""
                    direct = ""
                    homepage = ""
                    weekdays_list = []  # 모든 요일 정보 저장할 리스트
                    phoneNum = ""
                    extra_info = {}

                    try:
                        place_section_content = main.query_selector(".place_section.no_margin > .place_section_content > .PIbes")
                        address_div = place_section_content.query_selector(".O8qbU.tQY7D > .vV_z_")
                        hours_div = place_section_content.query_selector(".O8qbU.pSavy > .vV_z_")
                        phone_div = place_section_content.query_selector(".O8qbU.nbXkr > .vV_z_")
                        homepage_div = place_section_content.query_selector(".O8qbU.yIPfO > .vV_z_")

                        if address_div is None:
                            print("주소 정보 없음")
                            address = ""
                            directions = ""
                        else:
                            # 주소정보(주소, 가까운 역) 추출
                            address_span = address_div.query_selector(".PkgBl > span.LDgIH")
                            address = address_span.inner_text() if address_span else ""

                            directions = address_div.query_selector(".nZapA")

                            if directions:
                                directions.scroll_into_view_if_needed()
                                # span 태그를 제외한 주소정보 텍스트만 가져오기
                                direct = directions.evaluate("""
                                    (el) => {
                                        let textContent = '';
                                        const children = el.childNodes;  // 모든 자식 노드

                                        children.forEach(child => {
                                            if (child.nodeType === 3) {  // 텍스트 노드
                                                textContent += child.nodeValue.trim();  // 텍스트를 합침
                                            }
                                        });

                                        return textContent + "m";
                                    }
                                """)
                            else:
                                direct = ""

                        
                        if hours_div is None:
                            print("영업시간 정보 없음")
                            hours = ""
                        else:
                            hours_button = hours_div.query_selector("a.gKP9i.RMgN0")  # 영업시간 <a> 태그
                            hours_button.scroll_into_view_if_needed()
                            hours_button.click()
                            time.sleep(0.5)
                            entry_frame.wait_for_selector(".w9QyJ")
                            # entryIframe에서 .w9QyJ 클래스를 가진 모든 요소를 가져오기
                            week_days_locator = entry_frame.locator(".w9QyJ")

                            try:
                                # .w9QyJ 요소들 가져오기
                                week_days_elements = week_days_locator.all()

                                # .vI8SM 클래스가 없는 .w9QyJ 요소만 필터링
                                valid_week_days_elements = [element for element in week_days_elements if "vI8SM" not in element.get_attribute('class')]

                                # 유효한 .w9QyJ 요소가 있다면 모든 요소를 처리
                                if valid_week_days_elements:

                                    # 각 요소를 반복하면서 처리
                                    for element in valid_week_days_elements:
                                        week_days_text = element.inner_text()  # 각 요소의 텍스트 가져오기
                                        week_days_text = week_days_text.replace('\xa0', ' ') # &nbsp를 일반공백으로 변경
                                        week_days_text = week_days_text.replace("접기", "") # '접기' 제거
                                        weekdays_list.append(week_days_text)

                                else:
                                    print("유효한 요소가 없습니다.")

                            except Exception as e:
                                log_message(f"[ERROR] 요소 로딩 중 오류 발생: {e}")

                            # 대표번호 정보 추출
                            if phone_div is None:
                                print("대표번호 정보 없음")
                                phoneNum = ""
                            else:
                                phone_span = phone_div.query_selector("span.xlx7Q")
                                phoneNum = phone_span.inner_text() if phone_span else ""

                            # 대표 홈페이지 정보 추출
                            if homepage_div is None:
                                print("대표 홈페이지 정보 없음")
                                homepage = ""
                            else:
                                homepage_a = homepage_div.query_selector("a.place_bluelink.CHmqa[role='button']")
                                homepage = homepage_a.inner_text() if homepage_a else ""

                            # 추가 데이터를 script에서 긁어옴
                            extra_info = fetch_data(place_id)


                    except Exception as e:
                        log_message(f"[!] {i+1}번째 항목의 정보 추출 중 오류 발생: {e}")

                    # restaurant에 일괄적으로 upsert할 list
                    results.append({
                        "place_id": place_id,
                        "place_name": title,
                        "category": category,
                        "address" : address,
                        "road_address": extra_info.get("road_address", ""),
                        "direction" : direct,
                        "latitude": extra_info.get("lat", None),
                        "longitude": extra_info.get("lng", None),
                        "thumbnail": direct_shorten(img_urls[0]),
                        "weekdays" : weekdays_list,
                        "homepage" : homepage,
                        "phone": phoneNum,
                        "create_dt" : datetime.now(pytz.timezone('Asia/Seoul')).isoformat(),
                        "updated_at" : datetime.now(pytz.timezone('Asia/Seoul')).isoformat(),
                        "review_score" : extra_info.get("review_score", 0),
                        "review_count" : extra_info.get("review_total", 0),
                    })

                    # place_keyword에 일괄적으로 upsert할 list
                    keyword_results.append({
                        "place_id": place_id,
                        "keywords": extra_info.get("keyword_list"),
                        "updated_at" : datetime.now(pytz.timezone('Asia/Seoul')).isoformat(),
                    })

                    page.go_back()
                    page.wait_for_timeout(2000)

                    page.wait_for_selector("iframe#searchIframe")
                    search_frame = None
                    for frame in page.frames:
                        if frame.name == "searchIframe":
                            search_frame = frame
                            break
                    if not search_frame:
                        search_frame = page.frames[1]  # fallback

                except Exception as e:
                    log_message(f"[!] {i+1}번째 항목 처리 중 치명적인 오류 발생: {e}")

            # 식당(restaurant)에 데이터를 일괄적으로 삽입
            if results:
                # 중복된 place_id 제거 (마지막 항목이 우선됨)
                unique_results = {r["place_id"]: r for r in results}
                deduped_results = list(unique_results.values())

                try:
                    # upsert 실행
                    response = supabase.table("restaurant").upsert(deduped_results, on_conflict=["place_id"]).execute()

                    if response.data:
                        log_message(f"{keyword} 데이터 삽입 성공")
                    else:
                        log_message(f"응답 데이터 없음")
                except Exception as e:
                    log_message(f"데이터 삽입 중 오류 발생 : {e}")

            # 키워드(place_keyword) 데이터를 일괄적으로 삽입
            if keyword_results:
                unique_keywords = {k["place_id"]: k for k in keyword_results}
                deduped_keywords = list(unique_keywords.values())

                try:
                    response = supabase.table("place_keyword").upsert(deduped_keywords, on_conflict=["place_id"]).execute()

                    if response.data:
                        log_message(f"{keyword} 키워드 데이터 삽입 성공")
                    else:
                        log_message(f"키워드 응답 데이터 없음")
                except Exception as e:
                    log_message(f"키워드 데이터 삽입 중 오류 발생 : {e}")

            page.close() # 현재 페이지(탭) 닫기

        browser.close() # 전체 삽입 완료되면 브라우저 창 닫기

if __name__ == "__main__":    
    process_tab()

    # 실행 시간 출력
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")        

    # JSON 파일로 저장
    """
    try:
        with open("result_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("[INFO] 결과가 result_data.json 파일에 저장되었습니다.")
    except Exception as e:
        print(f"[ERROR] 결과 저장 중 오류 발생: {e}")
    """
