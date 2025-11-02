# Wowlingo AI - 일일 학습 피드백 시스템

아동 발음 학습자의 학습 데이터를 분석하여 매일 개인화된 피드백을 제공하는 AI 기반 시스템

## 주요 기능

- 🎯 **일일 학습 피드백**: 매일 학습 12시간 후 자동으로 피드백 생성
- 👶 **아동 친화적**: 7세 이하 아동이 이해할 수 있는 쉬운 표현
- 🌱 **성장 추적**: 스테이지 진행도 기반 성장 단계 (씨앗→새싹→성장한 식물→열매)
- 📊 **카테고리별 분석**: hashtag 기반 가장 잘한 영역 파악
- 🤖 **AI 기반**: Ollama + Gemma 모델을 활용한 다양한 피드백 생성

## 기술 스택

- **Backend**: FastAPI, Python 3.11, SQLAlchemy
- **Database**: MySQL (실제 Wowlingo DB 연결)
- **AI Engine**: Ollama + Gemma 모델
- **Scheduler**: APScheduler (선택사항)

## 프로젝트 구조

```
wowlingo-ai/
├── app/
│   ├── common/              # 공통 모듈 (config, database, logging)
│   ├── core/                # 핵심 로직 (scheduler)
│   ├── models/              # 데이터베이스 모델
│   │   └── wowlingo_models.py  # 실제 Wowlingo DB 스키마
│   ├── routers/             # API 엔드포인트
│   │   └── feedback.py      # 피드백 API
│   ├── services/            # 외부 서비스
│   │   ├── feedback.py      # 피드백 생성 로직
│   │   └── ollama.py        # Ollama 클라이언트
│   └── main.py              # FastAPI 애플리케이션
├── config/
│   ├── config.yaml          # 메인 설정
│   └── prompts.yaml         # AI 프롬프트 템플릿
├── .env                     # 환경 변수 (DB 접속 정보)
├── .env.example             # 환경 변수 템플릿
└── requirements.txt         # Python 의존성
```

## 설치 및 실행

### 1. 사전 요구사항

- Python 3.11+
- MySQL (Wowlingo 데이터베이스)
- Ollama + Gemma 모델

### 2. 프로젝트 설정

```bash
# 저장소 클론
git clone <repository-url>
cd wowlingo-ai

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 예시:**
```env
DATABASE_HOST=your-mysql-host
DATABASE_PORT=3306
DATABASE_NAME=wowlingo
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password
```

### 4. Ollama 설정

```bash
# Ollama 설치 (https://ollama.ai/)
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Gemma 모델 다운로드
ollama pull gemma

# Ollama 서버 시작 (백그라운드)
ollama serve
```

### 5. 애플리케이션 실행

```bash
# 개발 모드
python app/main.py

# 또는 uvicorn 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

애플리케이션이 `http://localhost:8000`에서 실행됩니다.

## API 사용법

### API 문서
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 API 엔드포인트

#### 1. 일일 피드백 생성

```bash
POST /api/feedback/generate
Content-Type: application/json

{
  "user_id": 1,
  "target_date": "2025-01-15"  # 선택사항, 없으면 오늘
}
```

**응답 예시:**
```json
{
  "summary": "오늘 퀴즈 15개 중 12개 맞혔어요!",
  "praise": "귀가 밝아지고 있어요 ☀️",
  "motivation": "새싹으로 자라날 준비 중이에요 🌿",
  "ai_feedback_id": 123
}
```

#### 2. 최신 피드백 조회

```bash
GET /api/feedback/user/{user_id}/latest
```

#### 3. 특정 날짜 피드백 조회

```bash
GET /api/feedback/user/{user_id}/date/2025-01-15
```

## 피드백 규격

### 학습 요약 (summary)
다음 3가지 중 랜덤으로 선택:
1. **정답률 기반**: "오늘 단어 듣기 퀴즈에서 75% 성공했어요"
2. **베스트 카테고리**: "환경음 퀴즈에서 정확히 구별했어요!"
3. **퀘스트 다양성**: "여러 종류 문제를 풀어서 멋진 하루였어요!"

### 칭찬 (praise)
정답률에 따라:
- **85% 이상**: 매우 긍정적 "귀가 세상의 모든 소리를 찾아내고 있어요 🌈"
- **70-84%**: 긍정적 "오늘의 귀가 한층 밝아졌어요 ☀️"
- **70% 미만**: 격려 "조금 어려웠죠? 하지만 씨앗은 물을 조금씩 먹고 자라요 🌱"

