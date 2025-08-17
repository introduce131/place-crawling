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
    """pos 이후 처음 나오는 '['부터 대괄호 밸런스를 맞춰 완전한 JSON 배열 문자열을 리턴"""
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
    """
    1) "newBusinessHours(...)" 블록을 regex로 찾아 그 안의 배열을 먼저 시도
    2) 실패하면 전체에서 "businessHours": [ ... ] 후보들을 순회하며 WorkingHoursInfo 리스트를 찾음
    """
    # 1) newBusinessHours(...) 키를 느슨하게 매칭 (내부는 뭐가 와도 괜찮게)
    m = re.search(r'"newBusinessHours\([^)]*\)"\s*:\s*\[', html)
    if m:
        arr_str = _extract_array_after_pos(html, m.start())
        if arr_str:
            try:
                arr = json.loads(arr_str)  # -> NewBusinessHour[] (대개 1개)
                for obj in arr:
                    if isinstance(obj, dict) and isinstance(obj.get("businessHours"), list):
                        return obj["businessHours"]
            except Exception:
                pass

    # 2) fallback: 모든 "businessHours": [ 를 훑어서 WorkingHoursInfo[] 모양을 찾기
    for mm in re.finditer(r'"businessHours"\s*:\s*\[', html):
        arr_str = _extract_array_after_pos(html, mm.start())
        if not arr_str:
            continue
        try:
            arr = json.loads(arr_str)
        except Exception:
            continue
        # WorkingHoursInfo[] 형태인지 판별
        if (
            isinstance(arr, list) and arr and isinstance(arr[0], dict)
            and "day" in arr[0] and "businessHours" in arr[0]
        ):
            return arr

    return None

def fetch_business_hours(business_id: str):
    url = f"https://pcmap.place.naver.com/restaurant/{business_id}/home"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": url,
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    time.sleep(1)
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code != 200:
        return {"error": f"Failed to fetch page: {r.status_code}"}

    html = r.text

    bh_list = _find_business_hours_array(html)
    if not bh_list:
        return {"error": "businessHours not found"}

    # normalize
    results = []
    for info in bh_list:
        if not isinstance(info, dict):
            continue
        bh = info.get("businessHours") or {}
        # lastOrderTimes가 없을 수도 있음
        last_orders = []
        for lo in info.get("lastOrderTimes") or []:
            if isinstance(lo, dict) and "time" in lo:
                last_orders.append(lo["time"])

        results.append({
            "day": fix_encoding(info.get("day")),                 # "월"~"일" 또는 "매일"
            "start": bh.get("start"),
            "end": bh.get("end"),
            "lastOrder": last_orders
        })

    return results

# 사용 예시
if __name__ == "__main__":
    business_id = "1027471594"
    result = fetch_business_hours(business_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
