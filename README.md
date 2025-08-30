# Place Crawling API Documentation

## 1. 식당 상세 조회

**Endpoint:** `GET /restaurant/{place_id}`
**설명:** Supabase에서 `place_id` 기준으로 식당 상세 정보를 가져옵니다.

| 파라미터   | 타입   | 설명                |
| ---------- | ------ | ------------------- |
| `place_id` | string | 조회할 식당 고유 ID |

**Response 예시:**

```json
{
  "restaurant": {
    "place_id": "1278436155",
    "name": "다목당",
    "address": "서울 강남구 남부순환로 2733 2층",
    "phone": "02-123-4567"
    ...
    ...
  },
  "menu": [
    {
      "menu_id": "1278436155_0",
      "place_id": "1278436155",
      "menu_name": "메로구이",
      "menu_price": 29000,
      "description": "A+급 최고급 메로 목살, 몸통살 부위의 메로구이",
      "image_url": "https://ldb-phinf.pstatic.net/20210422_228/.......jpg"
    }
  ],
  "booking_menu": [
    {
      "menu_id": "1516959879_0",
      "place_id": "1278436155",
      "menu_name": "피넛 애플 베이글",
      "menu_price": 7500,
      "description": "베이글 택1, 무가당 땅콩버터, 그릭요거트, 사과",
      "image_url": "https://naverbooking-phinf.pstatic.net/......jpg"
    }
  ],
  "menu_board": [
    {
      "image_url": "http://..."
    }
  ],
  "keywords": ["한식", "점심", "가성비"]
}
```

**Error 예시:**

```json
{ "error": "해당 place_id가 존재하지 않습니다." }
```

---

## 2. 식당 영업시간 조회 (네이버 플레이스 기준)

**Endpoint:** `GET /restaurant/{business_id}/hours`
**설명:** 네이버 플레이스의 `business_id` 기준으로 영업시간을 크롤링해서 반환합니다.

| 파라미터      | 타입   | 설명                         |
| ------------- | ------ | ---------------------------- |
| `business_id` | string | 네이버 플레이스 가게 고유 ID |

**Response 예시:**

```json
[
  {
    "day": "매일",
    "start": "11:00",
    "end": "22:00",
    "lastOrder": ["21:30"]
  },
  {
    "day": "월",
    "start": "11:00",
    "end": "22:00",
    "lastOrder": ["21:30"]
  }
]
```

---

## 3. 주변 식당 검색

**Endpoint:** `GET /restaurants`
**설명:** 사용자의 위도/경도 기준으로 Supabase RPC(`get_restaurants`) 호출하여 주변 식당 목록 조회.

| 파라미터         | 타입              | 설명                              |
| ---------------- | ----------------- | --------------------------------- |
| `lat`            | float             | 사용자 위도                       |
| `lng`            | float             | 사용자 경도                       |
| `category_group` | string (Optional) | 대분류 카테고리, 없으면 전체 조회 |
| `radius`         | int               | 반경(m), 기본값 5000              |

**Response 예시:**

```json
[
  {
    "place_id": "1883597886",
    "name": "홍길동 식당",
    "distance": 320,
    "category": "한식"
  },
  {
    "place_id": "1883597887",
    "name": "김철수 카페",
    "distance": 420,
    "category": "카페"
  }
]
```

**Error 예시:**

```json
{ "error": "Supabase RPC 호출 실패" }
```

---

## 4. 메뉴 조회 (실제 구현 미완)

**Endpoint:** `GET /menu`
**설명:** `business_id` 기반으로 메뉴 데이터를 가져오는 API (현재 구현 없음).

| 파라미터      | 타입   | 설명                         |
| ------------- | ------ | ---------------------------- |
| `business_id` | string | 네이버 플레이스 가게 고유 ID |

**Response 예시:**

```json
[]
```
