<template>
  <q-page class="q-mb-md">
    <div style="max-width: 800px; width: 100%">
      <div class="row q-gutter-sm">
        <!-- TEXT BOX  -->
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
        <!-- ENTER BUTTON -->
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
        <!-- DELETE BUTTON -->
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
      <!-- LOADING -->
      <div v-if="loading" class="row justify-center q-mt-sm">
        <q-spinner-dots color="primary" size="24px" />
        <span class="q-ml-sm">分析中...</span>
      </div>
      <!-- ERROR MESSAGE -->
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
      <!-- OUTPUT PER ROUND -->
      <div v-if="messages.length > 0" class="q-mt-md">
        <q-chat-message :text="[messages[messages.length - 1].original]" sent />
        <div class="q-mt-sm">
          <p class="q-mb-xs">
            <strong>情緒：</strong>{{ messages[messages.length - 1].emotion }}
          </p>
          <p class="q-mb-xs">
            <strong>Tension：</strong>{{ messages[messages.length - 1].tensionScore }}
          </p>
          <div class="text-caption text-grey-6">
            <p class="q-mb-none">修飾詞：{{ messages[messages.length - 1].modifier }} | 
            成語：{{ messages[messages.length - 1].idiom }} | 
            程度詞：{{ messages[messages.length - 1].degreeHead }} | 
            詞數：{{ messages[messages.length - 1].wordCount }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- RADAR CHART -->
    <div v-if="messages.length > 0" class="q-mt-lg" style="width: 550px; height: 550px;">
      <q-card class="full-height">
        <q-card-section class="q-pa-sm">
          <div class="text-subtitle2 text-center q-mb-xs">情緒分佈</div>
          <div style="height: 500px; position: relative;">
            <canvas ref="radarChartCanvas"></canvas>
          </div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { analyzeEmotionAndTension } from 'src/api/emotionApi'
import Chart from 'chart.js/auto'

const text = ref('')
const messages = ref([]) // stores text, emotion, tensionScore, modifier, idiom, degreeHead, wordCount

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
    const res = await analyzeEmotionAndTension(userInput)
    console.log('Raw API response:', res)

    if (res.error || !res.emotion || !res.tension) {
      console.error('API response error:', res)
      error.value = "分析失敗：無法獲得完整分析結果"
      return
    }

    const emotionResponse = res.emotion.response?.trim() || ''
    const emotion = parseEmotionResponse(emotionResponse)

    const tensionResponse = res.tension.response?.trim() || ''
    const tensionData = parseTensionResponse(tensionResponse)

    if (emotion === 'ERROR' || tensionData.tension === 'ERROR') {
      error.value = "分析失敗：解析回應時發生錯誤"
      return
    }

    const messageData = {
      original: userInput,
      emotion: emotion,
      tensionScore: tensionData.tension,
      modifier: tensionData.modifier,
      idiom: tensionData.idiom,
      degreeHead: tensionData.degreeHead,
      wordCount: tensionData.wordCount,
      timestamp: new Date()
    }

    messages.value.push(messageData)
    console.log('Messages after push:', messages.value)
    
    text.value = ''
    
    await nextTick()
    setTimeout(() => {
      updateRadarChart()
    }, 100)
    
  } catch (err) {
    console.error('Emotion prediction failed:', err)
    error.value = '網路錯誤，請稍後再試'
  } finally {
    loading.value = false
  }
}

function parseEmotionResponse(response) {
  if (!response) return 'ERROR'
  
  const match = response.match(/情緒[：:]\s*([^：:\n\r]+)/)
  if (match) {
    return match[1].trim()
  }
  
  const emotions = ['憤怒', '期待', '厭惡', '恐懼', '喜悅', '悲傷', '驚奇', '信任']
  for (const emotion of emotions) {
    if (response.includes(emotion)) {
      return emotion
    }
  }
  
  return 'ERROR'
}

function parseTensionResponse(response) {
  if (!response) {
    return { modifier: 'ERROR', idiom: 'ERROR', degreeHead: 'ERROR', wordCount: 'ERROR', tension: 'ERROR' }
  }
  
  const result = {}
  
  const patterns = {
    modifier: /Modifier[：:]\s*(\d+)/,
    idiom: /Idiom[：:]\s*(\d+)/,
    degreeHead: /DegreeHead[：:]\s*(\d+)/,
    wordCount: /WordCount[：:]\s*(\d+)/,
    tension: /Tension[：:]\s*([\d.]+)/
  }
  
  for (const [key, pattern] of Object.entries(patterns)) {
    const match = response.match(pattern)
    if (match) {
      if (key === 'tension') {
        result[key] = parseFloat(match[1])
      } else {
        result[key] = parseInt(match[1])
      }
    } else {
      result[key] = 'ERROR'
    }
  }
  
  return result
}

function clearHistory() {
  messages.value = []
  if (radarChartInstance) {
    radarChartInstance.destroy()
    radarChartInstance = null
  }
  error.value = ''
}

function getWeightedEmotionScores() {
  const scores = {}
  const emotions = ["憤怒", "期待", "厭惡", "恐懼", "喜悅", "悲傷", "驚奇", "信任"]

  emotions.forEach(emotion => scores[emotion] = 0)

  messages.value.forEach(msg => {
    if (Object.hasOwn(scores, msg.emotion) && typeof msg.tensionScore === 'number' && !isNaN(msg.tensionScore)) {
      scores[msg.emotion] += msg.tensionScore
    }
  })

  return scores
}

function updateRadarChart() {
  if (!radarChartCanvas.value) {
    console.error('Radar chart canvas not found')
    return
  }

  const weightedScores = getWeightedEmotionScores()
  
  if (Object.keys(weightedScores).length === 0) {
    console.log('No valid emotion data to display')
    return
  }
  
  const labels = Object.keys(weightedScores)
  const data = Object.values(weightedScores)
  
  console.log('Chart data:', { labels, data })
  
  const maxValue = Math.max(...data)
  const suggestedMax = maxValue > 0 ? Math.ceil(maxValue * 1.2) : 1
  
  if (radarChartInstance) {
    radarChartInstance.destroy()
    radarChartInstance = null
  }
  
  try {
    radarChartInstance = new Chart(radarChartCanvas.value, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [{
          data: data,  
          backgroundColor: 'rgba(75, 180, 180, 0.2)',
          borderColor: 'rgba(75, 180, 180, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(75, 180, 180, 1)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const emotion = context.label
                const score = context.parsed.r.toFixed(3)
                const count = messages.value.filter(msg => msg.emotion === emotion).length
                return `${emotion}: ${score} (${count}次)`
              }
            }
          }
        },
        scales: {
          r: {
            beginAtZero: true,
            suggestedMax: suggestedMax,
            ticks: {
              stepSize: suggestedMax / 5,
              color: '#666',
              callback: function(value) {
                return value.toFixed(2)
              }
            },
            pointLabels: {
              font: {
                size: 12
              }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        },
        animation: {
          onComplete: function() {
            console.log('Chart animation completed')
          }
        }
      }
    })
    
    console.log('Chart created successfully')
  } catch (error) {
    console.error('Error creating chart:', error)
  }
}
</script>