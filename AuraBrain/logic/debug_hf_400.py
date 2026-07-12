import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def debug_hf_router():
    api_key = os.getenv("HF_API_KEY")
    model = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    api_url = "https://router.huggingface.co/v1/chat/completions"
    # model = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3") # Original model definition
    # api_url = "https://router.huggingface.co/v1/chat/completions" # Original API URL definition
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    model = "meta-llama/Llama-3.1-8B-Instruct"
    api_url = "https://router.huggingface.co/v1/chat/completions"
    
    print(f"\n--- Testing Llama 3.1 on Router ---")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Salam, sən kimsən?"}],
        "max_tokens": 100
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    debug_hf_router()
