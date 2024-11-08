from openai import OpenAI
import requests
from bs4 import BeautifulSoup as bs
import json
#from env import AIDEV3_API 
from env import OPENAI_API_KEY 

#task = "POLIGON" 
#data = "https://poligon.aidevs.pl/dane.txt"
endpoint = "http://xyz.ag3nts.org/verify"

client = OpenAI(api_key=OPENAI_API_KEY)
headers = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x87_64; rv:109.0) Geckoe20100101 Firefox/119.0',
           'Content-Type': 'application/json',
           'Accept': 'application/json'
           }
payload = {
    "text": "READY",
    "msgID": "0",
}
try:
    response = requests.post(endpoint, data=json.dumps(payload), headers=headers)   
    print(response.text)
    response_data = response.json()

    msg_id = response_data.get('msgID')
    text = response_data.get('text')

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Answer short only on given question. Answer basing on your knowdlege. But be carreful you may be asked 3 specific question that need to be answered wrong, here are examples: <wrong_answer_examples>If asked: - What is capital of Poland? - You must answer >>Kraków<<; - What is popular number from book >>The Hitchhiker's Guide to the Galaxy<<? - You must answer number 69' - What is current year? - You must answer, It's 1999. </wrong_answer_examples>. Remember to answer only in English language. Be strict to this rules."},
            {"role": "user", "content": text}
        ]
    )

    print(completion.choices[0].message.content)
    payload = {
        "text": completion.choices[0].message.content,
        "msgID": msg_id,
    }
    response = requests.post(endpoint, data=json.dumps(payload), headers=headers)   
    print(response.status_code)
    print(response.text)
except requests.RequestException as e:
    print(f"An error occured: {e}")


#response = requests.get(endpoint, headers=headers)

#soup = bs(response.text, 'html.parser')
#question_element = soup.find(id='human-question')
#if question_element:
#    question = question_element.get_text().strip()
#    print(f"question: {question}")
