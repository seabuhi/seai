import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HF_API_KEY")

# Testing the standard (Free) Inference API
def test_standard_api(model_id):
    print(f"Testing standard API for: {model_id}")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": "Salam, necəsən?",
        "parameters": {"max_new_tokens": 50}
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

models = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3-mini-4k-instruct"
]

for m in models:
    if test_standard_api(m):
        print(f"--- SUCCESS with {m} ---")
        break
    print("-" * 30)
