from langchain.tools import tool
from typing import List, Dict
from app.services.mcp_client import MCPClient

@tool
async def search_products(style: str, furniture_types: List[str]) -> Dict[str, List[Dict]]:
    """
    MCP를 통해 스타일에 맞는 실제 제품을 검색합니다.
    
    Args:
        style: 스타일 (미니멀, 북유럽 등)
        furniture_types: 검색할 가구 타입 목록 ["bed_queen", "desk", ...]
    
    Returns:
        가구별 제품 목록 {"furniture-1": [products], "furniture-2": [products]}
    """
    
    mcp_client = MCPClient()
    results = {}
    
    for idx, furniture_type in enumerate(furniture_types):
        furniture_id = f"furniture-{idx + 1}"
        
        # MCP 쿼리 생성
        query = f"{style} {furniture_type}"
        
        # MCP 서버에 검색 요청
        products = await mcp_client.search_products(
            query=query,
            furniture_type=furniture_type,
            limit=3
        )
        
        results[furniture_id] = products
    
    return results
