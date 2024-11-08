import requests
from env import AIDEV3_API, POLIGON_URL, POLIGON_DATA

task = "POLIGON"
data = POLIGON_DATA
endpoint = POLIGON_URL

# Get TXT file
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'}
response = requests.get(data, headers=headers, timeout=15)

print(response.text)
table = []
strings = [line.strip() for line in response.text.split('\n') if line.strip()]
table = strings
print(table)
answer = {
    "task": task,
    "apikey": AIDEV3_API,
    "answer": table
}
response = requests.post(endpoint, json=answer)
print(response.status_code)
print(response.text)
