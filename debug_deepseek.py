import requests

url = "http://localhost:9002/api/generate"

payload = {
    "prompt": "Analyze the codebase and provide a summary of what needs to be fixed.",
    "use_deepseek": True,
    "max_tokens": 1000
}

response = requests.post(url, json=payload)

if response.ok:
    print("Summary of code issues:")
    print(response.json())
else:
    print("Failed to get a response:", response.status_code, response.text)
