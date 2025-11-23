from langchain.tools import tool
from typing import List, Dict, Tuple
from app.schemas.models import Position

@tool
def place_furniture(furniture_list: List[Dict], layout: dict, analyzed_layout: dict) -> List[Dict]:
    """
    가구를 최적 위치에 배치합니다.
    
    Args:
        furniture_list: 배치할 가구 목록 [{"type": "bed_queen", "room": "room1"}, ...]
        layout: 원본 도면 데이터
        analyzed_layout: 분석된 도면 데이터
    
    Returns:
        배치 결과 [{"id": "furniture-1", "type": "bed_queen", "position": {"x": 2, "y": 3}, ...}]
    """
    
    # 가구 크기 정의 (칸 단위)
    FURNITURE_SIZES = {
        "bed_single": (2, 4),
        "bed_double": (3, 4),
        "bed_queen": (4, 4),
        "sofa_1": (2, 2),
        "sofa_2": (3, 2),
        "sofa_3": (4, 2),
        "desk": (3, 2),
        "dining_table_2": (2, 2),
        "dining_table_4": (4, 3),
        "wardrobe": (3, 2),
        "dresser": (2, 1),
        "tv_stand": (3, 1),
        "fridge": (2, 2),
        "chair": (1, 1)
    }
    
    grid = layout["grid"]
    quantitative = analyzed_layout.get("quantitative", {})
    
    placements = []
    occupied_cells = set()
    
    for idx, furniture_item in enumerate(furniture_list):
        furniture_type = furniture_item["type"]
        room = furniture_item["room"]
        
        if furniture_type not in FURNITURE_SIZES:
            continue
        
        width, height = FURNITURE_SIZES[furniture_type]
        
        # 해당 공간의 셀 가져오기
        room_data = quantitative.get(room, {})
        room_cells = room_data.get("cells", [])
        
        if not room_cells:
            continue
        
        # 배치 가능한 위치 찾기
        best_position = find_best_position(
            grid, room_cells, occupied_cells, 
            width, height, furniture_type, room
        )
        
        if best_position:
            x, y = best_position
            
            # 점유 셀 표시
            for dy in range(height):
                for dx in range(width):
                    occupied_cells.add((x + dx, y + dy))
            
            reason = get_placement_reason(furniture_type, best_position, grid)
            
            placements.append({
                "id": f"furniture-{idx + 1}",
                "type": furniture_type,
                "position": {"x": x, "y": y},
                "rotation": 0,
                "room": room,
                "reason": reason
            })
    
    return placements

def find_best_position(
    grid: List[List[str]], 
    room_cells: List[Tuple[int, int]], 
    occupied: set,
    width: int, 
    height: int,
    furniture_type: str,
    room: str
) -> Tuple[int, int] | None:
    """최적 배치 위치 찾기"""
    
    candidates = []
    
    for x, y in room_cells:
        # 가구가 들어갈 수 있는지 체크
        if can_place(grid, x, y, width, height, room, occupied):
            # 점수 계산
            score = calculate_placement_score(
                grid, x, y, width, height, furniture_type
            )
            candidates.append((score, (x, y)))
    
    if not candidates:
        return None
    
    # 점수 높은 순 정렬
    candidates.sort(reverse=True)
    return candidates[0][1]

def can_place(
    grid: List[List[str]], 
    x: int, y: int, 
    width: int, height: int,
    room: str,
    occupied: set
) -> bool:
    """배치 가능 여부 확인"""
    
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid else 0
    
    # 범위 체크
    if x + width > grid_width or y + height > grid_height:
        return False
    
    # 셀 체크
    for dy in range(height):
        for dx in range(width):
            cx, cy = x + dx, y + dy
            
            # 이미 점유됨
            if (cx, cy) in occupied:
                return False
            
            cell = grid[cy][cx]
            
            # 해당 방이 아니거나 배치 불가 셀
            if cell != room and cell not in ["empty"]:
                return False
    
    return True

def calculate_placement_score(
    grid: List[List[str]], 
    x: int, y: int,
    width: int, height: int,
    furniture_type: str
) -> float:
    """배치 점수 계산"""
    
    score = 0.0
    
    # 창문 근처 가산점 (침대, 책상)
    if furniture_type in ["bed_queen", "bed_double", "bed_single", "desk"]:
        window_nearby = check_nearby_cells(grid, x, y, width, height, "window")
        score += window_nearby * 10
    
    # 벽면 배치 가산점
    wall_nearby = check_nearby_cells(grid, x, y, width, height, "wall")
    score += wall_nearby * 5
    
    return score

def check_nearby_cells(
    grid: List[List[str]], 
    x: int, y: int,
    width: int, height: int,
    target_type: str
) -> int:
    """주변 특정 타입 셀 개수"""
    
    count = 0
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid else 0
    
    # 상하좌우 체크
    for dy in range(height):
        # 좌측
        if x > 0 and grid[y + dy][x - 1] == target_type:
            count += 1
        # 우측
        if x + width < grid_width and grid[y + dy][x + width] == target_type:
            count += 1
    
    for dx in range(width):
        # 상단
        if y > 0 and grid[y - 1][x + dx] == target_type:
            count += 1
        # 하단
        if y + height < grid_height and grid[y + height][x + dx] == target_type:
            count += 1
    
    return count

def get_placement_reason(furniture_type: str, position: Tuple[int, int], grid: List[List[str]]) -> str:
    """배치 이유 생성"""
    
    reasons = {
        "bed_queen": "창가 배치",
        "bed_double": "창가 배치",
        "bed_single": "벽면 배치",
        "desk": "창문 근처",
        "sofa_2": "거실 중앙",
        "sofa_3": "거실 중앙",
        "dining_table_4": "부엌 중앙",
        "wardrobe": "벽면 배치",
        "tv_stand": "벽면 배치"
    }
    
    return reasons.get(furniture_type, "최적 위치")