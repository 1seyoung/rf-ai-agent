from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.models import LayoutData
from app.core.config import settings
from typing import Dict, Any

async def analyze_layout(layout: LayoutData) -> Dict[str, Any]:
    """도면 정량/정성 분석"""
    
    # 1. 정량 데이터 추출
    quantitative = extract_quantitative_data(layout)
    
    # 2. LLM 정성 분석
    qualitative = await llm_analyze(layout, quantitative)
    
    return {
        "quantitative": quantitative,
        "qualitative": qualitative
    }

def extract_quantitative_data(layout: LayoutData) -> Dict[str, Any]:
    """정량 데이터 추출"""
    
    spaces_data = {}
    
    for space in layout.spaces:
        space_type = space.type
        
        # 창문 개수 계산
        window_count = 0
        door_count = 0
        
        for cell in space.cells:
            x, y = cell.x, cell.y
            cell_type = layout.grid[y][x]
            
            if cell_type == "window":
                window_count += 1
            elif cell_type == "door":
                door_count += 1
        
        spaces_data[space_type] = {
            "area_sqm": space.areaSqM,
            "cell_count": space.cellCount,
            "window_count": window_count,
            "door_count": door_count,
            "cells": [(c.x, c.y) for c in space.cells]
        }
    
    return spaces_data

async def llm_analyze(layout: LayoutData, quantitative: Dict) -> str:
    """LLM 정성 분석"""
    
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    )
    
    prompt = ChatPromptTemplate.from_template("""
도면 정보를 분석하여 각 공간의 특징과 가구 추천 이유를 설명하세요.

정량 데이터:
{quantitative_data}

분석 항목:
1. 각 방의 크기 평가 (넓음/보통/좁음)
2. 채광 상태 (창문 개수 기반)
3. 적합한 용도 (침실/거실/서재 등)
4. 추천 가구 및 이유

200자 이내로 간결하게:
""")
    
    import json
    chain = prompt | llm
    result = await chain.ainvoke({
        "quantitative_data": json.dumps(quantitative, ensure_ascii=False, indent=2)
    })
    
    return result.content