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

for i, row in df.head(10).iterrows():  
    print(f"Processing row {i+1}: {row['text']}\t語氣：{row['emotion']}")  

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
        },
        headers = {
            "Content-Type": "application/json",
            "X-Function-Name": "batch-test",
            "X-Platform-ID": "123",
            "Authorization": "Bearer ",
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            # print(f"Raw response from {model_key}: {response.text}")
            if response.status_code == 200:
                res = response.json().get("response", "").strip()
                result_row[model_key] = res
                # if res != ...

            else:
                result_row[model_key] = f"ERROR {response.status_code}"
        except Exception as e:
            result_row[model_key] = str(e)

        time.sleep(1)  # cool off
    # result_row = {'text': '你要不要去吃午餐？', 'true emotion': '平淡語氣', 
    #               'GPT 4.1': '疑問語調', 'GPT 4.1 mini': '疑問語調', 'Gemini 2.5 Flash': '疑問語調'}
    results.append(result_row)
    # List[Dict[model, res]]

df_result = pd.DataFrame(results)   # convert results to pandas df
df_result.to_csv("sandbox_llm_results.csv", index=False)    # saves df to csv file

# Evaluate
for model in MODELS:
    acc = (df_result[model] == df_result["true emotion"]).mean()
    print(f"{model} accuracy: {acc:.2%}")