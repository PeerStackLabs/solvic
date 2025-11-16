"""
Google Gemini LLM provider integration.

Requires:
- GEMINI_API_KEY environment variable
- model name in config (e.g., gemini-2.5-flash-preview-05-20)

Get your API key: https://aistudio.google.com/apikey

Gemini has a generous free tier:
- 1,500 requests per day
- 1M tokens per minute
Perfect for personal/freelancer use!
"""

import os
import json
import requests
from typing import List, Dict, Any

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini implementation of LLMProvider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Get API key from environment
        gemini_config = config.get("gemini", {})
        api_key_env = gemini_config.get("api_key_env", "GEMINI_API_KEY")
        self.api_key = os.getenv(api_key_env)

        if not self.api_key:
            raise ValueError(
                f"Gemini API key not found in environment variable: {api_key_env}"
            )

        # Get model name
        self.model = gemini_config.get(
            "model", "gemini-2.5-flash-preview-05-20"
        )

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def extract_tasks(self, transcript_text: str) -> List[Dict[str, Any]]:
        """Extract tasks from transcript using Gemini"""

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        prompt = self.get_extraction_prompt(transcript_text)

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(
                url, json=payload, headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return []

            result = response.json()
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]

            # Extract JSON from response (remove markdown code blocks if present)
            generated_text = generated_text.strip()
            if generated_text.startswith("```"):
                lines = generated_text.split("\n")
                generated_text = "\n".join(lines[1:-1])  # Remove first and last line
            generated_text = (
                generated_text.replace("```json", "").replace("```", "").strip()
            )

            # Parse JSON
            try:
                tasks = json.loads(generated_text)
                return tasks
            except json.JSONDecodeError as e:
                print(f"Failed to parse Gemini response as JSON: {e}")
                print(f"Response was: {generated_text}")
                return []

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return []

    def test_connection(self) -> bool:
        """Test if Gemini API is accessible"""

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        test_payload = {
            "contents": [{"parts": [{"text": "Say OK if you can hear me"}]}]
        }

        try:
            response = requests.post(
                url, json=test_payload, headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200

        except Exception as e:
            print(f"Gemini connection test failed: {e}")
            return False
