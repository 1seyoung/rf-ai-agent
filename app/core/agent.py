from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
from app.services.tools import get_tools
import json
import re

async def analyze_intent(style_input: str, layout: dict) -> dict:
    """사용자 의도 분석 (Agent의 뇌)"""
    
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    )
    
    intent_prompt = ChatPromptTemplate.from_template("""
사용자 입력과 도면을 분석하여 의도를 파악하세요.

사용자 입력: {style_input}
도면 정보: {layout}

분석 항목:
1. 스타일: 언급된 무드/스타일 (미니멀, 북유럽 등)
2. 지정 가구: 명시적으로 요청한 가구 목록
3. 공간별 배치: 특정 공간에 특정 가구 배치 지시
4. 자동 결정 필요: 사용자가 가구를 지정 안 했는지
5. 제품 추천 필요: 실제 제품 검색이 필요한지

JSON 형식으로만 응답:
{{
    "style": "추출된 스타일",
    "specified_furniture": {{"room1": ["bed"], "room2": []}},
    "auto_decide_needed": true/false,
    "product_search_needed": true/false,
    "reasoning": "판단 근거"
}}
""")
    
    chain = intent_prompt | llm | StrOutputParser()
    result = await chain.ainvoke({
        "style_input": style_input,
        "layout": json.dumps(layout, ensure_ascii=False)
    })
    
    # JSON 추출
    if '```json' in result:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
    
    return json.loads(result)

def create_agent() -> AgentExecutor:
    """LangChain Agent 생성"""
    
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    )
    
    tools = get_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 RoomFlow 인테리어 AI 어시스턴트입니다.

**=== 의도 분석 결과 (JSON Schema) ===**
{intent_analysis}

Required fields:
- style: string (추출된 스타일/무드)
- specified_furniture: object (공간별 지정 가구)
- auto_decide_needed: boolean (가구 자동 결정 필요 여부)
- product_search_needed: boolean (제품 검색 필요 여부)

**=== Tools 사용 규칙 ===**
1. decide_furniture
   - 호출 조건: auto_decide_needed === true
   - tool_input: {{"layout": object, "style": string}}
   - 출력: {{"room_id": ["furniture_type", ...]}}

2. place_furniture
   - 호출 조건: 항상 (배치 필요시)
   - tool_input: {{"furniture_list": array, "layout": object}}
   - 출력: [{{"id": string, "type": string, "position": {{"x": int, "y": int}}, "rotation": int, "room": string, "reason": string}}]

3. search_products
   - 호출 조건: product_search_needed === true
   - tool_input: {{"style": string, "furniture_types": array}}
   - 출력: {{"furniture-1": [product objects]}}

**중요: 모든 tool_input은 반드시 유효한 JSON 형식이어야 함**

**=== 도면(Grid) 데이터 해석 ===**
- 좌표: (x, y) = (가로, 세로), 좌상단이 (0, 0)
- 1칸 = 50cm
- 현관: 항상 남쪽(하단) 위치

셀 타입:
- "empty": 빈 공간
- "wall": 벽 (배치 불가)
- "window": 창문 (배치 불가, 채광 고려)
- "door": 문 (배치 불가, 동선 고려)
- "room1/2/3": 거실/침실
- "kitchen": 부엌
- "bathroom": 화장실
- "entrance": 현관

배치 제약:
- wall/window/door 위치 배치 금지
- 가구 간 겹침 금지
- 동선 최소 1칸(50cm) 확보
- 침대: 창문 근처 우선
- 책상: 창문 또는 벽면

**=== Few-shot 예시 ===**

예시 1: 완전 자동 배치
입력: "미니멀하게 꾸며줘"
의도: {{"auto_decide_needed": true, "product_search_needed": true}}
Tool 순서:
1. decide_furniture({{"layout": ..., "style": "미니멀"}})
2. place_furniture({{"furniture_list": [...], "layout": ...}})
3. search_products({{"style": "미니멀", "furniture_types": ["bed_queen", "desk"]}})

