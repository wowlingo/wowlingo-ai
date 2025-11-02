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

    def analyze_learning_progress(self, progress_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze learning progress over time"""

        # Get prompt template from settings
        prompt_config = settings.prompts.learning_progress_analysis
        system_prompt = prompt_config.get('system_prompt', '')
        user_template = prompt_config.get('user_prompt_template', '')

        # Format user prompt with actual data
        prompt = system_prompt + "\n\n" + user_template.format(
            progress_data=json.dumps(progress_data, ensure_ascii=False, indent=2)
        )

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

        # Get prompt template from settings
        prompt_config = settings.prompts.personalized_recommendations
        system_prompt = prompt_config.get('system_prompt', '')
        user_template = prompt_config.get('user_prompt_template', '')

        # Format user prompt with actual data
        prompt = system_prompt + "\n\n" + user_template.format(
            user_profile=json.dumps(user_profile, ensure_ascii=False, indent=2)
        )

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