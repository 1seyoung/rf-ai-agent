from pydantic import BaseModel
from typing import List, Dict, Optional, Literal

# 위치 모델
class Position(BaseModel):
    x: int
    y: int

# 도면 메타 정보
class LayoutMeta(BaseModel):
    gridSize: int
    cellSizeCm: int
    totalSizeCm: int
    totalSizeM: float
    entranceDirection: str
    orientation: Dict[str, str]

# 공간 정보
class SpaceInfo(BaseModel):
    type: Literal["room1", "room2", "room3", "kitchen", "bathroom", "entrance", "corridor"]
    typeName: str
    cellCount: int
    areaSqM: float
    cells: List[Position]

# 도면 데이터
class LayoutData(BaseModel):
    meta: LayoutMeta
    grid: List[List[Literal["empty", "room1", "room2", "room3", "kitchen", "bathroom", "entrance", "corridor", "wall", "door", "window"]]]
    spaces: List[SpaceInfo]
    stats: Optional[Dict[str, int]] = None

# 요청
class GenerateRequest(BaseModel):
    style_input: str  # 사용자 입력 (자유 형식)
    layout: LayoutData

# 가구 배치
class FurniturePlacement(BaseModel):
    id: str  # furniture-1, furniture-2...
    type: Literal["bed_single", "bed_double", "bed_queen", "sofa_1", "sofa_2", "sofa_3", 
                  "desk", "dining_table_2", "dining_table_4", "wardrobe", "dresser", 
                  "tv_stand", "fridge", "chair"]
    position: Position
    rotation: Literal[0, 90, 180, 270]
    room: str
    reason: str

# 제품 추천
class ProductRecommendation(BaseModel):
    id: int  # DB id
    name: str
    category: str
    furniture_type: str
    price: int
    brand: str
    width_cm: int
    height_cm: int
    depth_cm: int
    image_url: str
    description: str
    features: List[str]
    similarity: Optional[float] = None

# 응답
class GenerateResponse(BaseModel):
    message: str
    furniture_placements: List[FurniturePlacement]
    recommended_products: Dict[str, List[ProductRecommendation]]  # furniture_id를 키로 사용: "furniture-1": [products]