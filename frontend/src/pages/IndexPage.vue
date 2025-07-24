<template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        @keypress.enter.prevent="evaluateEmotion"
        outlined
      > </q-input>
      <q-btn
        label="Enter"
        color="primary"
        icon-right="send"
        class="q-mt-sm"
        @click="evaluateEmotion"
      > </q-btn>
      <div v-if="loading" class="row justify-center q-mt-md">
        <q-spinner-dots color="primary" size="40px" />
        <span class="q-ml-md q-pt-sm">分析中...</span>
      </div>
       <div v-if="messages.length > 0">
        <q-chat-message :text="[messages[messages.length - 1].original]" sent />
        <p>
          情緒：{{ messages[messages.length - 1].emotion }}，
          分數：{{ messages[messages.length - 1].score }}
        </p>
      </div>
    </div>
    <canvas ref="chartCanvas" style="margin-top: 20px;"></canvas>
    <!-- <div>
      <q-card class="fixed-top-right q-mt-xl" style="width: 250px;">
        <q-card-section>
          <div class="text-h6">box</div>
          <p></p>
        </q-card-section>
      </q-card>
    </div> -->
  </q-page>
</template>


<script setup>
import { ref } from 'vue'
import { analyzeEmotion } from 'src/api/emotionApi'
import Chart from 'chart.js/auto'

const text = ref('')
const messages = ref([]) // stores text, emotion, score

const chartCanvas = ref(null)
let chartInstance = null
const loading = ref(false)

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if (!userInput) 
    return
  loading.value = true
  try {
    console.log("Calling analyzeEmotion with:", userInput)
    const res = await analyzeEmotion(userInput)
    console.log("Got result:", res)

    if (res.error) {
      console.error(res.message)
      return
    }

    const emotionText = res.response?.trim() || '無法判斷'

    messages.value.push({
      original: userInput,
      emotion: emotionText,
      score: emotionToScore(emotionText)
    })

    updateChart()
    text.value = ''
  } catch (err) {
    console.error('Emotion prediction failed:', err)
  } finally {
      loading.value = false
  }
}

function updateChart() {
  const labels = messages.value.map((_, i) => `Input ${i + 1}`)
  const scores = messages.value.map(entry => entry.score)

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "情緒值",
        data: scores,
        borderColor: "rgba(75, 180, 180, 1)",
        backgroundColor: "rgba(75, 180, 180, 0.2)",
        fill: true
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: false,
          suggestedMin: -1,
          suggestedMax: 1
        }
      }
    }
  })
}

function emotionToScore(emotion) {
  const mapping = {
    "悲傷語調": -0.8,
    "憤怒語調": -1.0,
    "厭惡語調": -0.7,
    "疑問語調": -0.3,
    "平淡語氣": 0,
    "驚奇語調": 0.5,
    "開心語調": 1.0,
    "關切語調": 0.3
  }
  return mapping[emotion]
}

</script>

<!-- <template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        @keypress.enter.prevent="evaluateEmotion"
        outlined
      > </q-input>
      <q-btn
        label="Enter"
        color="primary"
        icon-right="send"
        class="q-mt-sm"
        @click="evaluateEmotion"
      > </q-btn>
      <div v-if="loading" class="row justify-center q-mt-md">
        <q-spinner-dots color="primary" size="40px" />
        <span class="q-ml-md q-pt-sm">分析中...</span>
      </div>
      <div v-if="messages.length > 0">
        <q-chat-message :text="[text]" sent />
        <p>
          情緒：{{ messages[messages.length-1].label }}，
          分數：{{ messages[messages.length-1].score }}
        </p>
      </div>
    </div>
    <canvas ref="chartCanvas" style="margin-top: 20px;"></canvas>
  </q-page>
</template> -->


<!-- <script setup>
import { ref } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const text = ref('')
const messages = ref([]) // stores text, label, score

const chartCanvas = ref(null)
let chartInstance = null
const loading = ref(false)

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if(!userInput)
    return
  loading.value = true
  const result = await axios.post("http://localhost:8000/predict", {
    text: userInput
  })
  console.log('Received from backend:', result.data)
  try {
      messages.value.push({
        text: userInput,
        label: result.data.label,
        score: result.data.score,
      })
      if (!chartCanvas.value) {
        console.error('Chart canvas is not available')
        return
      }
      updateChart()
      text.value = ''
    } catch (err) {
      console.error('Emotion prediction failed:', err)
    } finally {
      loading.value = false
    }
  }

  function updateChart() {
  const labels = messages.value.map((_, i) => `Message ${i + 1}`)
  const scores = messages.value.map(entry => entry.score)

  if (chartInstance) {
    chartInstance.destroy() // destroy previous instance if exists
  }   

  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "情緒值",
        data: scores,
        borderColor: "rgba(75, 180, 180, 1)",
        backgroundColor: "rgba(75, 180, 180, 0.2)",
        fill: true
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: false,
          suggestedMin: -1,
          suggestedMax: 1,
        }
      }
    }
  })
  }
</script> -->