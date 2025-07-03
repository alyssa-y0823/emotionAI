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