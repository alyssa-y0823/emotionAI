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
required_files = ['sentences.json']
for file in required_files:
    if not os.path.exists(file):
        print(f"Warning: Required file '{file}' not found")

if not AUTH_TOKEN:
    raise ValueError("VITE_AUTH_TOKEN not found in environment variables")

# Combined prompt for both emotion classification and intensity measurement
def load_prompt(filename, default_content=""):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return default_content

COMBINED_PROMPT_DEFAULT = """
你是一個中文語言分析系統，請對使用者輸入的句子同時進行情緒分類和語言強度分類。

任務1：情緒分類  
請判斷此句最符合下列哪一種情緒（只能選一個）：憤怒、期待、厭惡、恐懼、喜悅、悲傷、驚奇、信任。

任務2：語言強度分類  
請根據句子的語言表達強度，將其分類為以下三個等級之一：

- Low：語言平和、溫和，情感表達較為含蓄
- Medium：語言有一定力度，情感表達適中
- High：語言激烈、強烈，情感表達非常突出

考慮因素包括：
- 形容詞和副詞的使用
- 程度副詞（如「很」、「非常」、「極為」等）
- 語氣詞和感嘆詞
- 重複和強調用法
- 整體語調和情感色彩

輸出格式：
情緒：<情緒標籤>
強度：<Low/Medium/High>

請勿補充說明，直接輸出結果。
"""

combined_prompt = load_prompt('combined_emotion_intensity_prompt.txt', COMBINED_PROMPT_DEFAULT)

# Load test data
with open("sentences.json", "r", encoding='utf-8') as f:
    data = json.load(f)

# Configuration
API_URL = "http://127.0.0.1:8010/invoke"
MODEL = "gpt-4.1"
OUTPUT_FILE = "4.1_3lev_results.csv"

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

def parse_combined_response(response):
    """Extract both emotion and intensity from combined response"""
    result = {
        "emotion": "PARSE_ERROR",
        "intensity": "PARSE_ERROR"
    }
    
    if "ERROR" in str(response):
        result["emotion"] = "ERROR"
        result["intensity"] = "ERROR"
        return result
    
    # Parse emotion
    emotion_match = re.search(r'情緒[：:]\s*([^：:\n\r]+)', response)
    if emotion_match:
        result["emotion"] = emotion_match.group(1).strip()
    else:
        # Fallback: look for known emotions
        emotions = ['憤怒', '期待', '厭惡', '恐懼', '喜悅', '悲傷', '驚奇', '信任']
        for emotion in emotions:
            if emotion in response:
                result["emotion"] = emotion
                break
    
    # Parse intensity
    intensity_match = re.search(r'強度[：:]\s*([^：:\n\r]+)', response)
    if intensity_match:
        intensity = intensity_match.group(1).strip()
        # Normalize to standard format
        if intensity.lower() in ['low', '低', '低強度']:
            result["intensity"] = "Low"
        elif intensity.lower() in ['medium', '中', '中強度']:
            result["intensity"] = "Medium"
        elif intensity.lower() in ['high', '高', '高強度']:
            result["intensity"] = "High"
        else:
            result["intensity"] = intensity
    else:
        # Fallback: look for known intensity levels
        if "Low" in response or "低" in response:
            result["intensity"] = "Low"
        elif "Medium" in response or "中" in response:
            result["intensity"] = "Medium"
        elif "High" in response or "高" in response:
            result["intensity"] = "High"
    
    return result

# Initialize tracking variables
results = []
api_times = []
intensity_levels = []  # Store all intensity classifications
emotion_error_count = 0
intensity_error_count = 0

# Calculate total requests for progress tracking
total_requests_count = sum(len(sent["emotion_sentences"]) for char in data for sent in char["sentences"])
current_request = 0

print(f"Starting combined single API batch processing of {total_requests_count} sentences...")
print("Each sentence will make 1 API call for both: Emotion Classification + Intensity Classification")
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
            
            # Single Combined API Call
            combined_result, api_time, api_status = make_api_call(
                combined_prompt, sent, "emotion-intensity-analyze", temperature=0.6
            )
            api_times.append(api_time)
            parsed_result = parse_combined_response(combined_result)
            
            # Track errors
            if "ERROR" in parsed_result["emotion"] or "PARSE_ERROR" in parsed_result["emotion"]:
                emotion_error_count += 1
            
            if parsed_result["intensity"] in ["Low", "Medium", "High"]:
                intensity_levels.append(parsed_result["intensity"])
            else:
                intensity_error_count += 1
            
            print(f"  API Call: {api_time:.3f}s | Status: {api_status}")
            print(f"  Emotion: {parsed_result['emotion']} | Intensity: {parsed_result['intensity']}")
            
            # Store results
            result_row = {
                "character": character_info,
                "true_emotion": label,
                "sentence": sent,
                "predicted_emotion": parsed_result["emotion"],
                "intensity_level": parsed_result["intensity"],
                "raw_response": combined_result,
                "api_time": api_time,
                "api_status": api_status
            }
            
            results.append(result_row)
            
            # Rate limiting
            time.sleep(1)

