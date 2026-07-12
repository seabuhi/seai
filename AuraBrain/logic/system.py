import os
import re
import sqlite3
import subprocess
import requests
import math
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

class MCTSNode:
    """Monte Carlo Tree Search decision node for Hybrid Reasoning."""
    def __init__(self, state, parent=None, action=None):
        self.state = state # The query string
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions = ["Direct_Answer", "Search_KB", "Search_Web"] if parent is None else []

    def select_child(self):
        best_uct = -1
        best_child = None
        for child in self.children:
            if child.visits == 0: return child
            exploit = child.value / child.visits
            explore = math.sqrt(2 * math.log(self.visits) / child.visits)
            uct = exploit + explore
            if uct > best_uct:
                best_uct = uct
                best_child = child
        return best_child

    def expand(self):
        action = self.untried_actions.pop()
        child = MCTSNode(state=self.state, parent=self, action=action)
        self.children.append(child)
        return child

    def simulate(self):
        # Heuristic Network Strategy (Simulated Value Network)
        query_lower = self.state.lower()
        if self.action == "Direct_Answer":
            if any(w in query_lower for w in ["salam", "hi", "necəsən", "kimsən", "adın"]):
                return 1.0
            return 0.1
        elif self.action == "Search_KB":
            # Favor KB if query looks like a concepts definition request
            if sum(1 for w in query_lower.split() if len(w) > 4) > 1:
                return 0.8
            return 0.4
        elif self.action == "Search_Web":
            # Favor Web if looking for code/tutorials
            if any(w in query_lower for w in ["kodu", "yaz", "necə", "python", "proqram"]):
                return 0.95
            return 0.6
        return 0.0

    def backpropagate(self, reward):
        self.visits += 1
        self.value += reward
        if self.parent:
            self.parent.backpropagate(reward)

class KnowledgeBase:
    """Stores and retrieves local dataset knowledge."""
    def __init__(self, filename="universal_knowledgebase_v1.txt"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dataset_path = os.path.join(self.base_dir, filename)

    def search(self, query: str):
        if not os.path.exists(self.dataset_path):
            return None
            
        keywords = [w.lower() for w in query.replace("?", "").replace(",", "").split() if len(w) > 3]
        if not keywords: return None
            
        best_match = ""
        max_score = 0
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                paragraphs = f.read().split("\n\n")
                for p in paragraphs:
                    score = sum(1 for k in keywords if re.search(r'\b'+re.escape(k)+r'\b', p.lower()))
                    if score > max_score:
                        max_score = score
                        best_match = p.strip()
            min_required = max(1, len(keywords) // 2)
            if len(keywords) > 1 and max_score < 2: return None
            if max_score >= min_required and len(best_match) > 20: return best_match
        except Exception as e:
            print(f"KB Error: {e}")
        return None

class SearchEngine:
    """Retrieves online external knowledge."""
    def search(self, query: str, max_results: int = 2):
        results = []
        lang = "az" if any(w in query for w in ["nə", "necə", "kodu"]) else "en"
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": query, "utf8": "", "format": "json", "srlimit": max_results}
        headers = {"User-Agent": "AuraBot/1.0 (contact@aura-ai.com)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5).json()
            for hit in resp.get("query", {}).get("search", []):
                snippet = re.sub(r'<[^>]+>', '', hit['snippet'])
                results.append(snippet)
        except Exception as e:
            print(f"Search Error: {e}")
        return results

class Memory:
    """Long-term and Short-term chat history storage."""
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "aura_memory.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, role TEXT, content TEXT)")

    def add_memory(self, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO history (role, content) VALUES (?, ?)", (role, content))

    def get_recent_context(self, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,))
            return list(reversed(cur.fetchall()))

class LearningSystem:
    """Interfaces with C++ Hydra Core for weight updates."""
    def __init__(self):
        self.core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "AuraCore", "tensor.exe")
        self.vocab = {}
        self.next_id = 1

    def tokenize(self, text: str):
        tokens = []
        for word in text.split():
            clean = "".join(c for c in word.lower() if c.isalnum())
            if clean:
                if clean not in self.vocab:
                    self.vocab[clean] = self.next_id
                    self.next_id += 1
                tokens.append(self.vocab[clean])
        return tokens

    def train_background(self, text: str):
        tokens = self.tokenize(text)
        if not tokens: return
        try:
            cmd = [self.core_path, "--train"] + [str(t) for t in tokens[:200]] # batch limit
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Learning error: {e}")

class LanguageGenerator:
    """Legacy extractor for fallback (not used in primary flow)."""
    def generate(self, context: str, source: str) -> str:
        if not context:
            return "Axtardığın məlumat barədə dəqiq bir şey tapa bilmədim."
        return f"Tapdığım məlumat ({source}):\n{context}"

class HuggingFaceGenerator:
    """Synthesizes context into natural language response using Hugging Face LLM."""
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, query: str, context: str, source: str, history: list) -> str:
        if not self.api_key or "your_hugging_face_token" in self.api_key:
            return f"XƏTA: Hugging Face API açarı təyin edilməyib. Zəhmət olmasa .env faylında HF_API_KEY sahəsini doldurun.\n\n(Fallback): {context}"

        # Building OpenAI-style message list
        system_content = (
            "Sən Aura AI (Aura Süni İntellekt Sistemi) — son dərəcə ağıllı, professional və milli dəyərlərə "
            "hörmətlə yanaşan Azərbaycanlı süni intellekt köməkçisisən.\n"
            "Sənin əsas məqsədin istifadəçinin suallarına mükəmməl, axıcı, təbii, qrammatik cəhətdən tam qüsursuz "
            "və zərif Azərbaycan dilində cavab verməkdir. Cavablarında elmi dəqiqliyə, aydınlığa, məntiqə və nəzakətə üstünlük ver.\n"
            "Sənə verilən məlumatlar və kontekstlər əsasında ən doğru və geniş izahları tərtib et.\n"
            f"İnformasiya mənbəyi: {source}.\n"
            f"İstifadə ediləcək yerli kontekst: {context}."
        )
        
        messages = [{"role": "system", "content": system_content}]
        
        # Ensure alternating roles and clean history
        # We merge context into the first user message if possible to keep it clean
        context_str = f"[MƏLUMAT/KONTEKST]: {context}\n\n" if context else ""
        
        history_messages = []
        for role, content in history:
            hf_role = "user" if role == "user" else "assistant"
            # Avoid consecutive same roles
            if history_messages and history_messages[-1]["role"] == hf_role:
                history_messages[-1]["content"] += f"\n{content}"
            else:
                history_messages.append({"role": hf_role, "content": content})

        # Final sequence construction
        if history_messages:
            # Prepend context to the first historical user message if it exists, else use current
            if history_messages[0]["role"] == "user":
                history_messages[0]["content"] = context_str + history_messages[0]["content"]
            else:
                messages.append({"role": "user", "content": context_str or "Sistem məlumatı yeniləndi."})
                messages.append({"role": "assistant", "content": "Anladım."})
            messages.extend(history_messages)
        else:
            if context_str:
                messages.append({"role": "user", "content": context_str + "Salam Aura."})
                messages.append({"role": "assistant", "content": "Salam! Anladım, bu məlumatlar əsasında cavab verəcəyəm."})

        # Add current query - ensuring it follows assistant
        if messages[-1]["role"] == "user":
            messages[-1]["content"] += f"\n\nCari Sual: {query}"
        else:
            messages.append({"role": "user", "content": query})
            
        # Add a professional pre-start for the AI to set a premium Azerbaijani tone
        messages.append({"role": "assistant", "content": "Aura Sistemi aktivdir. Sorğunuz əsasında tərtib edilmiş məlumat aşağıdakı kimidir:"})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.4
        }

        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
                if response.status_code in [500, 503, 504]:
                    print(f"HF Router Transient Error ({response.status_code}). Attempt {attempt + 1}/{max_retries}. Retrying...")
                    time.sleep(2)
                    continue
                    
                if response.status_code != 200:
                    print(f"DEBUG HF ERROR: {response.status_code} - {response.text}")
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"].strip()
                    return answer
                return f"API-dən gözlənilməz cavab formatı gəldi: {result}"
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"HF Router Fatal Error after {max_retries} attempts: {e}")
                    error_msg = f"Xəta: {str(e)}"
                    if 'response' in locals() and hasattr(response, 'text'):
                        error_msg += f" (Detallar: {response.text[:200]})"
                    return f"Bağışlayın, LLM mühərriki ilə hazırda əlaqə qurmaq mümkün deyil (Server Error). Zəhmət olmasa bir az sonra yenidən yoxlayın.\n\n{error_msg}\n\n(Fallback Məlumat): {context}"
                time.sleep(2)

