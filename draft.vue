<!-- contains code from previous model for easy access -->

<!--
<template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        outlined
      > </q-input>
      <q-btn
        label="Enter"
        color="primary"
        icon-right="send"
        class="q-mt-sm"
        @click="evaluateEmotion"
      > </q-btn>
       <div v-if="message">
        <q-chat-message :text="[text]" sent />
        <q-chat-message :text="[`情緒：${message.label}`, `分數：${message.score}`]"
        />
      </div>
    </div>
  </q-page>
</template>


<script setup>
import { ref } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const text = ref('')
const message = ref([])

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if(!userInput)
    return
  const result = await axios.post("http://localhost:8000/predict", {
    text: userInput
  })

  try {
      message.value = {
        text: userInput,
        label: result.data.label,
        score: result.data.score
      }
      text.value = ''
    } catch (err) {
      console.error('Emotion prediction failed:', err)
    }
  }
</script>
-->

<!--
<template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        outlined
        @keydown.enter="evaluateEmotion"
      > </q-input>
      <q-btn
        label="Enter"
        color="primary"
        icon-right="send"
        class="q-mt-sm"
        @click="evaluateEmotion"
      > </q-btn>
       <div v-if="inputs.length">
        <q-chat-message v-for="(entry, index) in inputs" :key="`input-${index}`" :text="[input.text]" sent />
        <q-chat-message v-for="(input, index) in inputs" :key="`label-${index}`" :text="[`情緒：${entry.label}`, `分數：${entry.score}`]" />
        </div>
      <canvas ref="myChart" style="max-width: 700px; width: 100%"> </canvas>
    </div>
  </q-page>
</template>


<script setup>
import { ref } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const text = ref('')
const inputs = ref([]) // stores text, label, score

const chartCanvas = ref(null)
let chartInstance = null

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if(!userInput)
    return
  const result = await axios.post("http://localhost:8000/predict", {
    text: userInput
  })

  try {
      // add to inputs array
      inputs.value.push({
        text: userInput,
        label: result.data.label,
        score: result.data.score
      })
      updateChart()
      text.value = ''
      index++
    } catch (err) {
      console.error('Emotion prediction failed:', err)
    }
  }

function updateChart() {
  const labels = inputs.value.map((_, i) => `Input ${i + 1}`)
  const scores = inputs.value.map(entry => entry.score)

  if (chartInstance) {
    chartInstance.destroy() // destroy previous instance if exists
  }   

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "情緒分數",
        data: scores,
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        fill: true,
        tension: 0.1
      }]
    }
  })
}

</script>
-->

<!--
# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-classification", model="Johnson8187/Chinese-Emotion")

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 添加設備設定
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 已在前面設定 device 變數，這裡無需重複定義
# 標籤映射字典
label_mapping = {   # label_mapping[index] = (label, score)
    # set emotion score from -1 to 1
    0: ("平淡語氣(Neutral)", 0.0),
    1: ("關切語調(Concerned)", -0.1),
    2: ("開心語調(Joy)", 1.0),
    3: ("憤怒語調(Anger)", -1.0),
    4: ("悲傷語調(Sadness)", -0.6),
    5: ("疑問語調(Questioning)", -0.2),
    6: ("驚奇語調(Surprise)", 0.2),
    7: ("厭惡語調(Disgust)", -0.7)
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

class TextInput(BaseModel):
    text: str  # define the structure of the input data

@app.post("/predict") # API endpoint (URL path), POST request
async def get_prediction(input: TextInput): # function of API
    label, score = predict_emotion(input.text)
    return {"label": label, "score": score}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

    -->