print("\n" + "=" * 80)
print("COMBINED SINGLE API PROCESSING COMPLETE")
print("=" * 80)

# Save results to CSV
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print(f"\nResults saved to: {OUTPUT_FILE}")

# Performance Statistics
total_time = sum(df['api_time'])

print(f"\n=== Performance Summary ===")
print(f"Total Sentences Processed: {len(results)}")
print(f"Total API Calls Made: {len(results)} (50% reduction from dual API approach)")
print(f"Total Processing Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

print(f"\n--- Combined API Performance ---")
api_series = pd.Series(api_times)
print(f"Average Response Time: {api_series.mean():.3f}s")
print(f"Min Response Time: {api_series.min():.3f}s")
print(f"Max Response Time: {api_series.max():.3f}s")
print(f"Median Response Time: {api_series.median():.3f}s")
print(f"90th Percentile: {api_series.quantile(0.90):.3f}s")
print(f"95th Percentile: {api_series.quantile(0.95):.3f}s")

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

# Intensity Level Analysis
print(f"\n=== Intensity Level Analysis ===")
if intensity_levels:
    intensity_counter = Counter(intensity_levels)
    total_valid = len(intensity_levels)
    
    print(f"Valid Intensity Classifications: {total_valid}")
    print(f"Distribution of Intensity Levels:")
    for level in ["Low", "Medium", "High"]:
        count = intensity_counter[level]
        percentage = (count / total_valid) * 100
        print(f"  {level}: {count} ({percentage:.1f}%)")
    
    # Intensity distribution by emotion type
    valid_both = df[(df['intensity_level'].isin(["Low", "Medium", "High"])) & 
                    (~df["predicted_emotion"].astype(str).str.contains("ERROR|PARSE_ERROR", na=False))]
    
    if len(valid_both) > 0:
        print(f"\n--- Intensity Distribution by Emotion ---")
        intensity_by_emotion = valid_both.groupby(['true_emotion', 'intensity_level']).size().unstack(fill_value=0)
        
        # Calculate percentages for each emotion
        intensity_pct = intensity_by_emotion.div(intensity_by_emotion.sum(axis=1), axis=0) * 100
        
        for emotion in intensity_pct.index:
            print(f"\n  {emotion} (n={intensity_by_emotion.loc[emotion].sum()}):")
            for level in ["Low", "Medium", "High"]:
                if level in intensity_pct.columns:
                    count = intensity_by_emotion.loc[emotion, level]
                    pct = intensity_pct.loc[emotion, level]
                    print(f"    {level}: {count} ({pct:.1f}%)")
                else:
                    print(f"    {level}: 0 (0.0%)")
        
        # Most common intensity by emotion
        print(f"\n--- Most Common Intensity by Emotion ---")
        for emotion in intensity_by_emotion.index:
            most_common_level = intensity_by_emotion.loc[emotion].idxmax()
            count = intensity_by_emotion.loc[emotion, most_common_level]
            total_emotion = intensity_by_emotion.loc[emotion].sum()
            pct = (count / total_emotion) * 100
            print(f"  {emotion}: {most_common_level} ({count}/{total_emotion}, {pct:.1f}%)")
else:
    print("No valid intensity classifications found")

# Error Analysis
print(f"\n=== Error Analysis ===")
print(f"Emotion Classification Errors: {emotion_error_count} ({emotion_error_count/len(df)*100:.1f}%)")
print(f"Intensity Classification Errors: {intensity_error_count} ({intensity_error_count/len(df)*100:.1f}%)")

# Error type breakdown
emotion_errors = df[df["predicted_emotion"].astype(str).str.contains("ERROR|PARSE_ERROR", na=False)]
if len(emotion_errors) > 0:
    print("\nEmotion error breakdown:")
    for error_type, count in emotion_errors["predicted_emotion"].value_counts().items():
        print(f"  {error_type}: {count}")

intensity_errors = df[~df["intensity_level"].isin(["Low", "Medium", "High"])]
if len(intensity_errors) > 0:
    print("\nIntensity error breakdown:")
    for error_type, count in intensity_errors["intensity_level"].value_counts().items():
        print(f"  {error_type}: {count}")

# Efficiency Comparison
print(f"\n=== Efficiency Improvement ===")
print(f"API Calls Reduction: 50% (from {len(results)*2} to {len(results)} calls)")
estimated_dual_time = total_time * 2.2  # Assuming dual calls would take ~2.2x time (including delays)
time_saved = estimated_dual_time - total_time
print(f"Estimated Time Saved: {time_saved:.1f}s ({time_saved/60:.1f} minutes)")
print(f"Processing Efficiency Gain: {((estimated_dual_time - total_time) / estimated_dual_time * 100):.1f}%")

# Visualization
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Intensity Level Distribution (Main focus - bar chart)
if intensity_levels:
    intensity_counts = Counter(intensity_levels)
    levels = ["Low", "Medium", "High"]
    counts = [intensity_counts[level] for level in levels]
    colors = ['lightblue', 'orange', 'red']
    
    bars = axes[0, 0].bar(levels, counts, color=colors, alpha=0.7, edgecolor='black')
    axes[0, 0].set_title('Intensity Level Distribution (Combined API)')
    axes[0, 0].set_xlabel('Intensity Level')
    axes[0, 0].set_ylabel('Frequency')
    
    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                       f'{count}', ha='center', va='bottom')
