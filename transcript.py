from openai import OpenAI
from env import OPENAI_API_KEY, AIDEV3_API, REPORT
import os
import re
import requests

task = "mp3"
endpoint = REPORT
client = OpenAI(api_key=OPENAI_API_KEY)
audio_dir = "./przesluchania"
transcript_memory = []

for filename in os.listdir(audio_dir):
    if filename.endswith(".m4a"):
        file_path = os.path.join(audio_dir, filename)
        print(file_path)

        txt_filename = f"{os.path.splitext(filename)[0]}.txt"
        txt_path = os.path.join(audio_dir, txt_filename)

        if os.path.exists(txt_path):
            with open(txt_path, "r") as txt_file:
                transcript = txt_file.read()
                transcript_memory.append(
                    {"filename": filename, "transcription": transcript})
            print(f"Transcript loaded from {txt_filename}")

        else:
            with open(file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                with open(txt_path, "w") as txt_file:
                    txt_file.write(transcript)

                transcript_memory.append(
                    {"filename": filename, "transcription": transcript})

                print(f"Transcription saved for {filename} as {txt_filename}")

print("\nTranscript Memory:", transcript_memory)
question = "Na jakiej ulicy znajduje się instytut uczelni, na której wykłada Andrzej Maj?"

transcriptions_text = "\n".join(
    f"- {entry['filename']}: {entry['transcription']}" for entry in transcript_memory
)

prompt = f"""
You are analyzing witness testimonies to answer the question: "{question}"

The testimonies may contain contradictions, errors, and unusual responses.
Although no specific street name appears in the transcription,
use your knowledge to determine the correct answer.

Here are the testimonies:

{transcriptions_text}

Please reason through the statements in the transcriptions,
using any relevant knowledge about universities in Poland.
Think out loud to reconcile any inconsistencies, and arrive at the best possible answer.
At the end, put the street answer into this format: {{"answer": "name_of_street"}}.
"""

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": f"You are an assistant solving a game riddle involving witness testimonies and logical deduction."},
        {"role": "user", "content": prompt}
    ]
)

print(completion.choices[0].message.content)

match = re.search(r'{"answer":\s*"([^"]+)"}',
                  completion.choices[0].message.content)
if match:
    street_name = match.group(1)
else:
    street_name = None

print(street_name)

answer = {
    "task": task,
    "apikey": AIDEV3_API,
    "answer": street_name
}
response = requests.post(endpoint, json=answer)
print(response.status_code)
print(response.text)
