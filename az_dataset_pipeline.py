import os
import re
import json
import lzma
import time
import urllib.request
import urllib.parse
import unicodedata
from collections import Counter

# Configuration
RAW_FILE = "az_data/dataset_raw.jsonl"
CLEAN_FILE = "az_data/dataset_clean.jsonl"
DEDUP_FILE = "az_data/dataset_deduplicated.jsonl"
FINAL_FILE = "az_data/dataset_final.jsonl"
STATS_FILE = "az_data/dataset_stats.json"

# Azerbaijani specific parameters
AZ_CHARS = set("əıöüğçşƏIÖÜĞÇŞ")
AZ_STOPWORDS = {
    'və', 'bir', 'olaraq', 'üçün', 'bu', 'da', 'də', 'ki', 'ilə', 'olan', 'sonra',
    'daha', 'tərəfindən', 'həmçinin', 'amma', 'lakin', 'görə', 'kimi', 'edib',
    'bəzi', 'hər', 'yeni', 'böyük', 'həm', 'öz', 'başqa', 'çox', 'isə', 'belə',
    'bunun', 'onun', 'altı', 'iki', 'üç', 'dörd', 'beş', 'il', 'daxil', 'tərəf'
}

def setup_directories():
    os.makedirs("az_data", exist_ok=True)

# ==========================================
# PHASE 1: RAW COLLECTION
# ==========================================

def fetch_wikipedia(target_count=10000):
    """
    Fetches Azerbaijani Wikipedia article extracts using MediaWiki API.
    """
    print(f"\n--- Wikipedia AZ Collection (Target: {target_count} articles) ---")
    url_base = 'https://az.wikipedia.org/w/api.php?action=query&format=json&generator=allpages&gapnamespace=0&gaplimit=50&gapfilterredir=nonredirects&prop=extracts&explaintext=1&exintro=1'
    
    headers = {'User-Agent': 'AuraDatasetPipeline/1.0 (contact: admin@auragpt.org)'}
    continue_params = {}
    count = 0
    pages_collected = []
    
    while count < target_count:
        url = url_base
        for k, v in continue_params.items():
            url += f"&{k}={urllib.parse.quote(str(v))}"
            
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
            query_data = data.get('query', {})
            pages = query_data.get('pages', {})
            
            for page in pages.values():
                title = page.get('title', '')
                extract = page.get('extract', '')
                page_id = page.get('pageid')
                
                # Filter out disambiguation pages or empty extracts
                if extract and len(extract.strip()) > 50:
                    pages_collected.append({
                        "id": f"wiki_{page_id}",
                        "title": title,
                        "text": extract.strip(),
                        "source": "wikipedia_az"
                    })
                    count += 1
                    if count >= target_count:
                        break
            
            # Print count using simple safe ASCII format to avoid terminal encoding errors
            print(f"Collected {count}/{target_count} Wikipedia articles...", end='\r')
            
            # Check for continuation
            continue_params = data.get('continue', {})
            if not continue_params:
                print("\nReached the end of Wikipedia articles.")
                break
                
            # Rate limiting / politeness
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\nError fetching Wikipedia batch: {e}")
            time.sleep(2) # Backoff
            
    print(f"\nFinished Wikipedia collection. Total: {len(pages_collected)} articles.")
    return pages_collected

def stream_cc100(target_docs=150000):
    """
    Streams Azerbaijani CC-100 dataset on the fly and decompresses it chunk-by-chunk.
    """
    print(f"\n--- CC-100 AZ Collection (Target: {target_docs} docs) ---")
    url = "http://data.statmt.org/cc-100/az.txt.xz"
    headers = {'User-Agent': 'AuraDatasetPipeline/1.0'}
    
    docs_collected = []
    decomp = lzma.LZMADecompressor()
    buffer = ""
    doc_count = 0
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            chunk_size = 256 * 1024  # 256 KB
            
            while doc_count < target_docs:
                chunk = resp.read(chunk_size)
                if not chunk:
                    print("\nReached end of stream from server.")
                    break
                
                try:
                    decompressed = decomp.decompress(chunk)
                except Exception as de:
                    print(f"\nDecompression error: {de}")
                    break
                    
                buffer += decompressed.decode('utf-8', errors='ignore')
                
                if "\n\n" in buffer:
                    parts = buffer.split("\n\n")
                    buffer = parts[-1]
                    
                    for doc in parts[:-1]:
                        doc_text = doc.strip()
                        if doc_text and len(doc_text) > 50:
                            docs_collected.append({
                                "id": f"cc100_{doc_count}",
                                "text": doc_text,
                                "source": "cc100_az"
                            })
                            doc_count += 1
                            if doc_count % 1000 == 0:
                                print(f"Collected {doc_count}/{target_docs} CC-100 documents...", end='\r')
                            if doc_count >= target_docs:
                                break
                                
    except Exception as e:
        print(f"\nError streaming CC-100: {e}")
        
    print(f"\nFinished CC-100 collection. Total: {len(docs_collected)} documents.")
    return docs_collected

