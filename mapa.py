from openai import OpenAI
from env import OPENAI_API_KEY
import os
import base64
import json

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to encode the images


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Path to images
image_dir = "./mapa_kawalki/"

output_file = "vision_response.json"

if os.path.exists(output_file):
    try:
        with open(output_file, "r") as json_file:
            data = json.load(json_file)
        print(f"Exisiting valid JSON file found: {output_file}")
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"JSON file {output_file} is corrupted or unreadableg")
        data = {}

else:
    data = {}

responses_updated = False
for filename in os.listdir(image_dir):
    file_path = os.path.join(image_dir, filename)
    if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        if filename in data:
            print(f"Skipping already processed image: {filename}")
            continue

        print(f"Processing image: {filename}")
        base64_image = encode_image(file_path)
        message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "You received a piece of map or a letter with a secret code. Can you recognize it the city by its fragment? Can you recognize codeauuu"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=message
        )

        response_data = (
            response.choices[0].to_dict() if hasattr(
                response.choices[0], 'to_dict') else response.choices[0]
        )

        data[filename] = response_data
        responses_updated = True

        print(f"vision response for {filename}: {response.choices[0]}")

if responses_updated:
    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"All vision responses saved to {output_file}")
else:
    print("No new images to process. JSON file remains unchanged.")

print("Moving to analyse...")
with open("vision_response.json", "r") as json_file:
    data = json.load(json_file)

previous_analyses = [item["message"]["content"] for item in data.values()]

hints = """* miasto posiada spichlerze * miasto posiada twierdzę"""

prompt = f"""Based on the following analyses of map fragments: 
{chr(10).join(f"Fragment {i+1}: {analysis}" for i,
              analysis in enumerate(previous_analyses))}
And considering these additional hints about the city: {hints}
Which city do you think these map fragments are from? Please explain your reasoning.
Think outloud."""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print("Final Analysis:")
print(response.choices[0].message.content)
