import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HF_API_KEY")
model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
url = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
}

print(f"Testing model: {model}")
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
