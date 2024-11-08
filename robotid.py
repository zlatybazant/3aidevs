from openai import OpenAI
from env import OPENAI_API_KEY, AIDEV3_API, CENTRALA_URL, ROBOTID_URL
import requests
import json

url = ROBOTID_URL
endpoint = CENTRALA_URL
task = "robotid"
client = OpenAI(api_key=OPENAI_API_KEY)


def fetch_robot_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        description = data['description']
        return description
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except KeyError as e:
        print(f"Error: Missing 'description' field in JSON data: {e}")
    return None


def completion_desc(desc):
    # Prepare prompt for DALE3

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "On given description of a object, prepare detailed prmpt for DALE-3 image generator."},
            {"role": "user", "content": desc}
        ]
    )
    return completion.choices[0].message.content


def dalle3_gen(prompt, api_key=OPENAI_API_KEY, size="1024x1024"):
    try:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(response.json())
        image_url = response.json()["data"][0]["url"]
        return image_url

    except requests.exceptions.RequestException as e:
        print(f"Error generating DALL-E image: {e}")
    except (KeyError, IndexError):
        print("Error: Invalid response from DALL-E API")
        return None


if __name__ == "__main__":
    url = url
    robot_desc = fetch_robot_data(url)
    print(robot_desc)
    prompt = completion_desc(robot_desc)
    print(prompt)
    image_url = dalle3_gen(prompt)
    print(image_url)

    answer = {
        "task": task,
        "apikey": AIDEV3_API,
        "answer": image_url
    }
    response = requests.post(endpoint, json=answer)
    print(response.status_code)
    print(response.text)
