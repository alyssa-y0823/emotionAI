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
required_files = ['prompt_2.js', 'sentences.json']
for file in required_files:
    if not os.path.exists(file):
        raise FileNotFoundError(f"Required file '{file}' not found")

if not AUTH_TOKEN:
    raise ValueError("VITE_AUTH_TOKEN not found in environment variables")

# Load prompt and data
with open('prompt_2.js', 'r', encoding='utf-8') as pf:
    prompt = pf.read().strip()

with open("sentences.json", "r", encoding='utf-8') as f:
    data = json.load(f)

# Configuration
API_URL = "http://127.0.0.1:8010/invoke"
MODEL = "gemini-2.5-flash"
DEV_PROMPT = prompt
OUTPUT_FILE = "gemini_2.5_flash_results.csv"

# Function to extract emotion and score from output format
def extract_emotion_and_score(prediction_text):
    """
    Extract emotion label and score from format: 情緒：<情緒標籤> 程度：<分數>
    Returns tuple: (emotion_label, score) or (None, None) if parsing fails
    """
    if not isinstance(prediction_text, str):
        return None, None
    
    # Pattern to match 情緒：<emotion> 程度：<score>
    pattern = r'情緒：([^程度\s]+)\s*程度：([0-9.]+)'
    match = re.search(pattern, prediction_text)
    
    if match:
        emotion = match.group(1).strip()
        try:
            score = float(match.group(2))
            return emotion, score
        except ValueError:
            return emotion, None
    
    return None, None

# Initialize tracking variables
results = []
times = []
error_count = 0
total_requests = 0
emotion_scores = []  # Store all emotion scores for histogram

# Calculate total requests for progress tracking
total_requests_count = sum(len(sent["emotion_sentences"]) for char in data for sent in char["sentences"])
current_request = 0

print(f"Starting batch processing of {total_requests_count} requests...")
print("=" * 60)

for character in data:
    character_info = character["character_information"]
    
    for emo in character["sentences"]:
        label = emo["emotion_label"]
        print(f"\n[Character: {character_info}] [Emotion: {label}]")
        
        for i, sent in enumerate(emo["emotion_sentences"]):
            current_request += 1
            progress = (current_request / total_requests_count) * 100
            
            payload = {
                "instance_id": "111",
                "developer_prompt": DEV_PROMPT,
                "user_prompt": sent,
                "model_name": MODEL,
                "temperature": 0.6
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Function-Name": "batch-test2",
                "X-Platform-ID": "456",
                "Authorization": f"Bearer {AUTH_TOKEN}"
            }

            try:
                start = time.time()
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                elapsed = time.time() - start
                times.append(elapsed)
                
                if response.status_code == 200:
                    res_json = response.json()
                    pred_raw = res_json.get("response", "ERROR")
                    
                    # Extract emotion and score from the response
                    pred_emotion, pred_score = extract_emotion_and_score(pred_raw)
                    
                    if pred_emotion is not None:
                        pred = pred_emotion
                        if pred_score is not None:
                            emotion_scores.append(pred_score)
                    else:
                        pred = "PARSE_ERROR"
                        error_count += 1
                else:
                    pred_raw = f"HTTP_ERROR_{response.status_code}"
                    pred = pred_raw
                    pred_score = None
                    error_count += 1
                    
            except requests.exceptions.Timeout:
                pred_raw = "TIMEOUT_ERROR"
                pred = pred_raw
                pred_score = None
                elapsed = 30.0  # timeout duration
                times.append(elapsed)
                error_count += 1
            except Exception as e:
                pred_raw = f"ERROR: {str(e)}"
                pred = pred_raw
                pred_score = None
                elapsed = 0
                times.append(elapsed)
                error_count += 1

            # Print progress and results
            print(f" [{current_request}/{total_requests_count}] ({progress:.1f}%) "
                  f"Time: {elapsed:.3f}s")
            print(f" Input: {sent[:80]}{'...' if len(sent) > 80 else ''}")
            print(f" Raw Response: {pred_raw if 'pred_raw' in locals() else pred}")
            
            if 'response' in locals():
                status = response.status_code
            else:
                status = 'N/A'
            print(f"  Status: {status}")

            results.append({
                "character": character_info,
                "true_emotion": label,
                "sentence": sent,
                "raw_response": pred_raw if 'pred_raw' in locals() else pred,
                "predicted_emotion": pred,
                "predicted_score": pred_score if 'pred_score' in locals() else None,
                "time": elapsed,
                "status": status
            })
            
            # Rate limiting
            time.sleep(1)

print("\n" + "=" * 60)
print("PROCESSING COMPLETE")
print("=" * 60)

# Performance Statistics
if times:
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    times_series = pd.Series(times)
    
    print(f"\n=== Performance Summary ===")
    print(f"Total Requests: {len(results)}")
    print(f"Successful Requests: {len(results) - error_count}")
    print(f"Failed Requests: {error_count}")
    print(f"Average Response Time: {avg_time:.3f}s")
    print(f"Min Response Time: {min_time:.3f}s")
    print(f"Max Response Time: {max_time:.3f}s")
    print(f"Median Response Time: {times_series.median():.3f}s")
    print(f"90th Percentile: {times_series.quantile(0.90):.3f}s")
    print(f"95th Percentile: {times_series.quantile(0.95):.3f}s")
    print(f"99th Percentile: {times_series.quantile(0.99):.3f}s")

