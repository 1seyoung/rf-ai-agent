from fastapi import APIRouter, HTTPException
from app.schemas.models import GenerateRequest, GenerateResponse
from app.core.agent import run_agent
from app.services.layout_analyzer import analyze_layout

router = APIRouter()

@router.post("/generate-layout", response_model=GenerateResponse)
async def generate_layout(request: GenerateRequest):
    """
    사용자 입력을 기반으로 가구 배치 및 제품 추천
    """
    try:
        # 1. 도면 분석 (전처리)
        analyzed_layout = await analyze_layout(request.layout)
        
        # 2. Agent 실행
        result = await run_agent(
            style_input=request.style_input,
            layout=request.layout.model_dump(),
            analyzed_layout=analyzed_layout
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))