class ReasoningEngine:
    """Orchestrates the AI flow, deciding where to get data and how to respond."""
    def __init__(self):
        self.kb = KnowledgeBase()
        self.search = SearchEngine()
        self.memory = Memory()
        self.learner = LearningSystem()
        self.generator = HuggingFaceGenerator()

    def process_query(self, query: str) -> str:
        # Step 1: Record to memory
        self.memory.add_memory("user", query)
        
        # MCTS Run (5 Simulation Iterations for Speed)
        root = MCTSNode(state=query)
        for _ in range(5):
            node = root
            # Selection
            while not node.untried_actions and node.children:
                node = node.select_child()
            # Expansion
            if node.untried_actions:
                node = node.expand()
            # Simulation
            reward = node.simulate()
            # Backpropagation
            node.backpropagate(reward)
            
        # Extract best action from MCTS
        best_action_node = max(root.children, key=lambda c: c.visits)
        chosen_action = best_action_node.action
        print(f"MCTS Selected Strategy: {chosen_action} (Visits: {best_action_node.visits})")
        
        source = ""
        context = ""
        
        if chosen_action == "Direct_Answer":
            source = "Direct Reasoning (Aura Identity)"
            context = "İstifadəçi salam verdi və ya ümumi söhbət edir. Sən Aura AI-san."


        # Knowledge Base Execution
        if chosen_action == "Search_KB":
            source = "Local Knowledge Base (MCTS Routed)"
            context = self.kb.search(query)
            if not context:
                chosen_action = "Search_Web" # Dynamic fallback
                print("MCTS dynamic fallback: KB failed, switching to Search_Web")

        # Web Execution
        if chosen_action == "Search_Web":
            source = "External Web Search (MCTS Routed)"
            web_results = self.search.search(query)
            if web_results:
                context = " ".join(web_results)

        # Step 4: Background Learning (Disabled for performance)
        # if context:
        #     self.learner.train_background(context)

        # Step 5: Language Generation (LLM Synthesis)
        history = self.memory.get_recent_context(limit=5)
        final_answer = self.generator.generate(query, context, source, history)
        
        # Step 6: Record output to memory
        self.memory.add_memory("ai", final_answer)
        
        return final_answer

# Singleton System Entry Point
class AuraSystem:
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ReasoningEngine()
        return cls._instance
