from openai import OpenAI
import requests
import json
from env import AIDEV3_API, OPENAI_API_KEY, JSON_DATA, CENTRALA_URL

task = "JSON"
data = JSON_DATA
endpoint = CENTRALA_URL
filename = "dane.json"
client = OpenAI(api_key=OPENAI_API_KEY)
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x87_64; rv:109.0) Geckoe20100101 Firefox/119.0'
           }


def download_json_file(data, filename):
    try:
        response = requests.get(data, headers=headers, timeout=15)
        response.raise_for_status()
        with open(filename, 'w') as file:
            file.write(response.text)
        print("Download and save successful.")
    except requests.RequestException as e:
        print(f"Exception occurred during download: {e}")


def load_json_data(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Exception occured while loading JSON data: {e}")
        return None


def verify_and_correct_answers(data):
    if data is None:
        print("No data to process.")
        return

    correct_count = 0
    incorrect_count = 0
    for item in data.get('test-data', []):
        question = item.get('question')
        expected_answer = item.get('answer')

        try:
            correct_answer = eval(question)
        except (SyntaxError, NameError) as e:
            print(f"Error eval {question}: {e}")
            continue

        if expected_answer == correct_answer:
            correct_count += 1
            print(f"correct answer: {correct_answer} for {question}")
        else:
            incorrect_count += 1
            print(f"incorrect answer found '{expected_answer}' for question: {
                  question}. Expected: {correct_answer} ")
            item['answer'] = correct_answer

    print(f"\nSummary: {correct_count} correct, {incorrect_count} incorrect.")


def update_api_key(data, apikey):
    data['apikey'] = apikey
    return data


def solve_test_questions(data, openaikey):
    for item in data.get('test-data', []):
        test_data = item.get('test')
        if test_data and test_data.get('a') == '???':
            q = test_data.get('q')
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Answer short only on given question."},
                    {"role": "user", "content": q}
                ]
            )
            test_data['a'] = completion.choices[0].message.content.strip()
    return data


def save_json_data(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def main(data, filename, aidevApi, openaiApi):
    print("Script is running...")
    download_json_file(data, filename)
    data = load_json_data(filename)
    data = update_api_key(data, aidevApi)
    data = solve_test_questions(data, openaiApi)
    if data is not None:
        verify_and_correct_answers(data)
    save_json_data(data, filename)


main(data, filename, AIDEV3_API, OPENAI_API_KEY)

data = load_json_data(filename)
print(data)
answer = {
    "task": task,
    "apikey": AIDEV3_API,
    "answer": data
}
response = requests.post(endpoint, json=answer)
print(response.status_code)
print(response.text)
