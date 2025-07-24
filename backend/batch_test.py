import pandas as pd
import requests
import time

# Load the dataset
df = pd.read_csv("hf://datasets/Johnson8187/Chinese_Multi-Emotion_Dialogue_Dataset/data.csv")
df = df[['text', 'emotion']].dropna()

# FastAPI endpoint
API_URL = "http://127.0.0.1:8010/invoke"

MODELS = {
    "GPT 4.1": "gpt-4.1",
    "GPT 4.1 mini": "gpt-4.1-mini",
    "Gemini 2.5 Flash": "gemini-2.5-flash"
}

DEV_PROMPT = (
    "請逐句分析客戶語氣，從以下情緒中選擇一項回覆：「悲傷語調」、「憤怒語調」、「驚奇語調」、「關切語調」、「開心語調」、「平淡語氣」、「疑問語調」、「厭惡語調」、「無法判斷」。請將客戶每次輸入整段話一起判斷出一個情緒，並指輸出那個情緒，例：憤怒語調。"
)

results = []
times = {model: [] for model in MODELS}

from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment
AUTH_TOKEN = os.getenv("VITE_AUTH_TOKEN")

for row_num, (i, row) in enumerate(df.sample(n=1000).iterrows(), 1):
    print(f"Processing row {row_num}: {row['text']}\t語氣：{row['emotion']}")  
    text = row['text']
    emotion = row['emotion']
    result_row = {"text": text, "true emotion": emotion}
    for model_key, model_value in MODELS.items():
        payload = {
            "instance_id": "111",
            "developer_prompt": DEV_PROMPT,
            "user_prompt": text,
            "model_name": model_value,
            "temperature": 0.6
        }
        headers = {
            "Content-Type": "application/json",
            "X-Function-Name": "batch-test",
            "X-Platform-ID": "123",
            "Authorization": f"Bearer {AUTH_TOKEN}",
        }

        try:
            start_time = time.time()
            response = requests.post(API_URL, headers=headers, json=payload)
            elapsed_time = time.time() - start_time
            print(f"\t{model_key}: {response.text}, time: {elapsed_time:.3f}s") # request sent
            times[model_key].append(elapsed_time)  # store time taken for each model
            if response.status_code == 200:
                res_json = response.json()
                if "error" in res_json:
                    result_row[model_key] = f"ERROR: {res_json['error']}"
                else:
                    res = res_json.get("response", "").strip()
                    result_row[model_key] = res
            else:
                result_row[model_key] = f"ERROR {response.status_code}"

        except Exception as e:
            print(f"Exception when requesting {model_key}: {e}")
            result_row[model_key] = str(e)

        time.sleep(1)
    results.append(result_row)

df_result = pd.DataFrame(results)   # convert results to pandas df
df_result.to_csv("sandbox_llm_results.csv", index=False)    # saves df to csv file

for model_key in MODELS:
    acc = (df_result[model_key] == df_result["true emotion"]).mean()
    is_error = df_result[model_key].astype(str).str.startswith("ERROR")
    error_rate = is_error.mean()
    avg_time = sum(times[model_key]) / len(times[model_key]) if times[model_key] else 0
    print(f"{model_key} accuracy: {acc:.2%}, error rate: {error_rate:.2%}")
    print(f"\taverage time: {avg_time:.3f}s, 95th percentile: {pd.Series(times[model_key]).quantile(0.95):.3f}s, 90th percentile: {pd.Series(times[model_key]).quantile(0.90):.3f}s, min time: {min(times[model_key]):.3f}s, max time: {max(times[model_key]):.3f}s")