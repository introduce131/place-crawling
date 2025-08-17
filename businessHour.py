import requests
import re
import json
import time

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
    """월~일 순서로 정렬, '매일'이 있으면 맨 앞"""
    weekday_order = ["월", "화", "수", "목", "금", "토", "일"]

    def get_index(item):
        day = item.get("day")
        if day == "매일":
            return -1  # 매일은 맨 앞
        try:
            return weekday_order.index(day)
        except ValueError:
            return 100  # 기타 값은 맨 뒤

    return sorted(bh_list, key=get_index)

def fetch_business_hours(business_id: str):
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": url,
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    time.sleep(1)
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

    # 요일 정렬
    results = sort_business_hours(results)
    return results

# 사용 예시
if __name__ == "__main__":
    business_id = "1883597886"
    result = fetch_business_hours(business_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
