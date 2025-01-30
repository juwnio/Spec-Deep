import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any
import time
from ..config.settings import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL

class GroqService:
    def __init__(self):
        self.session = requests.Session()
        # Add retry strategy
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 104],
            allowed_methods=["POST"]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
    def analyze_image(self, base64_image: str, context: str) -> str:
        try:
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": context},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            raise Exception(f"Groq API error: {response.text}")
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection to Groq API failed. Please check your internet connection: {str(e)}")
        except requests.exceptions.Timeout:
            raise Exception("Request to Groq API timed out")
        except Exception as e:
            raise Exception(f"Unexpected error with Groq API: {str(e)}")