def parse_local_dataset(filepath="dataset.txt"):
    """
    Parses local augmented dataset.txt.
    """
    print(f"\n--- Local dataset.txt Parsing ({filepath}) ---")
    docs = []
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Skipping.")
        return docs
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse dialogue turns and group Q&A pairs
        # Each QA pair is written as:
        # [USER] query
        # [AURA] response
        qa_pairs = re.findall(r'\[USER\](.*?)\n\[AURA\](.*?)(?=\[USER\]|\Z)', content, re.DOTALL)
        
        for idx, (user, aura) in enumerate(qa_pairs):
            text = f"Sual: {user.strip()}\nCavab: {aura.strip()}"
            docs.append({
                "id": f"local_qa_{idx}",
                "text": text,
                "source": "local_qa"
            })
            
        print(f"Parsed {len(docs)} Q&A pairs from dataset.txt.")
    except Exception as e:
        print(f"Error parsing dataset.txt: {e}")
        
    return docs

def parse_knowledgebase(filepath="universal_knowledgebase_v1.txt"):
    """
    Parses Azerbaijani sections from universal_knowledgebase_v1.txt.
    """
    print(f"\n--- Local knowledgebase Parsing ({filepath}) ---")
    docs = []
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Skipping.")
        return docs
        
    try:
        current_block = []
        is_az = False
        idx = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith('[AZ]'):
                    if current_block and is_az:
                        docs.append({
                            "id": f"local_kb_{idx}",
                            "text": "\n".join(current_block),
                            "source": "local_knowledgebase"
                        })
                        idx += 1
                    current_block = [line_str[4:].strip()]
                    is_az = True
                elif line_str.startswith('[RU]') or line_str.startswith('[EN]'):
                    if current_block and is_az:
                        docs.append({
                            "id": f"local_kb_{idx}",
                            "text": "\n".join(current_block),
                            "source": "local_knowledgebase"
                        })
                        idx += 1
                    current_block = []
                    is_az = False
                elif is_az:
                    if line_str:
                        current_block.append(line_str)
                    else:
                        if current_block:
                            docs.append({
                                "id": f"local_kb_{idx}",
                                "text": "\n".join(current_block),
                                "source": "local_knowledgebase"
                            })
                            idx += 1
                            current_block = []
                            
            if current_block and is_az:
                docs.append({
                    "id": f"local_kb_{idx}",
                    "text": "\n".join(current_block),
                    "source": "local_knowledgebase"
                })
                
        print(f"Parsed {len(docs)} Azerbaijani articles from knowledgebase.")
    except Exception as e:
        print(f"Error parsing knowledgebase: {e}")
        
    return docs

