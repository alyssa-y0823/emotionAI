import requests

url = "https://dev.telligentbiz.com/oauth2api/connect/token"

payload = "grant_type=client_credentials&client_id=client-credential&client_secret=123456&scope=internal"
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.json()["access_token"])