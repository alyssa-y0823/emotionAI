import json, requests, time, os
import pandas as pd

# load .env variable
from dotenv import load_dotenv
load_dotenv()
AUTH_TOKEN = os.getenv("VITE_AUTH_TOKEN")

# read sentences.json
with open("sentences.json", "r") as f:
    data = json.load(f)

API_URL = "http://127.0.0.1:8010/invoke"
MODEL = "gemini-2.5-flash"
DEV_PROMPT = (
    "請逐句分析客戶語氣，從以下情緒中選擇一項回覆：「悲傷語調」、「憤怒語調」、「驚奇語調」、「關切語調」、「開心語調」、「平淡語氣」、「疑問語調」、「厭惡語調」、「無法判斷」。請將客戶每次輸入整段話一起判斷出一個情緒，並只輸出那個情緒，例：憤怒語調。"
)

results = []
times = []

for character in data:
    character_info = character["character_information"]
    for emo in character["sentences"]:
        label = emo["emotion_label"]
        print(f"[{character_info}] [{label}]")
        for sent in emo["emotion_sentences"]:
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
                response = requests.post(API_URL, headers=headers, json=payload)
                elapsed = time.time() - start
                times.append(elapsed)
                res_json = response.json() if response.status_code == 200 else {}
                pred = res_json.get("response", "ERROR")
            except Exception as e:
                pred = str(e)
                elapsed = 0
                times.append(elapsed)

            # print results
            print(f"Input: {sent}")
            print(f"Predicted: {pred}")
            print(f"Time: {elapsed:.3f}s | Status: {response.status_code if 'response' in locals() else 'N/A'}")

            results.append({
                "character": character_info,
                "true_emotion": label,
                "sentence": sent,
                "predicted": pred,
                "time": elapsed
            })
            time.sleep(1)

# 統計 summary
if times:
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    print("\n=== Summary ===")
    print(f"Avg Time: {avg_time:.3f} s")
    print(f"Min Time: {min_time:.3f} s")
    print(f"Max Time: {max_time:.3f} s")
    print(f"90th percentile: {pd.Series(times).quantile(0.90):.3f} s")
    print(f"95th percentile: {pd.Series(times).quantile(0.95):.3f} s")

# save as csv file
df = pd.DataFrame(results)
df.to_csv("gemini_2.5_flash_results.csv", index=False)

# accuracy & error rate
acc = (df["predicted"] == df["true_emotion"]).mean()
is_error = df["predicted"].astype(str).str.startswith("ERROR") | (df["predicted"] == "") | (df["predicted"].isnull())
error_rate = is_error.mean()
print(f"Accuracy: {acc*100:.2f}%")
print(f"Error Rate: {error_rate*100:.2f}%")