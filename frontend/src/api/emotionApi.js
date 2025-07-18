import axios from 'axios'

const SANDBOX_URL = "http://127.0.0.1:8010/invoke";

export async function analyzeEmotion(userDialogue) {
  try {
    const response = await axios.post(
      SANDBOX_URL,
      {
        instance_id: "111",
        developer_prompt:
          "請逐句分析客戶語氣，從以下情緒中選擇一項回覆：「悲傷語調」、「憤怒語調」、「驚奇語調」、「關切語調」、「開心語調」、「平淡語氣」、「疑問語調」、「厭惡語調」、「無法判斷」。請以每行一句的格式輸出。",
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
          "Authorization": `Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQxNDkwODJGOTFCOUY0RDNERjkwN0YzNDA4NDhDRENBNTNFOTAzOUIiLCJ4NXQiOiJRVWtJTDVHNTlOUGZrSDgwQ0VqTnlsUHBBNXMiLCJ0eXAiOiJhdCtqd3QifQ.eyJzdWIiOiJjbGllbnQtY3JlZGVudGlhbCIsIm5hbWUiOiJNMk0iLCJyb2xlIjoiU3VwZXJBZG1pbmlzdHJhdG9yIiwib2lfcHJzdCI6ImNsaWVudC1jcmVkZW50aWFsIiwiY2xpZW50X2lkIjoiY2xpZW50LWNyZWRlbnRpYWwiLCJvaV90a25faWQiOiIwOGRkYzRkOS04ZDgwLTRlMjEtODQ2Yi0wMTYyNWIzMTNhOTEiLCJzY29wZSI6ImludGVybmFsIiwianRpIjoiOGY3N2MwNTUtZjk0Zi00NDk3LWFjZTMtMmVlNDUxMmNiMGVlIiwiZXhwIjoxNzUyNzIyODgxLCJpc3MiOiJodHRwczovL2Rldi50ZWxsaWdlbnRiaXouY29tL29hdXRoMmFwaS8iLCJpYXQiOjE3NTI3MTkyODF9.KZxuQVBJEZZhmy_X534ESG33SbybeILtboJS-BTlzEvARkw6vRekiha0IAhfQp8aF1YF98emfDh82wH2sPx7pEAAy7Z9yjDGwYeGU1ytpjnr2CtTo5R_LevOXv1otbK_B9yxvghpUGmfJGRQfAt8plEtlfy5TfBP7p0Id0Q2pengFDK_3SgfxrF2DgS3SuipN-3D8wzAK0hheA4c0r_uE7ZC61-vL8rGPcvO4lwPb3SeOk9Gk-sJDB_yy1amZPVXJp-2NQ12nUBep3ABvjFrSCGoPCfmajF2_8jEr5sbxPsNlVGl_SnRxKl82tD6s6vZLXSw4PoOPM6j86YBl_hTcQ`
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
