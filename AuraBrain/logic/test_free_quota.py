import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HF_API_KEY")
url = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Testing smaller/cheaper models to see if any are free
models_to_test = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta"
]

for model in models_to_test:
    print(f"Testing model: {model}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("--- SUCCESS ---")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 30)
