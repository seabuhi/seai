import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HF_API_KEY")
model_id = "mistralai/Mistral-7B-Instruct-v0.3"
url = f"https://api-inference.huggingface.co/models/{model_id}/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": model_id,
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 10
}

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Success! Response: {resp.json()['choices'][0]['message']['content']}")
    else:
        print(f"Failed. Error: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
