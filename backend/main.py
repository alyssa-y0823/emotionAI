# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-classification", model="Johnson8187/Chinese-Emotion")

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 添加設備設定
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 已在前面設定 device 變數，這裡無需重複定義
# 標籤映射字典
label_mapping = {
    0: ("平淡語氣", 0.0),
    1: ("關切語調", 0.3),
    2: ("開心語調", 1.0),
    3: ("憤怒語調", -1.0),
    4: ("悲傷語調", -0.8),
    5: ("疑問語調", -0.3),
    6: ("驚奇語調", 0.5),
    7: ("厭惡語調", -0.7)
}

def predict_emotion(text, model_path="Johnson8187/Chinese-Emotion"):
    # 載入模型和分詞器
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)  # 移動模型到設備
    
    # 將文本轉換為模型輸入格式
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)  # 移動輸入到設備
    
    # 進行預測
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 取得預測結果
    predicted_class = torch.argmax(outputs.logits).item() # index
    predicted_emotion, predicted_score = label_mapping[predicted_class] # label & score

    return predicted_emotion, predicted_score


# turn this into an API

from fastapi import FastAPI
from pydantic import BaseModel  # parse JSON into Python objects
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from Quasar dev server (localhost:9000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class TextInput(BaseModel):
    text: str  # define the structure of the input data

@app.post("/predict") # API endpoint (URL path), POST request
async def get_prediction(input: TextInput): # function of API
    label, score = predict_emotion(input.text)
    return {"label": label, "score": score}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)