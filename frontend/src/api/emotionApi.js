import axios from 'axios'
const SANDBOX_URL = "http://127.0.0.1:8010/invoke";

const AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN

export async function analyzeEmotion(userDialogue) {
  try {
    console.log("AUTH_TOKEN:", AUTH_TOKEN)
    const response = await axios.post(
      SANDBOX_URL,
      {
        instance_id: "111",
        developer_prompt:
          "請只針對整段輸入判斷一次語氣，從以下情緒中選擇最貼近的一項回覆：「悲傷語調」、「憤怒語調」、「驚奇語調」、「關切語調」、「開心語調」、「平淡語氣」、「疑問語調」、「厭惡語調」、「無法判斷」。請只輸出情緒詞，勿重複、勿補充說明。",
        user_prompt: userDialogue,
        model_name: "gemini-2.5-flash",
        temperature: 0.6,
        // history_steps: "all"
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Function-Name": "test",
          "X-Platform-ID": "123",
          "Authorization": `Bearer ${AUTH_TOKEN}`
        }
      }
    )

    return response.data // response.response is the LLM's output
  } catch (error) {
    console.error("Error calling LLM sandbox:", error)
    return {
      error: true,
      message: error.response?.data?.detail || error.message
    }
  }
}