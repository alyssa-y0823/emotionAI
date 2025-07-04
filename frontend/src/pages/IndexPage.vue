<template>
  <q-page class="q-mb-md">
    <div style="max-width: 600px; width: 100%">
      <q-input
        v-model="text"
        label="請輸入文字"
        autogrow
        type="textarea"
        @keydown.enter="evaluateEmotion"
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
        <q-chat-message :text="[text]" sent />
        <p>情緒：{{ messages[messages.length-1].label }}，分數：{{ messages[messages.length-1].score }}</p>
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
const messages = ref([]) // stores text, label, score

const chartCanvas = ref(null)
let chartInstance = null

async function evaluateEmotion() {
  const userInput = text.value.trim()
  if(!userInput)
    return
  const result = await axios.post("http://localhost:8000/predict", {
    text: userInput
  })
  console.log('Received from backend:', result.data)

  try {
      // add to messages array
      messages.value.push({
        text: userInput,
        label: result.data.label,
        score: result.data.score
      })
      if (!chartCanvas.value) {
        console.error('Chart canvas is not available')
        return
      }
      updateChart()
      text.value = ''
    } catch (err) {
      console.error('Emotion prediction failed:', err)
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
</script>