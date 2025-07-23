import json, requests, time
import pandas as pd

# 讀取 sentences.json
with open("sentences.json", "r") as f:
    data = json.load(f)

API_URL = "http://127.0.0.1:8000/predict"  # calling Chinese Emotion API

results = []
time_list = []
for character in data:
    character_info = character["character_information"]
    for emo in character["sentences"]:
        label = emo["emotion_label"]
        for sent in emo["emotion_sentences"]:
            payload = {"text": sent}
            headers = {
                "Content-Type": "application/json",
            }

            try:
                start = time.time()
                response = requests.post(API_URL, headers=headers, json=payload)
                elapsed = time.time() - start
                res_json = response.json() if response.status_code == 200 else {}
                pred = res_json.get("label", "ERROR")
                print(f"Tested: {sent} | True: {label} | Pred: {pred} | Time: {elapsed:.2f}s")
                time_list.append(elapsed)
            except Exception as e:
                pred = str(e)
                print(f"ERROR for: {sent} | {e}")
                time_list.append(0)

            results.append({
                "character": character_info,
                "true_emotion": label,
                "sentence": sent,
                "predicted": pred
            })
            time.sleep(1)

df = pd.DataFrame(results)
df.to_csv("chinese_emotion_results.csv")

# accuracy / error rate
acc = (df["predicted"] == df["true_emotion"]).mean()
is_error = df["predicted"].astype(str).str.startswith("ERROR") | (df["predicted"] == "") | (df["predicted"].isnull())
error_rate = is_error.mean()
print(f"Accuracy: {acc*100:.2f}%")
print(f"Error Rate: {error_rate*100:.2f}%")

# time
if time_list:
    print(f"Average time: {sum(time_list)/len(time_list):.2f}s, Min time: {min(time_list):.2f}s, Max time: {max(time_list):.2f}s")
    print(f"95th percentile: {pd.Series(time_list).quantile(0.95):.2f}s, 90th percentile: {pd.Series(time_list).quantile(0.90):.2f}s")