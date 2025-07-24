<template>
  <q-page class="q-mb-md">
    <!-- radar chart -->
    <div v-if="messages.length > 0" class="fixed-top-right q-mt-md q-mr-md" style="width: 350px; height: 350px;">
      <q-card class="full-height">
        <q-card-section class="q-pa-sm">
          <div class="text-subtitle2 text-center q-mb-xs">情緒分佈</div>
          <div style="height: 300px; position: relative;">
            <canvas ref="radarChartCanvas"></canvas>
          </div>
        </q-card-section>
      </q-card>
    </div>
    <div style="max-width: 800px; width: 100%">
      <div class="row q-gutter-sm">
        <!-- text box  -->
        <div class="col">
          <q-input
            v-model="text"
            label="請輸入文字"
            autogrow
            type="textarea"
            @keypress.enter.prevent="evaluateEmotion"
            outlined
            class="q-mt-xs"
          />
        </div>
        <!-- enter button -->
        <div class="col-auto">
          <q-btn
            label="Enter"
            color="primary"
            icon-right="send"
            @click="evaluateEmotion"
            style="height: 45px"
            class="q-mt-sm"
          />
        </div>
        <!-- delete button -->
        <div class="col-auto">
          <q-btn
          v-if="messages.length > 0"
          label="清除紀錄"
          color="grey"
          icon-right="delete"
          outline
          @click="clearHistory"
          style="height: 45px"
          class="q-mt-sm"
          />
        </div>
      </div>
      <!-- loading -->
      <div v-if="loading" class="row justify-center q-mt-sm">
        <q-spinner-dots color="primary" size="24px" />
        <span class="q-ml-sm">分析中...</span>
      </div>
      <!-- error message -->
      <div v-if="error" class="q-mt-md">
        <q-banner class="text-white bg-red">
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          <div class="row items-center justify-between full-width">
            <span>{{ error }}</span>
            <q-btn 
              flat 
              color="white" 
              icon="close" 
              @click="error = ''"
              dense
              size="sm"
            />
          </div>
        </q-banner>
      </div>
      <!-- output per round -->
      <div v-if="messages.length > 0" class="q-mt-md">
        <q-chat-message :text="[messages[messages.length - 1].original]" sent />
        <p>
          情緒：{{ messages[messages.length - 1].emotion }}，
          分數：{{ messages[messages.length - 1].score }}
        </p>
      </div>
    </div>
    <!-- chart -->
    <div v-if="messages.length > 0" class="q-mt-lg">
      <div style="height: 600px; position: relative">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>

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
const error = ref('')

const radarChartCanvas = ref(null)
let radarChartInstance = null

async function evaluateEmotion() {

  error.value = ""

  const userInput = text.value.trim()
  if (!userInput) {
    error.value = "請輸入文字"
    return
  }
  loading.value = true
  try {
    const res = await analyzeEmotion(userInput)

    if (res.error) {
      console.error(res.message)
      error.value = "分析失敗分析失敗"
      return
    }

    const emotionText = res.response?.trim() || '無法判斷'

    messages.value.push({
      original: userInput,
      emotion: emotionText,
      score: emotionToScore(emotionText)
    })

    updateChart()
    updateRadarChart()
    text.value = ''
  } catch (err) {
    console.error('Emotion prediction failed:', err)
    error.value = '網路錯誤，請稍後再試'
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

function clearHistory() {
  messages.value = []
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  error.value = ''
}

// for radar chart

function getEmotionCounts() {
  const counts = {}
  const emotions = ["悲傷語調", "憤怒語調", "厭惡語調", "疑問語調", "平淡語氣", "驚奇語調", "開心語調", "關切語調"]
  
  emotions.forEach(emotion => counts[emotion] = 0)
  messages.value.forEach(msg => {
    if (Object.hasOwn(counts, msg.emotion)) {
      counts[msg.emotion]++
    }
  })
  
  return counts
}

function updateRadarChart() {
  const emotionCounts = getEmotionCounts()
  const labels = Object.keys(emotionCounts)
  const data = Object.values(emotionCounts)
  
  if (radarChartInstance) {
    radarChartInstance.destroy()
  }
  
  radarChartInstance = new Chart(radarChartCanvas.value, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: '情緒次數',
        data: data,
        backgroundColor: 'rgba(75, 180, 180, 0.2)',
        borderColor: 'rgba(75, 180, 180, 1)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          ticks: { stepSize: 1 }
        }
      }
    }
  })
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