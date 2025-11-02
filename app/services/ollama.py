import requests
import json
from typing import Dict, Any, Optional
from app.common.config import settings
from app.common.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Ollama API client for AI analysis"""

    def __init__(self):
        self.base_url = settings.ollama.base_url
        self.model = settings.ollama.model
        self.timeout = settings.ollama.timeout

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make request to Ollama API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            return None

    def analyze_confusion_patterns(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze user confusion patterns using Ollama"""

        prompt = f"""
        너는 학습 피드백 전문가야. 주어진 학습 결과 데이터를 분석해서,
        사용자가 이해하기 쉽도록 간단하고 직관적인 문장으로 피드백을 작성해줘.
        이모지는 사용하지 않고, 문장만으로 친근하고 부드러운 톤을 유지할 것.

        다음은 한국어 발음 학습자의 답변 데이터입니다:

        사용자 정보:
        - 총 문제 수: {user_data.get('total_questions', 0)}
        - 정답률: {user_data.get('accuracy', 0):.1%}

        혼동 패턴:
        {json.dumps(user_data.get('confusion_patterns', {}), ensure_ascii=False, indent=2)}

        음성학적 혼동:
        {json.dumps(user_data.get('phonetic_confusions', {}), ensure_ascii=False, indent=2)}

        이 데이터를 분석하여 다음 형식으로 결과를 제공해주세요:

        {{
            "summary": "오늘은 [총 문제 수]문제 중 [맞힌 문제 수]개를 맞추셨어요.",
            "strengths": ["특히 잘한 부분을 한두 문장으로"],
            "weaknesses": ["어려웠던 부분을 한두 문장으로"],
            "recommendations": ["앞으로 어떻게 연습하면 좋은지 구체적인 행동 제안"]
        }}

        피드백에는 다음 요소를 포함해줘:
        1) 강점: 특히 잘한 부분을 한두 문장으로
        2) 약점: 어려웠던 부분을 한두 문장으로
        3) 추천 학습 방향: 앞으로 어떻게 연습하면 좋은지 구체적인 행동 제안

        답변은 반드시 JSON 형식으로만 제공하고, 한국어로 작성해주세요.
        """

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        logger.info(f"Requesting confusion pattern analysis for user data")
        response = self._make_request("/api/generate", data)

        if response and "response" in response:
            try:
                analysis_result = json.loads(response["response"])
                logger.info("Successfully analyzed confusion patterns")
                return analysis_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response as JSON: {e}")
                return None

        return None

    def analyze_learning_progress(self, progress_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze learning progress over time"""

        prompt = f"""
        다음은 학습자의 시간별 진도 데이터입니다:

        {json.dumps(progress_data, ensure_ascii=False, indent=2)}

        이 데이터를 분석하여 학습 진도와 개선사항을 다음 형식으로 제공해주세요:

        {{
            "progress_summary": "전반적인 진도 요약",
            "improvement_areas": ["개선된 영역 1", "개선된 영역 2"],
            "stagnant_areas": ["정체된 영역 1", "정체된 영역 2"],
            "next_steps": ["다음 단계 1", "다음 단계 2"],
            "estimated_proficiency": "초급/중급/고급"
        }}

        답변은 반드시 JSON 형식으로만 제공하고, 한국어로 작성해주세요.
        """

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        logger.info("Requesting learning progress analysis")
        response = self._make_request("/api/generate", data)

        if response and "response" in response:
            try:
                analysis_result = json.loads(response["response"])
                logger.info("Successfully analyzed learning progress")
                return analysis_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response as JSON: {e}")
                return None

        return None

    def generate_personalized_recommendations(self, user_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate personalized learning recommendations"""

        prompt = f"""
        다음은 학습자의 종합 프로필입니다:

        {json.dumps(user_profile, ensure_ascii=False, indent=2)}

        이 정보를 바탕으로 개인화된 학습 권장사항을 다음 형식으로 제공해주세요:

        {{
            "priority_skills": ["우선 학습 기술 1", "우선 학습 기술 2"],
            "practice_exercises": [
                {{
                    "type": "연습 유형",
                    "description": "연습 설명",
                    "frequency": "권장 빈도"
                }}
            ],
            "difficulty_adjustment": "쉽게/유지/어렵게",
            "motivational_message": "격려 메시지"
        }}

        답변은 반드시 JSON 형식으로만 제공하고, 한국어로 작성해주세요.
        """

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        logger.info("Requesting personalized recommendations")
        response = self._make_request("/api/generate", data)

        if response and "response" in response:
            try:
                analysis_result = json.loads(response["response"])
                logger.info("Successfully generated personalized recommendations")
                return analysis_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response as JSON: {e}")
                return None

        return None

    def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


# Global Ollama client instance
ollama_client = OllamaClient()