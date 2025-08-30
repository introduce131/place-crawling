# test_menu_groups.py
from graphql.menu_graphql import fetch_menu_for_place
from graphql.menu_groups_graphql import fetch_menu_groups_for_place
import asyncio

# 테스트할 값
PLACE_ID = "11689995"
BOOKING_ID = "683284"
NAVERORDER_ID = "4380337"

async def main():
    menus = await fetch_menu_for_place(PLACE_ID, BOOKING_ID, NAVERORDER_ID)
    print(f"[RESULT] 메뉴 개수: {len(menus)}")
    
    print(menus)

if __name__ == "__main__":
    asyncio.run(main())