예시 2: 부분 지정 배치
입력: "방1에 침대, 방2에 소파 배치해줘"
의도: {{"specified_furniture": {{"room1": ["bed"], "room2": ["sofa"]}}, "auto_decide_needed": false}}
Tool 순서:
1. place_furniture({{"furniture_list": [{{"type": "bed_queen", "room": "room1"}}, {{"type": "sofa_2", "room": "room2"}}], "layout": ...}})
2. search_products({{"style": "일반", "furniture_types": ["bed_queen", "sofa_2"]}})

예시 3: 제품 추천만
입력: "북유럽 스타일 침대 추천해줘"
의도: {{"product_search_needed": true, "placement_needed": false}}
Tool 순서:
1. search_products({{"style": "북유럽", "furniture_types": ["bed_queen"]}})

예시 4: 배치 불가 예외
입력: "화장실에 침대 배치해줘"
의도: {{"placement_impossible": true}}
응답: "죄송합니다. 화장실은 고정 용도 공간으로 가구 배치가 불가합니다."

**=== 최종 응답 형식 (엄격 준수) ===**
출력 형식: {{"message": "..."}}

제약 조건:
1. 전체 글자 수: 80~150자
2. 문장 수: 2~3개
3. 허구의 제품명/가격 생성 금지
4. Tool 결과만 활용
5. 과도한 설명 금지

좋은 예:
"침대를 창가에, 책상을 벽면에 배치했어요. 미니멀 스타일 제품 3개를 추천드립니다."

나쁜 예 (금지):
"안녕하세요! 사용자님의 요청에 따라 미니멀한 스타일로 방을 꾸며드렸습니다. 먼저 퀸 침대를 북쪽 창가에 배치하여 자연 채광을 최대한 활용할 수 있도록 했고, 책상은 동쪽 벽면에 배치하여 집중도를 높였습니다. 에이스침대 화이트오크(89만원), 한샘 원목책상(35만원), 이케아 MALM 서랍장(12.9만원)을 추천드립니다. 더 궁금한 점이 있으시면 언제든 문의해주세요!"

**응답 생성 시:**
- Tool 실행 완료 후 결과 확인
- message는 2~3문장, 80~150자로 제한
- 제품명은 Tool 반환값만 사용
- 배치 이유는 간단히 (예: "창가 배치")
"""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=10
    )
    
    return agent_executor

async def run_agent(style_input: str, layout: dict, analyzed_layout: dict) -> dict:
    """Agent 실행 - 의도 분석 후 Tool 선택"""
    
    # 1. 의도 분석 (Agent의 뇌)
    intent_analysis = await analyze_intent(style_input, layout)
    print(f"[Agent] 의도 분석: {intent_analysis}")
    print(f"[Agent] 도면 분석: {analyzed_layout}")
    
    # 2. Agent 실행
    agent_executor = create_agent()
    
    result = await agent_executor.ainvoke({
        "input": style_input,
        "intent_analysis": json.dumps(intent_analysis, ensure_ascii=False),
        "analyzed_layout": json.dumps(analyzed_layout, ensure_ascii=False)
    })
    
    # 3. 결과 포맷팅
    return format_agent_response(result, intent_analysis)

def format_agent_response(result: dict, intent_analysis: dict) -> dict:
    """Agent 응답을 GenerateResponse 형태로 변환"""
    
    intermediate_steps = result.get("intermediate_steps", [])
    
    furniture_placements = []
    recommended_products = {}
    
    # Tool 결과 추출
    for action, observation in intermediate_steps:
        tool_name = action.tool
        tool_input = action.tool_input
        
        if tool_name == "place_furniture":
            # 배치 결과 추출
            if isinstance(observation, list):
                furniture_placements.extend(observation)
        
        elif tool_name == "search_products":
            # 제품 검색 결과 추출
            if isinstance(observation, dict):
                recommended_products.update(observation)
    
    return {
        "message": result["output"],
        "furniture_placements": furniture_placements,
        "recommended_products": recommended_products
    }