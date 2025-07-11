import axios from 'axios'

const SANDBOX_URL = "http://127.0.0.1:8010/invoke";

export async function analyzeEmotion(userDialogue) {
  try {
    
    const response = await axios.post(
      SANDBOX_URL,
      {
        instance_id: "111",
        developer_prompt:
          "請逐句分析客戶語氣，從以下情緒中選擇一項回覆：「悲傷語調」、「憤怒語調」、「驚奇語調」、「關切語調」、「開心語調」、「平淡語氣」、「疑問語調」、「厭惡語調」、「無法判斷」。請以每行一句的格式輸出。\n\n${dialogue}",
        user_prompt: userDialogue,
        model_name: "gpt-4.1", // gpt-4.1 ; gpt-4o-mini ; gemini-2.5-flash
        temperature: 0.7,
        // history_steps: "all"
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Function-Name": "test",
          "X-Platform-ID": "123",
          "Authorization": `Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQxNDkwODJGOTFCOUY0RDNERjkwN0YzNDA4NDhDRENBNTNFOTAzOUIiLCJ4NXQiOiJRVWtJTDVHNTlOUGZrSDgwQ0VqTnlsUHBBNXMiLCJ0eXAiOiJhdCtqd3QifQ.eyJzdWIiOiJjbGllbnQtY3JlZGVudGlhbCIsIm5hbWUiOiJNMk0iLCJyb2xlIjoiU3VwZXJBZG1pbmlzdHJhdG9yIiwib2lfcHJzdCI6ImNsaWVudC1jcmVkZW50aWFsIiwiY2xpZW50X2lkIjoiY2xpZW50LWNyZWRlbnRpYWwiLCJvaV90a25faWQiOiIwOGRkYmY3OS04MzIzLTRmNzQtOGE0Mi1mYmM0NGUzMTFhNDgiLCJzY29wZSI6ImludGVybmFsIiwianRpIjoiMzgxODgyNjQtNDI2My00ZWM0LWFlMzItMDdmYWYzYTcyNDE2IiwiZXhwIjoxNzUyMTMxODc2LCJpc3MiOiJodHRwczovL2Rldi50ZWxsaWdlbnRiaXouY29tL29hdXRoMmFwaS8iLCJpYXQiOjE3NTIxMjgyNzZ9.r3N1LIKv_hxe1a8vM-8j5GYKue3xq1vGEMrqGMwYICO3kzLTpZKfkUgQ-iTxp2EKTgKy4viNS6PCiKt4QJ03jbGltaJuemQih_9Ty3YRxkbclTq8nyynB_q5ahVioKNAiTOm8DSmD7Sut281ooI5Gv8rUrA-egnCfZh9v-Ixz6s--cA6mysdn0sYzVQntP88ktXqx5MaG4NoNkcwxORjyjbQxLndDjTQZp1nUNeG_edUMKdnUG5nsEWeWh_ILA395MBfODzQeeFmrQ8SHBg5__bY4NtbnwjFvGiLNYhhxKVvS4hJKn0GQyA68tM-919Hnbb1wCRTGz4V3YhXL5HINQ`
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
