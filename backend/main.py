from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_name = "tabularisai/multilingual-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def predict_sentiment(texts):
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_map = {
        0: ("Very Negative", -2),
        1: ("Negative", -1), 
        2: ("Neutral", 0), 
        3: ("Positive", 1), 
        4: ("Very Positive", 2)
    }
    top_class = torch.argmax(probabilities).item()
    confidence = probabilities[0, top_class].item()
    rating = sentiment_map[top_class][1]
    return sentiment_map[top_class], round(rating, 4)

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

class TextInput(BaseModel):
    text: str  # define the structure of the input data

@app.post("/predict") # API endpoint (URL path), POST request
async def get_prediction(input: TextInput): # function of API
    label, score = predict_sentiment(input.text)
    return {"label": label, "score": score}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)