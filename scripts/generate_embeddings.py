"""
가구 제품 임베딩 생성 및 업데이트 스크립트
"""
import os
import asyncpg
from openai import OpenAI
from typing import List
import asyncio

# OpenAI 클라이언트
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text: str) -> List[float]:
    """텍스트 임베딩 생성"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

async def update_embeddings():
    """모든 제품의 임베딩 생성 및 업데이트"""
    
    # DB 연결
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    )
    
    try:
        # 모든 제품 가져오기
        products = await conn.fetch("""
            SELECT id, name, category, furniture_type, description, features
            FROM furniture_products
            WHERE embedding IS NULL
        """)
        
        print(f"Processing {len(products)} products...")
        
        for product in products:
            # 임베딩 텍스트 생성
            features_str = ", ".join(product['features']) if product['features'] else ""
            embedding_text = f"{product['furniture_type']} {product['name']} {product['description']} {features_str}"
            
            # 임베딩 생성
            embedding = generate_embedding(embedding_text)
            
            # DB 업데이트
            await conn.execute("""
                UPDATE furniture_products
                SET embedding = $1
                WHERE id = $2
            """, embedding, product['id'])
            
            print(f"✓ {product['name']}")
        
        print(f"\n완료! {len(products)}개 제품 임베딩 생성")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(update_embeddings())