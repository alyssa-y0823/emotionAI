import axios from 'axios'
const SANDBOX_URL = "http://127.0.0.1:8010/invoke";

const AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN
import { emotionPrompt, tensionPrompt } from 'src/api/prompts.js'

export async function analyzeEmotionAndTension(userDialogue) {
  try {
    // first api call
    const emotionResponse = await axios.post(SANDBOX_URL,
      {
        instance_id: "111",
        developer_prompt: emotionPrompt,
        user_prompt: userDialogue,
        model_name: "gemini-2.5-flash",
        temperature: 0.6,
        history_steps: 15
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Function-Name": "emotion-classify",
          "X-Platform-ID": "123",
          "Authorization": `Bearer ${AUTH_TOKEN}`
        }
      }
    )

    // second api call
    const tensionResponse = await axios.post(SANDBOX_URL,
      {
        instance_id: "111",
        developer_prompt: tensionPrompt,
        user_prompt: userDialogue,
        model_name: "gemini-2.5-flash",
        temperature: 0.3, // lower temp
        history_steps: 15
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Function-Name": "tension-measure",
          "X-Platform-ID": "123",
          "Authorization": `Bearer ${AUTH_TOKEN}`
        }
      }
    )

    console.log('Emotion Response:', emotionResponse.data)
    console.log('Tension Response:', tensionResponse.data)

    return {
      emotion: emotionResponse.data,
      tension: tensionResponse.data,
      combined: {
        emotion_result: emotionResponse.data.response,
        tension_result: tensionResponse.data.response,
        timestamp: new Date().toISOString()
      }
    }
  } catch (error) {
    console.error("Error calling LLM sandbox:", error)
    throw new Error(error.response?.data?.detail || error.message || '網路錯誤')
  }
}

// Legacy function for backward compatibility
export async function analyzeEmotion(userDialogue) {
  const result = await analyzeEmotionAndTension(userDialogue)
  return result.emotion
}