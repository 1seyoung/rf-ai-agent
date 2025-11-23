from langchain.tools import tool
from typing import Dict, List

@tool
def decide_furniture(layout: dict, analyzed_layout: dict, style: str) -> Dict[str, List[str]]:
    """
    방 크기와 스타일에 맞는 가구를 자동으로 결정합니다.
    
    Args:
        layout: 원본 도면 데이터
        analyzed_layout: 분석된 도면 데이터 (정량/정성)
        style: 스타일 (미니멀, 북유럽 등)
    
    Returns:
        공간별 가구 목록 {"room1": ["bed_queen", "desk"], ...}
    """
    
    quantitative = analyzed_layout.get("quantitative", {})
    furniture_by_room = {}
    
    for space_type, space_data in quantitative.items():
        if space_type in ["wall", "door", "window", "empty"]:
            continue
            
        area = space_data.get("area_sqm", 0)
        window_count = space_data.get("window_count", 0)
        
        furniture = []
        
        # 방 (room1, room2, room3)
        if space_type.startswith("room"):
            if area >= 10:
                # 넓은 방: 침대 + 책상 + 수납
                furniture = ["bed_queen", "desk", "wardrobe"]
            elif area >= 7:
                # 중간 방: 침대 + 책상
                furniture = ["bed_double", "desk"]
            elif area >= 5:
                # 작은 방: 침대만
                furniture = ["bed_single"]
            
            # 창문 많으면 거실로 활용
            if window_count >= 2 and area >= 8:
                furniture = ["sofa_2", "tv_stand"]
        
        # 부엌
        elif space_type == "kitchen":
            if area >= 6:
                furniture = ["dining_table_4", "fridge"]
            elif area >= 4:
                furniture = ["dining_table_2", "fridge"]
        
        # 화장실, 현관, 복도는 가구 배치 안 함
        elif space_type in ["bathroom", "entrance", "corridor"]:
            furniture = []
        
        if furniture:
            furniture_by_room[space_type] = furniture
    
    return furniture_by_room