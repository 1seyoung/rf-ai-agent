import httpx
from typing import List, Dict, Optional
from app.core.config import settings
from openai import OpenAI

class MCPClient:
    """MCP PostgreSQL 서버 클라이언트"""
    
    def __init__(self):
        self.mcp_url = settings.MCP_SERVER_URL
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def search_products(
        self, 
        query: str, 
        furniture_type: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Vector 검색으로 제품 찾기
        
        Args:
            query: 검색 쿼리 (예: "미니멀 bed_queen")
            furniture_type: 가구 타입
            limit: 결과 개수
        
        Returns:
            제품 목록
        """
        
        # 1. 쿼리 임베딩 생성
        query_embedding = self._generate_embedding(query)
        
        # 2. MCP 서버에 요청
        products = await self._query_mcp(
            embedding=query_embedding,
            furniture_type=furniture_type,
            limit=limit
        )
        
        return products
    
    def _generate_embedding(self, text: str) -> List[float]:
        """OpenAI 임베딩 생성"""
        
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding
    
    async def _query_mcp(
        self, 
        embedding: List[float],
        furniture_type: str,
        limit: int
    ) -> List[Dict]:
        """MCP 서버에 Vector 검색 요청"""
        
        # MCP 쿼리 형식
        mcp_query = {
            "action": "vector_search",
            "table": "furniture_products",
            "embedding": embedding,
            "filters": {
                "furniture_type": furniture_type
            },
            "limit": limit
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/query",
                    json=mcp_query,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("results", [])
                
        except Exception as e:
            print(f"MCP 쿼리 오류: {e}")
            return []