else:
    axes[0, 0].text(0.5, 0.5, 'No intensity levels available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=axes[0, 0].transAxes, fontsize=12)
    axes[0, 0].set_title('Intensity Level Distribution')

# API Response Time Distribution
axes[0, 1].hist(api_times, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
axes[0, 1].set_title('Combined API Response Time Distribution')
axes[0, 1].set_xlabel('Response Time (seconds)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].axvline(api_series.mean(), color='red', linestyle='--', 
                   label=f'Mean: {api_series.mean():.3f}s')
axes[0, 1].legend()

# Emotion Distribution
if len(valid_emotions) > 0:
    emotion_counts = valid_emotions['true_emotion'].value_counts()
    axes[1, 0].bar(range(len(emotion_counts)), emotion_counts.values, color='coral')
    axes[1, 0].set_title('Distribution of True Emotions')
    axes[1, 0].set_xlabel('Emotion')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].set_xticks(range(len(emotion_counts)))
    axes[1, 0].set_xticklabels(emotion_counts.index, rotation=45, ha='right')

# Emotion-Intensity Heatmap (if enough data)
if 'valid_both' in locals() and len(valid_both) > 0:
    try:
        # Create pivot table for heatmap
        heatmap_data = valid_both.pivot_table(
            index='predicted_emotion', 
            columns='intensity_level', 
            values='sentence', 
            aggfunc='count', 
            fill_value=0
        )
        
        # Ensure all intensity levels are present
        for level in ["Low", "Medium", "High"]:
            if level not in heatmap_data.columns:
                heatmap_data[level] = 0
        
        # Reorder columns
        heatmap_data = heatmap_data[["Low", "Medium", "High"]]
        
        # Create heatmap
        im = axes[1, 1].imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
        
        # Set ticks and labels
        axes[1, 1].set_xticks(range(len(heatmap_data.columns)))
        axes[1, 1].set_xticklabels(heatmap_data.columns)
        axes[1, 1].set_yticks(range(len(heatmap_data.index)))
        axes[1, 1].set_yticklabels(heatmap_data.index)
        
        # Add text annotations
        for i in range(len(heatmap_data.index)):
            for j in range(len(heatmap_data.columns)):
                text = axes[1, 1].text(j, i, int(heatmap_data.iloc[i, j]),
                                     ha="center", va="center", color="black", fontsize=8)
        
        axes[1, 1].set_title('Emotion-Intensity Heatmap')
        axes[1, 1].set_xlabel('Intensity Level')
        axes[1, 1].set_ylabel('Predicted Emotion')
        
        # Add colorbar
        plt.colorbar(im, ax=axes[1, 1], shrink=0.6)
        
    except Exception as e:
        # Fallback to accuracy chart if heatmap fails
        if 'emotion_stats' in locals():
            axes[1, 1].bar(range(len(emotion_stats)), emotion_stats['accuracy_pct'], color='gold')
            axes[1, 1].set_title('Emotion Classification Accuracy by Type')
            axes[1, 1].set_xlabel('Emotion')
            axes[1, 1].set_ylabel('Accuracy (%)')
            axes[1, 1].set_xticks(range(len(emotion_stats)))
            axes[1, 1].set_xticklabels(emotion_stats.index, rotation=45, ha='right')
            axes[1, 1].set_ylim(0, 100)
elif len(valid_emotions) > 0 and 'emotion_stats' in locals():
    # Fallback to accuracy chart
    axes[1, 1].bar(range(len(emotion_stats)), emotion_stats['accuracy_pct'], color='gold')
    axes[1, 1].set_title('Emotion Classification Accuracy by Type')
    axes[1, 1].set_xlabel('Emotion')
    axes[1, 1].set_ylabel('Accuracy (%)')
    axes[1, 1].set_xticks(range(len(emotion_stats)))
    axes[1, 1].set_xticklabels(emotion_stats.index, rotation=45, ha='right')
    axes[1, 1].set_ylim(0, 100)

plt.tight_layout()
plt.savefig('combined_emotion_intensity_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nVisualization saved as: combined_emotion_intensity_analysis.png")
print("Combined emotion-intensity API analysis complete!")