# Save results to CSV
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print(f"\nResults saved to: {OUTPUT_FILE}")

# Accuracy Analysis - now using extracted emotions
print(f"\n=== Accuracy Analysis ===")
valid_predictions = df[~df["predicted_emotion"].astype(str).str.contains("ERROR|TIMEOUT|PARSE_ERROR", na=False)]

if len(valid_predictions) > 0:
    accuracy = (valid_predictions["predicted_emotion"] == valid_predictions["true_emotion"]).mean()
    print(f"Overall Accuracy: {accuracy*100:.2f}% ({len(valid_predictions)} valid predictions)")
    
    # Per-emotion accuracy
    print(f"\n=== Per-Emotion Performance ===")
    emotion_stats = valid_predictions.groupby('true_emotion').agg({
        'predicted_emotion': lambda x: (x == x.name).mean(),
        'sentence': 'count'
    }).round(4)
    emotion_stats.columns = ['accuracy', 'count']
    emotion_stats['accuracy_pct'] = emotion_stats['accuracy'] * 100
    print(emotion_stats.sort_values('accuracy_pct', ascending=False))
    
    # Confusion analysis
    print(f"\n=== Common Misclassifications ===")
    misclassified = valid_predictions[valid_predictions["predicted_emotion"] != valid_predictions["true_emotion"]]
    if len(misclassified) > 0:
        confusion_pairs = misclassified.groupby(['true_emotion', 'predicted_emotion']).size().sort_values(ascending=False)
        print("Top 10 True->Predicted pairs:")
        for (true_emo, pred_emo), count in confusion_pairs.head(10).items():
            print(f"  {true_emo} -> {pred_emo}: {count} times")

else:
    print("No valid predictions found for accuracy calculation")

# Score Statistics
if emotion_scores:
    scores_series = pd.Series(emotion_scores)
    print(f"\n=== Emotion Score Statistics ===")
    print(f"Total Scores Extracted: {len(emotion_scores)}")
    print(f"Average Score: {scores_series.mean():.3f}")
    print(f"Min Score: {scores_series.min():.3f}")
    print(f"Max Score: {scores_series.max():.3f}")
    print(f"Median Score: {scores_series.median():.3f}")
    print(f"Standard Deviation: {scores_series.std():.3f}")

# Error Analysis
is_error = df["predicted_emotion"].astype(str).str.contains("ERROR|TIMEOUT|PARSE_ERROR", na=False)
error_rate = is_error.mean()
print(f"\nError Rate: {error_rate*100:.2f}%")

if error_rate > 0:
    error_types = df[is_error]["predicted_emotion"].value_counts()
    print("Error breakdown:")
    for error_type, count in error_types.items():
        print(f"  {error_type}: {count}")

# Visualization
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Emotion scores distribution by 0.1 intervals (replacing response time histogram)
if emotion_scores:
    score_bins = np.arange(0, max(emotion_scores) + 0.1, 0.1)
    axes[0, 0].hist(emotion_scores, bins=score_bins, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0, 0].set_title('Emotion Score Distribution (程度) - 0.1 intervals')
    axes[0, 0].set_xlabel('Emotion Score (程度)')
    axes[0, 0].set_ylabel('Frequency')
    if emotion_scores:
        avg_score = sum(emotion_scores) / len(emotion_scores)
        axes[0, 0].axvline(avg_score, color='red', linestyle='--', label=f'Mean: {avg_score:.3f}')
        axes[0, 0].legend()
else:
    axes[0, 0].text(0.5, 0.5, 'No emotion scores available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=axes[0, 0].transAxes, fontsize=12)
    axes[0, 0].set_title('Emotion Score Distribution (程度) - 0.1 intervals')

# Response time by 0.05s intervals (keeping this for reference)
time_bins = np.arange(0, max(times) + 0.05, 0.05)
axes[0, 1].hist(times, bins=time_bins, alpha=0.7, color='lightgreen', edgecolor='black')
axes[0, 1].set_title('Response Time Distribution (0.05s intervals)')
axes[0, 1].set_xlabel('Response Time (seconds)')
axes[0, 1].set_ylabel('Frequency')

# Emotion distribution
if len(valid_predictions) > 0:
    emotion_counts = valid_predictions['true_emotion'].value_counts()
    axes[1, 0].bar(range(len(emotion_counts)), emotion_counts.values, color='coral')
    axes[1, 0].set_title('Distribution of True Emotions')
    axes[1, 0].set_xlabel('Emotion')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].set_xticks(range(len(emotion_counts)))
    axes[1, 0].set_xticklabels(emotion_counts.index, rotation=45, ha='right')

# Accuracy by emotion (if valid predictions exist)
if len(valid_predictions) > 0 and len(emotion_stats) > 0:
    axes[1, 1].bar(range(len(emotion_stats)), emotion_stats['accuracy_pct'], color='gold')
    axes[1, 1].set_title('Accuracy by Emotion')
    axes[1, 1].set_xlabel('Emotion')
    axes[1, 1].set_ylabel('Accuracy (%)')
    axes[1, 1].set_xticks(range(len(emotion_stats)))
    axes[1, 1].set_xticklabels(emotion_stats.index, rotation=45, ha='right')
    axes[1, 1].set_ylim(0, 100)

plt.tight_layout()
plt.savefig('batch_test_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nVisualization saved as: batch_test_analysis.png")
print("Analysis complete!")