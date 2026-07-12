import os
import re
import requests
import json

def main():
    print("=== Aura System: Dataset Integration Agent ===")
    
    url = "https://datasets-server.huggingface.co/rows?dataset=angrygiraffe%2Fclaude-opus-4.6-4.7-reasoning-8.7k&config=default&split=train&offset=0&length=100"
    print(f"Fetching dataset from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("Dataset downloaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to fetch dataset: {e}")
        return

    rows = data.get("rows", [])
    print(f"Retrieved {len(rows)} rows from Hugging Face server.")

    qa_pairs = []
    for idx, r in enumerate(rows):
        row_data = r.get("row", {})
        category = row_data.get("category", "general")
        messages = row_data.get("messages", [])
        
        user_content = ""
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "").strip()
            if role == "user":
                user_content = content
            elif role == "assistant" and user_content:
                # We have a QA pair
                qa_pairs.append({
                    "category": category,
                    "question": user_content,
                    "response": content
                })
                user_content = "" # Reset for next turn if multi-turn
                
    print(f"Parsed {len(qa_pairs)} high-quality QA reasoning pairs.")

    # 1. Update universal_knowledgebase_v1.txt (MCTS KB)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kb_path = os.path.join(base_dir, "universal_knowledgebase_v1.txt")
    
    kb_content = ""
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            kb_content = f.read()
            
    # Make it idempotent: find if Section 5 is already there and truncate
    section_marker = "════════════════════════════════════════════════════════════════\nBÖLMƏ 5: REASONING & CS TUTORING DATASET (HF CLAUDE-OPUS)"
    if section_marker in kb_content:
        print("Found existing Section 5 in Knowledge Base. Overwriting to prevent duplicates...")
        kb_content = kb_content.split(section_marker)[0].strip() + "\n\n"
    else:
        kb_content = kb_content.strip() + "\n\n"

    # Append new section
    new_kb_section = section_marker + "\n════════════════════════════════════════════════════════════════\n\n"
    for pair in qa_pairs:
        # Escape question and response cleanly for KB formatting
        cat = pair["category"].upper()
        q = pair["question"].strip()
        resp = pair["response"].strip()
        
        new_kb_section += f"[EN] Category: {cat}\nQuestion: {q}\nResponse: {resp}\n\n"
        
    with open(kb_path, "w", encoding="utf-8") as f:
        f.write(kb_content + new_kb_section)
    print(f"Knowledge Base updated at: {kb_path}")

    # NOTE: HF reasoning data is NOT written to C++ GPT dataset files.
    # The long English reasoning texts are too complex for the tiny 225K-param model
    # and corrupt its Azerbaijani Q&A learning. This data lives ONLY in the
    # MCTS Knowledge Base where Qwen-72B can use it properly.
    print("\nIntegration completed! Reasoning data added to MCTS Knowledge Base only.")
    print("C++ GPT dataset is kept clean for pure Azerbaijani Q&A training.")

if __name__ == "__main__":
    main()