### 동기부여 (motivation)
성장 단계(스테이지)별:
- **씨앗** (스테이지 1): "물방울을 모아서 새싹을 키워볼까요? 🌱"
- **새싹** (스테이지 2-4): "새싹이 쑥쑥 자라고 있어요! 💧"
- **성장한 식물** (스테이지 5-7): "식물이 튼튼하게 자라고 있어요 🌿"
- **열매** (스테이지 8+): "맛있는 열매가 열릴 거예요 🍎"

**모든 문장: 공백 포함 25자 이내, 7세 아동 눈높이**

### 성장 단계 계산 방식
- `user_quest_progress` 테이블에서 `done_yn=0` (미완료) 중 `Quest.order`가 가장 작은 스테이지를 현재 진행 중인 스테이지로 판단
- 각 스테이지는 70문제, 50개 이상 맞추면 다음 스테이지로 진행
- 스테이지 순서에 따라 성장 단계 자동 매핑

## 데이터베이스 스키마

주요 테이블 (schema.sql 참조):
- `user`: 사용자 정보
- `quests`: 문제집 (order 컬럼으로 스테이지 순서 관리)
- `quest_items`: 개별 문제
- `quest_item_units`: 문제 유닛 (음성 파일)
- `user_quests`: 사용자 퀘스트 수행 기록 (정답률, 시간)
- `user_quest_items`: 사용자 문제 답변 기록
- `user_quest_progress`: **스테이지별 진행도** (전체 문제 수, 정답 개수, 완료 여부)
- `hashtags`: 카테고리 (환경음, 말소리, 의문문, 평서문 등)
- `quest_hashtags`: 퀘스트-해시태그 매핑
- `user_quest_attempts`: 학습 시도 날짜 이력
- `ai_feedbacks`: AI 피드백 저장 (message 컬럼에 `\n` 구분자로 summary, praise, motivation 저장)

## 설정 파일

### config/config.yaml
```yaml
database:
  # .env 파일에서 환경 변수로 덮어씌워짐
  host: localhost
  port: 3306

ollama:
  base_url: http://localhost:11434
  model: gemma
  timeout: 30
```

### config/prompts.yaml
AI 프롬프트 템플릿을 관리합니다. 코드 수정 없이 프롬프트만 변경하여 피드백 스타일 조정 가능.

## 실행 예시

### cURL로 피드백 생성
```bash
curl -X POST "http://localhost:8000/api/feedback/generate" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "target_date": "2025-01-15"}'
```

### Python으로 피드백 생성
```python
import requests

response = requests.post(
    "http://localhost:8000/api/feedback/generate",
    json={"user_id": 1, "target_date": "2025-01-15"}
)

feedback = response.json()
print(f"학습 요약: {feedback['summary']}")
print(f"칭찬: {feedback['praise']}")
print(f"동기부여: {feedback['motivation']}")
```

## 트러블슈팅

### 1. Ollama 연결 실패
```bash
# Ollama 서비스 상태 확인
ollama list

# 모델 다운로드 확인
ollama pull gemma

# 서버 재시작
killall ollama
ollama serve
```

### 2. 데이터베이스 연결 오류
```bash
# MySQL 서비스 상태 확인
mysql -h localhost -u your-username -p

# .env 파일의 접속 정보 확인
cat .env
```

### 3. 피드백이 25자 초과
- `config/prompts.yaml`의 시스템 프롬프트 조정
- 더 강조된 제한 문구 추가

### 4. 학습 데이터가 없는 경우
```json
{
  "detail": "No learning data found for user 1 on 2025-01-15"
}
```
→ 해당 날짜에 `user_quests` 데이터가 있는지 확인

## 개발 가이드

### 프롬프트 수정
`config/prompts.yaml` 파일을 편집하면 코드 수정 없이 피드백 스타일 변경 가능.

### 새로운 API 추가
1. `app/routers/` 에 라우터 파일 생성
2. `app/main.py`에 라우터 등록
3. `app/services/`에 비즈니스 로직 추가

### 로그 확인
```bash
# 애플리케이션 로그 (설정 필요시)
tail -f logs/app.log
```

## 향후 개선 사항

- [ ] **learning_progress_analysis**: 시간에 따른 학습 진도 분석 (데이터 충분 ✅)
- [ ] **personalized_recommendations**: 개인화된 학습 추천 (제한적 데이터 ⚠️)
- [ ] **자동 스케줄링**: 학습 12시간 후 자동 피드백 생성
- [ ] **다국어 지원**: 영어/일본어 피드백

## 라이센스

MIT License

## 지원

문제가 발생하면 GitHub Issues에 보고해 주세요.
