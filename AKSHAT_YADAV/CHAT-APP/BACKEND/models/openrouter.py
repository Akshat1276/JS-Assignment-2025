import os
import requests
import json

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter(model: str, messages: list):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",  # Optional: your site URL
        "X-Title": "LLM Chat App"  # Optional: your app name
    }
    data = {
        "model": model,
        "messages": messages
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        print(f"OpenRouter response status: {response.status_code}")
        print(f"OpenRouter response: {response.text}")
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        print(f"OpenRouter API Error: {e}")
        print(f"Request data: {json.dumps(data, indent=2)}")
        raise e