from ollama import Client
from env import AIDEV3_API, REPORT, CENZURA_URL
import requests

endpoint = REPORT
task = 'CENZURA'
url = CENZURA_URL
data = requests.get(url)
print(data.text)

oc = Client(host='http://localhost:11434')
system_rules = """Replace names in sentence with word 'CENZURA'.
Follow the rules:
<rules>
- replace last name
- replace name
- replace person's living address
- replace building number
- replace person's age
- do not add any comment
- rest of sentence leave as it is
</rules>
Example:
user: Tożsamość osoby: Jan Kowalski. Zamieszkały w Gdańsku przy ul. Głównej 2.\
Ma 43 lata.
assistant Tożsamość osoby: CENZURA. Zamieszkały w CENZURA przy ul. CENZURA.\
Ma CENZURA lata.
"""

messages = [
    {'role': 'system', 'content': system_rules},
    {'role': 'user', 'content': data.text},
    {'format': 'json'}
]
response = oc.chat(model='gemma2:2b', messages=messages,
                   options={'temperature': 0})
print(response)

answer = {
    "task": task,
    "apikey": AIDEV3_API,
    "answer": response['message']['content']
}
response = requests.post(endpoint, json=answer)
print(response.status_code)
print(response.text)