def run_raw_collection():
    setup_directories()
    
    import sys
    force_refresh = "--force" in sys.argv
    
    # Check if local files are newer than the cached RAW_FILE
    if os.path.exists(RAW_FILE) and not force_refresh:
        raw_mtime = os.path.getmtime(RAW_FILE)
        for path in ["dataset.txt", "AuraCore/dataset.txt", "universal_knowledgebase_v1.txt"]:
            if os.path.exists(path) and os.path.getmtime(path) > raw_mtime:
                print(f"\nNote: Local file {path} has been modified since {RAW_FILE} was created.")
                print("Forcing raw collection refresh to include updates.")
                force_refresh = True
                break
                
    if os.path.exists(RAW_FILE) and not force_refresh:
        print(f"\nFound cached raw collection at {RAW_FILE}.")
        print("Skipping Wikipedia API fetching and CC-100 downloading.")
        print("To force download new data, run with the '--force' flag.")
        count = 0
        try:
            with open(RAW_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            print(f"Loaded {count} items from cache.")
            return count
        except Exception as e:
            print(f"Error reading cache: {e}. Re-fetching raw collection...")
            
    # 1. Fetch from sources
    wiki_data = fetch_wikipedia(12000)
    cc100_data = stream_cc100(160000)
    local_qa = parse_local_dataset("dataset.txt")
    local_kb = parse_knowledgebase("universal_knowledgebase_v1.txt")
    
    # Also check AuraCore subdirectory for dataset.txt if not in root
    if not local_qa and os.path.exists("AuraCore/dataset.txt"):
        local_qa = parse_local_dataset("AuraCore/dataset.txt")
        
    all_data = wiki_data + cc100_data + local_qa + local_kb
    
    print(f"\nWriting raw collection to {RAW_FILE}...")
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Raw collection complete. Saved {len(all_data)} items.")
    return len(all_data)

# ==========================================
# PHASE 2: CLEANING
# ==========================================

def clean_document_text(text):
    if not text:
        return ""
        
    # Unicode normalization
    text = unicodedata.normalize('NFC', text)
    
    # 1. Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 2. Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    
    # 3. Remove emails
    text = re.sub(r'\S+@\S+', ' ', text)
    
    # 4. Remove excessive whitespaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 5. Fix linebreaks (keep double newlines at most)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    return text.strip()

def run_cleaning():
    print(f"\n--- Phase 2: Cleaning ({RAW_FILE} -> {CLEAN_FILE}) ---")
    
    import sys
    force_refresh = "--force" in sys.argv
    if os.path.exists(CLEAN_FILE) and not force_refresh:
        print(f"Found cached clean dataset at {CLEAN_FILE}. Skipping cleaning.")
        count = 0
        try:
            with open(CLEAN_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            print(f"Loaded {count} cleaned items from cache.")
            return count
        except Exception as e:
            print(f"Error reading clean cache: {e}. Re-running cleaning...")

    if not os.path.exists(RAW_FILE):
        print(f"Error: {RAW_FILE} does not exist.")
        return 0
        
    clean_count = 0
    filtered_short = 0
    total_raw = 0
    
    with open(RAW_FILE, 'r', encoding='utf-8') as infile, \
         open(CLEAN_FILE, 'w', encoding='utf-8') as outfile:
         
        for line in infile:
            total_raw += 1
            item = json.loads(line)
            raw_text = item.get("text", "")
            
            cleaned_text = clean_document_text(raw_text)
            
            # Length filter: must be at least 80 characters
            if len(cleaned_text) < 80:
                filtered_short += 1
                continue
                
            item["text"] = cleaned_text
            outfile.write(json.dumps(item, ensure_ascii=False) + "\n")
            clean_count += 1
            
    print(f"Cleaning complete.")
    print(f"Total Raw: {total_raw} | Cleaned: {clean_count} | Filtered (short): {filtered_short}")
    return clean_count

# ==========================================
# PHASE 3: DEDUPLICATION & LANGUAGE FILTER
# ==========================================

def is_azerbaijani(text, char_threshold=0.015, word_threshold=0.04):
    """
    Checks if text is Azerbaijani.
    """
    text_lower = text.lower()
    total_chars = len(text_lower)
    if total_chars == 0:
        return False
        
    # Azerbaijani specific letters count
    az_char_count = sum(1 for c in text_lower if c in AZ_CHARS)
    az_char_ratio = az_char_count / total_chars
    
    # Words list
    words = re.findall(r'\b\w+\b', text_lower)
    if not words:
        return False
        
    # Azerbaijani stop words check
    stopword_count = sum(1 for w in words if w in AZ_STOPWORDS)
    stopword_ratio = stopword_count / len(words)
    
    # Heuristics: must have some AZ letters OR AZ stop words
    # Wikipedia titles can be short and have no stop words, but might have AZ chars.
    return (az_char_ratio >= char_threshold) or (stopword_ratio >= word_threshold)

def run_deduplication():
    print(f"\n--- Phase 3: Deduplication & Language Filter ({CLEAN_FILE} -> {DEDUP_FILE}) ---")
    
    import sys
    force_refresh = "--force" in sys.argv
    if os.path.exists(DEDUP_FILE) and not force_refresh:
        print(f"Found cached deduplicated dataset at {DEDUP_FILE}. Skipping deduplication.")
        count = 0
        try:
            with open(DEDUP_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            print(f"Loaded {count} deduplicated items from cache.")
            return count
        except Exception as e:
            print(f"Error reading deduplicated cache: {e}. Re-running deduplication...")

    if not os.path.exists(CLEAN_FILE):
        print(f"Error: {CLEAN_FILE} does not exist.")
        return 0
        
    seen_exact_hashes = set()
    seen_prefixes = set() # For near-duplicate detection of headers/templates
    
    dedup_count = 0
    filtered_dup = 0
    filtered_lang = 0
    filtered_spam = 0
    
    with open(CLEAN_FILE, 'r', encoding='utf-8') as infile, \
         open(DEDUP_FILE, 'w', encoding='utf-8') as outfile:
         
        for line in infile:
            item = json.loads(line)
            text = item.get("text", "")
            
            # 1. Azerbaijani language check
            if not is_azerbaijani(text):
                filtered_lang += 1
                continue
                
            # 2. Spam repetition filter
            words = text.lower().split()
            if len(words) > 15:
                word_counts = Counter(words)
                most_common_word, count = word_counts.most_common(1)[0]
                ratio = count / len(words)
                # If a single word makes up > 30% of the document, it is likely spam
                if ratio > 0.3:
                    filtered_spam += 1
                    continue
            
            # 3. Exact deduplication
            import hashlib
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if text_hash in seen_exact_hashes:
                filtered_dup += 1
                continue
            seen_exact_hashes.add(text_hash)
            
            # 4. Near-duplicate prefix deduplication
            # Wikipedia articles/CC-100 pages sometimes repeat exact introductory standard templates.
            # We take the first 60 characters as a prefix signature (normalized whitespace)
            normalized_prefix = re.sub(r'\s+', '', text[:60].lower())
            if len(normalized_prefix) >= 40:
                if normalized_prefix in seen_prefixes:
                    filtered_dup += 1
                    continue
                seen_prefixes.add(normalized_prefix)
                
            outfile.write(json.dumps(item, ensure_ascii=False) + "\n")
            dedup_count += 1
            
    print(f"Deduplication complete.")
    print(f"Deduplicated count: {dedup_count} | Filtered duplicates: {filtered_dup} | Filtered non-AZ: {filtered_lang} | Filtered spam: {filtered_spam}")
    return dedup_count

# ==========================================
# PHASE 4: FINAL ASSEMBLY & STATS
# ==========================================

def run_final_assembly():
    print(f"\n--- Phase 4: Final Assembly & Stats ({DEDUP_FILE} -> {FINAL_FILE}) ---")
    
    import sys
    force_refresh = "--force" in sys.argv
    if os.path.exists(FINAL_FILE) and os.path.exists(STATS_FILE) and not force_refresh:
        print(f"Found cached final assembly at {FINAL_FILE} and stats at {STATS_FILE}. Skipping assembly.")
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as sf:
                stats = json.load(sf)
            print("\n--- Final Dataset Statistics (from Cache) ---")
            print(f"Total Documents: {stats['total_documents']:,}")
            print(f"Total Words: {stats['total_words']:,}")
            print(f"Total Characters: {stats['total_characters']:,}")
            print(f"Estimated Tokens: {stats['estimated_tokens']:,}")
            print("Source Distribution:")
            for src, count in stats.get('source_distribution', {}).items():
                print(f"  - {src}: {count:,} documents")
            return stats
        except Exception as e:
            print(f"Error reading stats cache: {e}. Re-running final assembly...")

    if not os.path.exists(DEDUP_FILE):
        print(f"Error: {DEDUP_FILE} does not exist.")
        return
        
    total_tokens = 0
    total_words = 0
    total_chars = 0
    docs_by_source = Counter()
    
    with open(DEDUP_FILE, 'r', encoding='utf-8') as infile, \
         open(FINAL_FILE, 'w', encoding='utf-8') as outfile:
         
        for line in infile:
            item = json.loads(line)
            text = item.get("text", "")
            source = item.get("source", "unknown")
            
            # Calculate metrics
            words = text.split()
            word_count = len(words)
            char_count = len(text)
            
            # Token estimation for Azerbaijani (~1.4 tokens per word)
            token_est = int(word_count * 1.4)
            
            total_words += word_count
            total_chars += char_count
            total_tokens += token_est
            
            docs_by_source[source] += 1
            
            outfile.write(line)
            
    stats = {
        "total_documents": sum(docs_by_source.values()),
        "total_words": total_words,
        "total_characters": total_chars,
        "estimated_tokens": total_tokens,
        "source_distribution": dict(docs_by_source),
        "tokens_per_source": {src: int(count * (total_tokens / sum(docs_by_source.values()))) for src, count in docs_by_source.items()}
    }
    
    with open(STATS_FILE, 'w', encoding='utf-8') as sf:
        json.dump(stats, sf, indent=4, ensure_ascii=False)
        
    print("\n--- Final Dataset Statistics ---")
    print(f"Total Documents: {stats['total_documents']:,}")
    print(f"Total Words: {stats['total_words']:,}")
    print(f"Total Characters: {stats['total_characters']:,}")
    print(f"Estimated Tokens: {stats['estimated_tokens']:,}")
    print("Source Distribution:")
    for src, count in docs_by_source.items():
        print(f"  - {src}: {count:,} documents")
        
    return stats

# ==========================================
# MAIN EXECUTION FLOW
# ==========================================

if __name__ == "__main__":
    start_time = time.time()
    
    print("====================================================")
    print("AZERBAIJANI LANGUAGE DATASET PIPELINE — START")
    print("====================================================")
    
    # Step 1: Raw collection
    raw_count = run_raw_collection()
    
    # Step 2: Cleaning
    clean_count = run_cleaning()
    
    # Step 3: Deduplication & Language Filtering
    dedup_count = run_deduplication()
    
    # Step 4: Final assembly & Stats
    stats = run_final_assembly()
    
    elapsed = time.time() - start_time
    print("====================================================")
    print(f"PIPELINE COMPLETED IN {elapsed:.2f} SECONDS")
    print(f"Final output: {FINAL_FILE}")
    print(f"Final estimated tokens: {stats['estimated_tokens']:,}")
    print("====================================================")
