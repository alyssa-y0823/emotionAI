from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your frontend URL, e.g., ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import httpx
def deepl_translate(text: str, api_key: str) -> str:
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": api_key,
        "text": text,
        "target_lang": "EN"
    }
    response = httpx.post(url, data=params)
    response.raise_for_status()
    return response.json()["translations"][0]["text"]

# Define the input model
class TextRequest(BaseModel):
    texts: List[str]

# Use a pipeline as a high-level helper
from transformers import pipeline
sentiment_analysis = pipeline("text-classification", model="boltuix/bert-emotion")

# Map emotions to scores
label_mapping = {
    "sadness": -0.6,
    "anger": -1.0,
    "love": 0.9,
    "surprise": 0.2,
    "fear": -0.7,
    "happiness": 1.0,
    "neutral": 0.0,
    "disgust": -0.8,
    "shame": -0.5,
    "guilt": -0.4,
    "confusion": -0.3,
    "desire": 0.8,
    "sarcasm": -0.2,
}


import os
api_key = os.environ.get('DEEPL_APIKEY')

@app.post("/analyze")
async def analyze_emotions(request: TextRequest):
    original_texts = request.texts
    translated_texts = [
    deepl_translate(text, api_key)
    for text in original_texts
    ]
    
    results = []
    for original, translated in zip(original_texts, translated_texts):
        prediction = sentiment_analysis(translated)[0]
        emotion = prediction["label"]
        conf = round(prediction["score"], 4)
        emotion_score = label_mapping.get(emotion)

        results.append({
            "original": original,
            "translated": translated,
            "emotion": emotion,
            "confidence": conf,
            "graph_score": emotion_score
        })

    return {"results": results}