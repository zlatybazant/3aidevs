# 1. Sort files in dictionary
# 2. Create OpenAI features calls in separate functions
# 3. Read dictionary with sorted types
# ==============================
import base64
from collections import defaultdict
import json
import os
from env import OPENAI_API_KEY, AIDEV3_API, REPORT_URL
from openai import OpenAI
import requests

endpoint = REPORT_URL
task = 'kategorie'
client = OpenAI(api_key=OPENAI_API_KEY)


def text_completion(file_path, model="gpt-4o", system="Process text file"):
    with open(file_path, 'r') as file:
        content = file.read()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content}
        ]
    )
    return completion.choices[0].message.content


def audio_completion(file_path, model="whisper-1"):
    with open(file_path, "rb") as file:
        transcript = client.audio.transcriptions.create(
            model=model,
            file=file,
            response_format="text"
        )
    return transcript


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def vision_request(image_path, model="gpt-4o-mini"):
    base64_image = encode_image(image_path)
    vision = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "What is in the image?"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"}},
            ]}
        ]
    )
    return vision.choices[0].message.content


def sort_file_by_type(directory):
    files_by_type = defaultdict(list)

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            # Get file extension
            _, file_exetension = os.path.splitext(filename)
            # Add file path to the corresponding file type lis,t
            files_by_type[file_exetension].append(file_path)

    return files_by_type


def load_existing_results(results_file):
    if os.path.exists(results_file):
        with open(results_file, 'r') as file:
            return json.load(file)
    return {}


def save_results(results, results_file):
    with open(results_file, 'w') as file:
        json.dump(results, file, indent=4)


def process_files(sorted_files, results_file="results.json"):
    results = load_existing_results(results_file)

    for file_type, paths in sorted_files.items():
        for file_path in paths:
            file_name = os.path.basename(file_path)

            if file_name in results:
                print(f"Skipping already processed file: {file_path}")
                continue
            try:
                if file_type == '.txt':
                    print(f"Processing text file: {file_path}")
                    result = text_completion(file_path)
                elif file_type == '.mp3':
                    print(f"Processing audio file: {file_path}")
                    result = audio_completion(file_path)
                elif file_type == '.png':
                    print(f"Processing image file: {file_path}")
                    result = vision_request(file_path)
                else:
                    print(f"Skipping unsupported file type: {file_type}")
                    continue

                results[file_name] = result
                print(f"Result saved for {file_path}")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    save_results(results, results_file)


system = """
You are a classification system that analyzes security reports and returns exactly one word
from these options: PEOPLE, NOBODY, HARDWARE, SOFTWARE, or OTHER.

Rules for classification:
- PEOPLE: Human individuals, rebels, intruders, specific named persons
- NOBODY: Reports indicating absence of people, empty locations
- HARDWARE: Physical equipment repairs, sensor issues, mechanical problems
- SOFTWARE: System updates, algorithm modifications, communication protocols
- OTHER: Reports not fitting above categories (e.g., environmental observations)

Additional Retrieval Instructions:

Please only retrieve notes containing information about:
1. Captured people or traces of their presence
2. Fixed hardware faults (ignore those related to software)

You must return only one of these words without any additional explanation.

Examples:
Input: "We searched the town for rebels and found no one."
Output: NOBODY

Input: "Barbara Zawadzka was identified near the alarm system."
Output: PEOPLE

Input: "Motion sensor had a short circuit due to mouse interference."
Output: HARDWARE

Input: "AI module updated with new motion analysis algorithms."
Output: SOFTWARE

Input: "Area remains calm. No activity detected."
Output: OTHER

Input: "We need pineapple pizza delivered. Our team's morale depends on it."
Output: OTHER

Input: "We found one guy hanging around the gate. He was tinkering with something
on the alarm equipment. He was arrested."
Output: PEOPLE

Please analyze the provided report and return only one word:
PEOPLE, NOBODY, HARDWARE, SOFTWARE, or OTHER.
"""


def process_results_for_prompt(results_file, model="gpt-4o", system=system):
    if not os.path.exists(results_file):
        print("Results file not found")
        return

    categorized_files = {
        "people": [],
        "hardware": []
    }

    with open(results_file) as file:
        results = json.load(file)

    for file_name, result in results.items():
        try:
            prompt = f"File: {file_name}\nContent:\n{
                result}\nProvide further analysis."
            print(f"Processing prompt for: {file_name}")

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            )

            category = completion.choices[0].message.content.strip().upper()
            print(f"AI output {
                  completion.choices[0].message.content} for {file_name}")

            if category == "PEOPLE":
                categorized_files["people"].append(file_name)
            elif category == "HARDWARE":
                categorized_files["hardware"].append(file_name)
            else:
                print(f"Unexpected category '{category}' for {file_name}")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    return categorized_files


def main():
    directory = './downloads/'
    sorted_files = sort_file_by_type(directory)
    process_files(sorted_files)
    categorized_results = process_results_for_prompt(
        results_file="results.json", model="gpt-4o", system=system)
    print("Categorized results:")
    print(json.dumps(categorized_results, indent=4))

    answer = {
        "task": task,
        "apikey": AIDEV3_API,
        "answer": categorized_results
    }
    response = requests.post(endpoint, json=answer)
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
