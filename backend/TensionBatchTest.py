import json, requests, time, os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import re

# Load .env variable
from dotenv import load_dotenv
load_dotenv()
AUTH_TOKEN = os.getenv("VITE_AUTH_TOKEN")

# Validate required files and environment
required_files = ['emotion_prompt.txt', 'tension_prompt.txt', 'sentences.json']
for file in required_files:
    if not os.path.exists(file):
        print(f"Warning: Required file '{file}' not found")

if not AUTH_TOKEN:
    raise ValueError("VITE_AUTH_TOKEN not found in environment variables")

# Load prompts
def load_prompt(filename, default_content=""):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return default_content

# Default prompts if files don't exist
EMOTION_PROMPT_DEFAULT = """
你是一個中文情緒分類系統，請對使用者輸入的句子進行情緒分類。

任務：情緒分類  
請判斷此句最符合下列哪一種情緒（只能選一個）：憤怒、期待、厭惡、恐懼、喜悅、悲傷、驚奇、信任。

輸出格式：
情緒：<情緒標籤>

請勿補充說明，直接輸出結果。
"""

TENSION_PROMPT_DEFAULT = """
你是一個中文語言張力(Tension)計算系統，請對使用者輸入的句子計算其語言張力值。

任務：Tension 計算  
請根據以下公式與定義計算此句的 Tension 值：

Tension = ( Modifier + Idiom + 2 × DegreeHead ) ÷ WordCount

定義如下：
- MODIFIER：形容詞、副詞的數量（語氣強化）
- IDIOM：成語或諺語數量
- DegreeHead：程度副詞（例如「很」、「非常」、「極為」、「好」、「太」、「最」）的數量
- WordCount：句子的詞彙總數（不含標點符號）

輸出格式：
Modifier：<數值>
Idiom：<數值>
DegreeHead：<數值>
WordCount：<數值>  
Tension：<結果數值，四捨五入到小數點後兩位>

請勿補充說明，直接輸出結果。
"""

emotion_prompt = load_prompt('emotion_prompt.txt', EMOTION_PROMPT_DEFAULT)
tension_prompt = load_prompt('tension_prompt.txt', TENSION_PROMPT_DEFAULT)

# Load test data
with open("sentences.json", "r", encoding='utf-8') as f:
    data = json.load(f)

# Configuration
API_URL = "http://127.0.0.1:8010/invoke"
MODEL = "gemini-2.5-flash"
OUTPUT_FILE = "dual_backend_batch_results.csv"

