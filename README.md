# Wowlingo AI - 일일 학습 피드백 시스템

아동 발음 학습자의 학습 데이터를 분석하여 매일 개인화된 피드백을 제공하는 AI 기반 시스템

## 주요 기능

- 🎯 **자동 일일 피드백**: 매일 오후 10시(설정 가능) 자동으로 모든 사용자 피드백 생성
- 🕐 **스케줄러 내장**: APScheduler로 배치 작업 자동 실행
- 🌏 **타임존 지원**: Asia/Seoul 등 원하는 타임존 설정 가능
- 📊 **배치 처리**: 병렬 처리로 대량 사용자 효율적 처리
- 🤖 **AI 기반**: Ollama + Gemma 모델을 활용한 개인화 피드백
- 🔧 **Config 기반**: YAML 파일로 스케줄 관리

## 기술 스택

- **Backend**: FastAPI, Python 3.11, SQLAlchemy
- **Database**: PostgreSQL (실제 Wowlingo DB 연결)
- **AI Engine**: Ollama + Gemma 모델
- **Scheduler**: APScheduler (자동 실행)

## 프로젝트 구조

```
wowlingo-ai/
├── app/
│   ├── common/              # 공통 모듈 (config, database, logging)
│   ├── core/                # 핵심 로직
│   │   ├── scheduler.py    # 스케줄러 관리
│   │   └── feedback_generator.py  # 배치 피드백 생성
│   ├── models/              # 데이터베이스 모델
│   │   └── wowlingo_models.py  # 실제 Wowlingo DB 스키마
│   ├── routers/             # API 엔드포인트
│   │   ├── feedback.py      # 피드백 API
│   │   └── batch.py         # 배치 관리 API
│   ├── services/            # 외부 서비스
│   │   ├── feedback.py      # 개별 피드백 생성
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

### ⚠️ 중요: 스케줄러 자동 실행
**서버를 시작하면 스케줄러가 자동으로 실행됩니다.**
별도의 배치 프로세스를 실행할 필요가 없습니다.

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
# 개발 모드 (스케줄러 자동 시작)
python app/main.py

# 또는 uvicorn 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

애플리케이션이 `http://localhost:8000`에서 실행됩니다.

**🔄 스케줄러 자동 실행:**
- 서버 시작 시 스케줄러가 자동으로 백그라운드에서 실행
- 설정된 시간에 자동으로 배치 작업 수행
- 서버 종료 시 스케줄러도 함께 종료

## API 사용법

### API 문서
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 API 엔드포인트

#### 1. 수동 배치 실행 (테스트용)

```bash
POST /api/batch/trigger/daily_feedback
```

**응답 예시:**
```json
{
  "message": "Batch job daily_feedback completed successfully",
  "result": {
    "job_type": "daily_feedback",
    "date": "2025-01-27",
    "total_users": 150,
    "processed_count": 148,
    "error_count": 2
  }
}
```

#### 2. 스케줄러 상태 확인

```bash
GET /api/batch/scheduler/status
```

**응답 예시:**
```json
{
  "status": "running",
  "timezone": "Asia/Seoul",
  "jobs": [
    {
      "id": "daily_feedback",
      "name": "Daily AI Feedback Generation",
      "next_run": "2025-01-27T22:00:00+09:00",
      "trigger": "cron[hour='22', minute='0']"
    }
  ]
}
```

#### 3. 최근 생성된 피드백 조회

```bash
GET /api/batch/feedbacks/recent?limit=10
```

#### 4. 개별 사용자 피드백 생성 (기존 API)

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

#### 5. 최신 피드백 조회

```bash
GET /api/feedback/user/{user_id}/latest
```

#### 6. 특정 날짜 피드백 조회

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
  host: ${DATABASE_HOST}
  port: ${DATABASE_PORT}
  database: ${DATABASE_NAME}
  username: ${DATABASE_USERNAME}
  password: ${DATABASE_PASSWORD}

ollama:
  base_url: http://localhost:11434
  model: gemma
  timeout: 30

batch:
  # 기본 타임존 설정 (한국 시간)
  timezone: Asia/Seoul
  
  # 데일리 AI 피드백 생성 (매일 오후 10시)
  daily_feedback:
    enabled: true
    hour: 22
    minute: 0
  
  # 기존 분석 작업들 (필요시 활성화)
  daily_analysis:
    enabled: false
    hour: 0
    minute: 0
```

### 스케줄러 설정 변경

1. **시간 변경**: `config/config.yaml`의 `hour`, `minute` 수정
2. **타임존 변경**: `timezone` 값 변경 (예: `America/New_York`)
3. **잡 활성화/비활성화**: `enabled: true/false` 설정
4. **서버 재시작**: 변경사항 적용을 위해 서버 재시작 필요

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

## 배치 처리 및 스케줄링

### 자동 실행되는 작업

1. **일일 AI 피드백 생성** (daily_feedback)
   - 실행 시간: 매일 오후 10시 (설정 가능)
   - 대상: 당일 학습한 모든 사용자
   - 저장 위치: `ai_feedbacks` 테이블
   - 병렬 처리: 50명씩 배치 처리

### 배치 처리 특징

- **자동 재시도**: 실패한 사용자는 로그에 기록
- **병렬 처리**: `asyncio.gather()`로 성능 최적화
- **메모리 효율**: 청크 단위 처리 (기본 50명)
- **타임존 인식**: KST ↔ UTC 자동 변환

### 모니터링

```bash
# 서버 로그 확인
tail -f logs/app.log

# 스케줄러 상태 API
curl http://localhost:8000/api/batch/scheduler/status

# 최근 생성된 피드백 확인
curl http://localhost:8000/api/batch/feedbacks/recent
```

## 향후 개선 사항

- [x] **자동 스케줄링**: ✅ APScheduler로 구현 완료
- [x] **배치 처리**: ✅ 병렬 처리로 대량 사용자 지원
- [x] **Config 기반 설정**: ✅ YAML로 스케줄 관리
- [ ] **Redis 큐**: 대규모 확장 시 도입 검토
- [ ] **모니터링 대시보드**: Grafana 연동
- [ ] **알림 시스템**: Slack/이메일 연동

## 라이센스

MIT License

## 지원

문제가 발생하면 GitHub Issues에 보고해 주세요.
