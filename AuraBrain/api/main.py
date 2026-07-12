from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import subprocess

# Add the parent directory to sys.path to import search logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.search import SearchAgent
from logic.system import AuraSystem

app = FastAPI(title="Aura Bridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

search_agent = SearchAgent()

class ChatRequest(BaseModel):
    message: str

class SimpleTokenizer:
    def __init__(self):
        self.vocab = {}
        self.next_id = 1

    def tokenize(self, text: str):
        tokens = []
        for word in text.split():
            clean_word = "".join(c for c in word.lower() if c.isalnum())
            if not clean_word: continue
            if clean_word not in self.vocab:
                self.vocab[clean_word] = self.next_id
                self.next_id += 1
            tokens.append(self.vocab[clean_word])
        return tokens

tokenizer = SimpleTokenizer()

@app.post("/chat")
def chat_with_aura(request: ChatRequest):
    msg = request.message.strip()
    
    # 0. Pass the query directly to the Reasoning Engine
    try:
        response = AuraSystem.get().process_query(msg)
        return {"reply": response}
    except Exception as e:
        print(f"AuraSystem Error: {e}")
        return {"reply": "Sistemimdə (AuraSystem) müvəqqəti nasazlıq yarandı. Öyrənməyə davam edirəm."}

def process_distillation(tokens: list[int]):
    try:
        core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "AuraCore", "tensor.exe")
        cmd = [core_path, "--train"] + [str(t) for t in tokens]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, _ = process.communicate()
        if "Final Weights" in stdout:
            print(f"Distillation Complete: {stdout.strip().splitlines()[-1]}")
    except Exception as e:
        print(f"Distillation Error: {e}")

@app.get("/")
def read_root():
    return {"status": "Aura AI Bridge is Running"}

@app.get("/search")
def search_web(q: str):
    results = search_agent.search(q)
    return {"query": q, "results": results}

@app.post("/learn")
def start_learning(topic: str, background_tasks: BackgroundTasks):
    # This will be refined as we integrate the C++ core
    background_tasks.add_task(process_learning, topic)
    return {"message": f"Learning process started for: {topic}"}

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        # Tokenize the entire file
        print(f"Tokenizing dataset: {file.filename}")
        tokens = tokenizer.tokenize(text)
        print(f"Generated {len(tokens)} tokens from {file.filename}.")
        
        if background_tasks and tokens:
            # Send to background task to process in chunks
            background_tasks.add_task(process_batch_training, tokens)
            return {"message": f"Dataset {file.filename} accepted. {len(tokens)} tokens queued for training."}
        else:
            return {"message": "Failed to process dataset or empty file."}
            
    except Exception as e:
        return {"error": str(e)}

def process_batch_training(tokens: list[int], batch_size: int = 200):
    print(f"Starting batch training for {len(tokens)} tokens...")
    core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "AuraCore", "tensor.exe")
    
    # Process in chunks to avoid memory/command line length limits
    total_batches = (len(tokens) + batch_size - 1) // batch_size
    
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i:i + batch_size]
        try:
            cmd = [core_path, "--train"] + [str(t) for t in batch]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = process.communicate()
            current_batch = (i // batch_size) + 1
            print(f"Batch {current_batch}/{total_batches} Complete.")
        except Exception as e:
            print(f"Batch {current_batch} Error: {e}")
            break
    print("Dataset training loop finished.")

def process_learning(topic: str):
    print(f"Learning about {topic}...")
    results = search_agent.search(topic, max_results=3)
    
    all_tokens = []
    for r in results:
        content = search_agent.scrape_page(r['href'])
        if content:
            tokens = tokenizer.tokenize(content)
            all_tokens.extend(tokens[:50]) # Limit per source for mock
            print(f"Scraped & Tokenized {len(tokens)} tokens from {r['href']}")

    if not all_tokens:
        print("No training data found.")
        return

    # Trigger C++ Core for real training
    try:
        core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "AuraCore", "tensor.exe")
        cmd = [core_path, "--train"] + [str(t) for t in all_tokens[:100]] # Limit total tokens for perf
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print("AuraCore training successful")
            for line in stdout.splitlines():
                if "Final Weights" in line:
                    print(f"TRAINING RESULT: {line}")
        else:
            print(f"AuraCore error: {stderr}")
            
    except Exception as e:
        print(f"Bridge error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
