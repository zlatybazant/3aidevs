import json
import os
import requests
from openai import OpenAI
from env import AIDEV3_API, REPORT_URL, ARXIV_URL, ARXIV_ART_URL, OPENAI_API_KEY
from file_processor import FileProcessor, ResultManager
from media_downloader import MediaDownloader
from web_content_scraper import WebContentScraper

endpoint = REPORT_URL
task = 'arxiv'
client = OpenAI(api_key=OPENAI_API_KEY)


def merge_json_files(captions_file: str, descriptions_file: str, output_file: str):
    # Load the JSON data from the files
    with open(captions_file, 'r', encoding='utf-8') as f:
        captions_data = json.load(f)

    with open(descriptions_file, 'r', encoding='utf-8') as f:
        descriptions_data = json.load(f)

    # Merge the JSON data
    merged_data = {}
    for filename in set(captions_data.keys()).union(descriptions_data.keys()):
        merged_data[filename] = {
            "caption": captions_data.get(filename, None),
            "description": descriptions_data.get(filename, None)
        }

    # Write the merged data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4, ensure_ascii=False)

    print(f"Merged data has been written to {output_file}")


def get_responses_from_openai(page_value, json_file_path, questions_file_path, api_key):
    # Load the JSON content from the specified file
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        json_content = json.load(json_file)

    # Read questions from the specified text file
    with open(questions_file_path, 'r', encoding='utf-8') as questions_file:
        questions_content = questions_file.read()

    # Split the questions into a list (assuming each question is on a new line)
    questions = questions_content.strip().split("\n")
    responses = {}

    # Iterate over each question and request an OpenAI completion
    for question in questions:
        # Extract question number and question text
        question_number, question_text = question.split('=')

        # Prepare the system prompt to get a short, single-sentence answer
        system_prompt = (
            "Provide a concise, single-sentence answer to the following question. "
            "Your response should be clear, direct, and no longer than one sentence. "
            "Focus on the most important information."
        )

        # Format the JSON content
        formatted_content = "\n\n".join([
            f"Image Name: {image_name}\n"
            f"Caption: {details.get('caption', 'No caption')}\n"
            f"Description:\n{details.get('description', 'No description')}"
            for image_name, details in json_content.items()
        ])

        # Prepare the user message
        user_message = {
            "content": page_value + "\n\n" + formatted_content + "\n\n" + question_text,
            "role": "user"
        }

        try:
            # Make a request to the OpenAI API
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    user_message
                ]
            )

            # Extract and store the response for the current question
            response_content = completion.choices[0].message.content.strip()

            # Ensure the response is a single sentence
            response_content = response_content.split('.')[0] + '.'

            responses[question_number] = response_content

        except Exception as e:
            print(f"An error occurred while processing question {
                  question_number}: {e}")
            responses[question_number] = str(e)

    return responses


def main():
    scraper = WebContentScraper(log_file='web_scraper.log')
    downloader = MediaDownloader(scraper.logger, scraper.timeout)

    try:
        url = ARXIV_ART_URL
        content = scraper.fetch_content(url)

        downloader.download_media(content)

    except Exception as e:
        print(f"Scraping error: {e}")

    api_key = OPENAI_API_KEY  # Replace with your actual API key
    processor = FileProcessor(
        api_key=api_key,
        default_text_model="gpt-4o",  # You can adjust the model
        default_audio_model="whisper-1",
        default_vision_model="gpt-4o-mini"
    )

    # Directory to process
    directory = "article_downloads"

    # Ensure directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist!")
        return

    # Get all files sorted by type
    print(f"\nScanning directory: {directory}")
    sorted_files = FileProcessor.sort_files_by_type(directory)

    # Print summary of found files
    print("\nFound files:")
    for file_type, files in sorted_files.items():
        if processor.is_supported_file_type(file_type):
            category = processor.get_file_category(file_type)
            print(f"{category.upper()} files ({file_type}): {len(files)} files")
        else:
            print(f"Unsupported files ({file_type}): {len(files)} files")

    # Confirm processing
    total_files = sum(len(files) for files in sorted_files.values())
    print(f"\nTotal files found: {total_files}")

    result_manager = ResultManager()
    proceed = input("\nDo you want to proceed with processing? (y/n): ")
    if proceed.lower() != 'y':
        print("Processing cancelled.")
        return

    try:
        print("\nStarting file processing...")
        results = result_manager.process_files(processor, sorted_files)

        # Print summary of processed files
        processed_count = len(results)
        print("\nProcessing complete!")
        print(f"Successfully processed: {processed_count} files")
        print(f"Results saved to: {result_manager.results_file}")

    except Exception as e:
        print(f"\nAn error occurred during processing: {e}")
        return

    # Example usage
    merge_json_files(
        captions_file="image_captions.json",
        descriptions_file="arxiv.json",
        output_file="merged_output.json"
    )

    json_file = 'merged_output.json'
    questions_file = 'arxiv.txt'

    page = content['text']

    responses = get_responses_from_openai(
        page, json_file, questions_file, api_key)
    for question_number, answer in responses.items():
        print(f"Question {question_number}: {answer}")

    answer = {
        "task": task,
        "apikey": AIDEV3_API,
        "answer": responses
    }
    response = requests.post(endpoint, json=answer)
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
