import os
import sys
from dotenv import load_dotenv

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from system import AuraSystem

def test_aura_hf():
    print("--- Aura Hugging Face Integration Test ---")
    
    # 1. Check .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env_path):
        print(f"ERROR: .env not found at {env_path}")
        return

    # 2. Get instance
    try:
        aura = AuraSystem.get()
        print("AuraSystem instance created.")
        
        # 3. Test query
        test_query = "Salam, sən kimsən?"
        print(f"Testing query: {test_query}")
        
        # This will trigger the MCTS -> HF Generator flow
        response = aura.process_query(test_query)
        
        print("\n--- RESPONSE ---")
        print(response)
        print("----------------")
        
        if "HF_API_KEY" in response and "XƏTA" in response:
            print("\nRESULT: System is working but API key is missing. This is expected if the user hasn't filled .env yet.")
        elif "xəta" in response.lower() or "bağışlayın" in response.lower():
            print("\nRESULT: Verification FAILED with an error.")
        else:
            print("\nRESULT: Verification SUCCESSFUL (Natural Language Response received).")
            
    except Exception as e:
        print(f"Test crashed: {e}")

if __name__ == "__main__":
    test_aura_hf()
