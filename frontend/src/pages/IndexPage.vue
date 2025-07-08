<template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        @keydown.enter.prevent="evaluateEmotion"
        outlined
      > </q-input>
      <q-btn
        label="Enter"
        color="primary"
        icon-right="send"
        class="q-mt-sm"
        @click="evaluateEmotion"
      > </q-btn>
       <div v-if="messages.length > 0">
        <q-chat-message :text="[messages[messages.length - 1].original]" sent />
        <p>情緒：{{ messages[messages.length - 1].emotion }}，
          信心度：{{ (messages[messages.length - 1].confidence * 100).toFixed(2) }}%，
          分數：{{ messages[messages.length - 1].score }}</p>
      </div>
    </div>
    <canvas ref="chartCanvas" style="margin-top: 20px;"></canvas>
  </q-page>
</template>


<script setup>
import { ref } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const text = ref('')
const messages = ref([]) // stores text, emotion, score

const chartCanvas = ref(null)
let chartInstance = null

// let total = ref(0)

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if (!userInput) return

  try {
    const result = await axios.post("http://localhost:8000/analyze", {
      texts: [userInput]
    })

    const data = result.data.results[0]

    messages.value.push({
      original: data.original,
      translated: data.translated,
      emotion: data.emotion,
      confidence: data.confidence,
      score: data.graph_score
    })

    updateChart()
    // updateTotal()
    // console.log("Total score:", total.value)
    text.value = ''
  } catch (err) {
    console.error('Emotion prediction failed:', err)
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

// function updateTotal() {
//   total.value = messages.value.reduce((sum, entry) => sum + entry.score, 0)
// }
</script>
