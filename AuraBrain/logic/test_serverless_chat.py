import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HF_API_KEY")

def test_serverless_chat(model_id):
    print(f"Testing Serverless Chat API for: {model_id}")
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
            print(f"Response: {resp.json()['choices'][0]['message']['content']}")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

models = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct"
]

for m in models:
    if test_serverless_chat(m):
        print(f"--- SUCCESS with {m} ---")
        break
    print("-" * 30)