def make_api_call(prompt, user_input, function_name, temperature=0.6):
    """Make a single API call and return the result"""
    payload = {
        "instance_id": "111",
        "developer_prompt": prompt,
        "user_prompt": user_input,
        "model_name": MODEL,
        "temperature": temperature
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Function-Name": function_name,
        "X-Platform-ID": "456",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        start = time.time()
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            res_json = response.json()
            result = res_json.get("response", "ERROR").strip()
        else:
            result = f"HTTP_ERROR_{response.status_code}"
            
        return result, elapsed, response.status_code
        
    except requests.exceptions.Timeout:
        return "TIMEOUT_ERROR", 30.0, "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}", 0, "ERROR"

def parse_emotion_response(response):
    """Extract emotion from response"""
    if "ERROR" in str(response):
        return "ERROR"
    
    # Look for pattern: 情緒：<emotion>
    match = re.search(r'情緒[：:]\s*([^：:\n\r]+)', response)
    if match:
        return match.group(1).strip()
    
    # Fallback: look for known emotions
    emotions = ['憤怒', '期待', '厭惡', '恐懼', '喜悅', '悲傷', '驚奇', '信任']
    for emotion in emotions:
        if emotion in response:
            return emotion
    
    return "PARSE_ERROR"

def parse_tension_response(response):
    """Extract tension metrics from response"""
    if "ERROR" in str(response):
        return {"modifier": "ERROR", "idiom": "ERROR", "degree_head": "ERROR", 
                "word_count": "ERROR", "tension": "ERROR"}
    
    result = {}
    
    # Parse each component
    patterns = {
        'modifier': r'Modifier[：:]\s*(\d+)',
        'idiom': r'Idiom[：:]\s*(\d+)', 
        'degree_head': r'DegreeHead[：:]\s*(\d+)',
        'word_count': r'WordCount[：:]\s*(\d+)',
        'tension': r'Tension[：:]\s*([\d.]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, response)
        if match:
            if key == 'tension':
                result[key] = float(match.group(1))
            else:
                result[key] = int(match.group(1))
        else:
            result[key] = "PARSE_ERROR"
    
    return result

# Initialize tracking variables
results = []
emotion_times = []
tension_times = []
tension_scores = []  # Store all tension scores for histogram
emotion_error_count = 0
tension_error_count = 0

# Calculate total requests for progress tracking
total_requests_count = sum(len(sent["emotion_sentences"]) for char in data for sent in char["sentences"])
current_request = 0

print(f"Starting backend dual API batch processing of {total_requests_count} sentences...")
print("Each sentence will make 2 separate API calls: Emotion Classification + Tension Measurement")
print("=" * 80)

for character in data:
    character_info = character["character_information"]
    
    for emo in character["sentences"]:
        label = emo["emotion_label"]
        print(f"\n[Character: {character_info}] [True Emotion: {label}]")
        
        for i, sent in enumerate(emo["emotion_sentences"]):
            current_request += 1
            progress = (current_request / total_requests_count) * 100
            
            print(f"  [{current_request}/{total_requests_count}] ({progress:.1f}%)")
            print(f"  Input: {sent[:80]}{'...' if len(sent) > 80 else ''}")
            
            # API Call 1: Emotion Classification
            emotion_result, emotion_time, emotion_status = make_api_call(
                emotion_prompt, sent, "emotion-classify", temperature=0.6
            )
            emotion_times.append(emotion_time)
            parsed_emotion = parse_emotion_response(emotion_result)
            
            if "ERROR" in parsed_emotion:
                emotion_error_count += 1
            
            print(f"  Emotion API: {emotion_time:.3f}s | Status: {emotion_status} | Result: {parsed_emotion}")
            
            # Small delay between calls
            time.sleep(0.5)
            
            # API Call 2: Tension Measurement  
            tension_result, tension_time, tension_status = make_api_call(
                tension_prompt, sent, "tension-measure", temperature=0.3
            )
            tension_times.append(tension_time)
            parsed_tension = parse_tension_response(tension_result)
            
            # Store tension score for histogram if valid
            if isinstance(parsed_tension.get('tension'), (int, float)):
                tension_scores.append(parsed_tension['tension'])
            else:
                tension_error_count += 1
            
            print(f"  Tension API: {tension_time:.3f}s | Status: {tension_status} | Score: {parsed_tension.get('tension', 'ERROR')}")
            
            # Store results
            result_row = {
                "character": character_info,
                "true_emotion": label,
                "sentence": sent,
                "predicted_emotion": parsed_emotion,
                "emotion_raw_response": emotion_result,
                "emotion_time": emotion_time,
                "emotion_status": emotion_status,
                "tension_modifier": parsed_tension.get('modifier', 'ERROR'),
                "tension_idiom": parsed_tension.get('idiom', 'ERROR'), 
                "tension_degree_head": parsed_tension.get('degree_head', 'ERROR'),
                "tension_word_count": parsed_tension.get('word_count', 'ERROR'),
                "tension_score": parsed_tension.get('tension', 'ERROR'),
                "tension_raw_response": tension_result,
                "tension_time": tension_time,
                "tension_status": tension_status,
                "total_time": emotion_time + tension_time
            }
            
            results.append(result_row)
            
            # Rate limiting
            time.sleep(1)

print("\n" + "=" * 80)
print("BACKEND DUAL API PROCESSING COMPLETE")
print("=" * 80)

# Save results to CSV
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print(f"\nResults saved to: {OUTPUT_FILE}")

# Performance Statistics
all_times = emotion_times + tension_times
total_time = sum(df['total_time'])

print(f"\n=== Performance Summary ===")
print(f"Total Sentences Processed: {len(results)}")
print(f"Total API Calls Made: {len(results) * 2}")
print(f"Total Processing Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

print(f"\n--- Emotion API Performance ---")
emotion_series = pd.Series(emotion_times)
print(f"Average Response Time: {emotion_series.mean():.3f}s")
print(f"Min Response Time: {emotion_series.min():.3f}s")
print(f"Max Response Time: {emotion_series.max():.3f}s")
print(f"Median Response Time: {emotion_series.median():.3f}s")
print(f"90th Percentile: {emotion_series.quantile(0.90):.3f}s")
print(f"95th Percentile: {emotion_series.quantile(0.95):.3f}s")

print(f"\n--- Tension API Performance ---")
tension_series = pd.Series(tension_times)
print(f"Average Response Time: {tension_series.mean():.3f}s")
print(f"Min Response Time: {tension_series.min():.3f}s")
print(f"Max Response Time: {tension_series.max():.3f}s")
print(f"Median Response Time: {tension_series.median():.3f}s")
print(f"90th Percentile: {tension_series.quantile(0.90):.3f}s")
print(f"95th Percentile: {tension_series.quantile(0.95):.3f}s")

# Emotion Classification Accuracy Analysis
print(f"\n=== Emotion Classification Accuracy ===")
valid_emotions = df[~df["predicted_emotion"].astype(str).str.contains("ERROR|PARSE_ERROR", na=False)]

if len(valid_emotions) > 0:
    emotion_accuracy = (valid_emotions["predicted_emotion"] == valid_emotions["true_emotion"]).mean()
    print(f"Overall Emotion Accuracy: {emotion_accuracy*100:.2f}% ({len(valid_emotions)}/{len(df)} valid predictions)")
    
    # Per-emotion accuracy
    print(f"\n--- Per-Emotion Performance ---")
    emotion_stats = valid_emotions.groupby('true_emotion').agg({
        'predicted_emotion': lambda x: (x == x.name).mean(),
        'sentence': 'count'
    }).round(4)
    emotion_stats.columns = ['accuracy', 'count']
    emotion_stats['accuracy_pct'] = emotion_stats['accuracy'] * 100
    print(emotion_stats.sort_values('accuracy_pct', ascending=False))
    
    # Confusion analysis
    print(f"\n--- Common Misclassifications ---")
    misclassified = valid_emotions[valid_emotions["predicted_emotion"] != valid_emotions["true_emotion"]]
    if len(misclassified) > 0:
        confusion_pairs = misclassified.groupby(['true_emotion', 'predicted_emotion']).size().sort_values(ascending=False)
        print("Top 10 True->Predicted pairs:")
        for (true_emo, pred_emo), count in confusion_pairs.head(10).items():
            print(f"  {true_emo} -> {pred_emo}: {count} times")
else:
    print("No valid emotion predictions found for accuracy calculation")

# Tension Score Analysis
print(f"\n=== Tension Score Analysis ===")
if tension_scores:
    scores_series = pd.Series(tension_scores)
    print(f"Valid Tension Scores: {len(tension_scores)}")
    print(f"Average Tension Score: {scores_series.mean():.4f}")
    print(f"Min Tension Score: {scores_series.min():.4f}")
    print(f"Max Tension Score: {scores_series.max():.4f}")
    print(f"Median Tension Score: {scores_series.median():.4f}")
    print(f"Standard Deviation: {scores_series.std():.4f}")
    
    # Tension by emotion type
    valid_both = df[(pd.to_numeric(df['tension_score'], errors='coerce').notna()) & 
                    (~df["predicted_emotion"].astype(str).str.contains("ERROR|PARSE_ERROR", na=False))]
    
    if len(valid_both) > 0:
        print(f"\n--- Average Tension by Emotion ---")
        tension_by_emotion = valid_both.groupby('true_emotion')['tension_score'].apply(
            lambda x: pd.to_numeric(x, errors='coerce').mean()
        ).sort_values(ascending=False)
        for emotion, avg_tension in tension_by_emotion.items():
            count = len(valid_both[valid_both['true_emotion'] == emotion])
            print(f"  {emotion}: {avg_tension:.4f} (n={count})")
else:
    print("No valid tension scores found")

# Error Analysis
print(f"\n=== Error Analysis ===")
print(f"Emotion Classification Errors: {emotion_error_count} ({emotion_error_count/len(df)*100:.1f}%)")
print(f"Tension Measurement Errors: {tension_error_count} ({tension_error_count/len(df)*100:.1f}%)")

# Error type breakdown
emotion_errors = df[df["predicted_emotion"].astype(str).str.contains("ERROR|PARSE_ERROR", na=False)]
if len(emotion_errors) > 0:
    print("\nEmotion error breakdown:")
    for error_type, count in emotion_errors["predicted_emotion"].value_counts().items():
        print(f"  {error_type}: {count}")

# Visualization
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Tension Score Distribution (Main focus - histogram)
if tension_scores:
    # Create bins with 0.05 intervals for tension scores
    min_score = min(tension_scores)
    max_score = max(tension_scores)
    bins = np.arange(min_score, max_score + 0.05, 0.05)
    
    axes[0, 0].hist(tension_scores, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0, 0].set_title('Tension Score Distribution (0.05 intervals)')
    axes[0, 0].set_xlabel('Tension Score')
    axes[0, 0].set_ylabel('Frequency')
    
    avg_tension = sum(tension_scores) / len(tension_scores)
    axes[0, 0].axvline(avg_tension, color='red', linestyle='--', label=f'Mean: {avg_tension:.4f}')
    axes[0, 0].legend()
else:
    axes[0, 0].text(0.5, 0.5, 'No tension scores available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=axes[0, 0].transAxes, fontsize=12)
    axes[0, 0].set_title('Tension Score Distribution')

# API Response Time Comparison
axes[0, 1].boxplot([emotion_times, tension_times], labels=['Emotion API', 'Tension API'])
axes[0, 1].set_title('API Response Time Comparison')
axes[0, 1].set_ylabel('Response Time (seconds)')

# Emotion Distribution
if len(valid_emotions) > 0:
    emotion_counts = valid_emotions['true_emotion'].value_counts()
    axes[1, 0].bar(range(len(emotion_counts)), emotion_counts.values, color='coral')
    axes[1, 0].set_title('Distribution of True Emotions')
    axes[1, 0].set_xlabel('Emotion')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].set_xticks(range(len(emotion_counts)))
    axes[1, 0].set_xticklabels(emotion_counts.index, rotation=45, ha='right')

# Accuracy by Emotion
if len(valid_emotions) > 0 and 'emotion_stats' in locals():
    axes[1, 1].bar(range(len(emotion_stats)), emotion_stats['accuracy_pct'], color='gold')
    axes[1, 1].set_title('Accuracy by Emotion')
    axes[1, 1].set_xlabel('Emotion')
    axes[1, 1].set_ylabel('Accuracy (%)')
    axes[1, 1].set_xticks(range(len(emotion_stats)))
    axes[1, 1].set_xticklabels(emotion_stats.index, rotation=45, ha='right')
    axes[1, 1].set_ylim(0, 100)

plt.tight_layout()
plt.savefig('backend_dual_batch_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nVisualization saved as: backend_dual_batch_analysis.png")
print("Backend dual API analysis complete!")