# rf-ai-agent

### todo

#### tool 1 : 입력 파싱

**agent가 해야하는 판단**
- 스타일 키워드 추출
- 가구 언급 여부
- 공간별 배치 지시 여부
- 자동 결정 필요 여부


#### tool 2 : 가구 결정

**agent가 해야하는 판단**
- 방 크기 기반 가구 선택
- 스타일 고려

#### tool 3 : 배치 계산 

**알고리즘 (Python 자체 구현)**
- 공간별 가구 할당
- 충돌 감지
- 동선 확보
- 창문/문 위치 고려


### 가구 데이터 설계

```sql
CREATE TABLE furniture_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    category VARCHAR(50),
    furniture_type VARCHAR(50),
    price INTEGER,
    brand VARCHAR(100),
    image_url TEXT,
    
    -- 크기 (배치용)
    width_cm INTEGER,
    height_cm INTEGER,
    depth_cm INTEGER,
    
    -- RAG/임베딩용
    description TEXT,
    features TEXT[],
    
    -- 임베딩
    embedding VECTOR(1536)
);
```


description 활용
- 임베딩 생성: `style + name + description + features`
- AI 추천 문구: description 기반으로 GPT가 생성

**예시:**
```
description: "편안한 좌석감의 북유럽 스타일 3인 소파. 
부드러운 패브릭 원단으로 장시간 앉아도 편안합니다."

features: ["친환경 소재", "분리 세척 가능", "10년 AS"]

→ AI 생성 문구:
"이 소파는 편안한 좌석감이 장점이고, 
친환경 소재에 세탁도 가능해서 관리가 쉬워요!"