# taq_generator.py
import uuid
import os
import json
from file_processor import FileProcessor
from src.services.openai import OpenAIService


class KeywordExtractor:
    def __init__(self):
        """
        Initialize the KeywordExtractor with the OpenAI API key.

        :param api_key: OpenAI API key
        """
        self.openai_client = OpenAIService()
        self.system_prompt = "Extract important keywords from the following\
        text. Return words in denominator form separated with comma."

    def get_keywords_from_openai(self, content: str) -> str:
        """
        Use OpenAI to extract important keywords from the given content.

        :param content: The content of the file
        :return: Extracted keywords
        """
        try:
            # Prepare the messages for the OpenAI API
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content}
            ]

            # Call the text_completion method from OpenAIService
            completion = self.openai_client.text_completion(messages)

            # Extract and return the response for the current content
            # Assuming the completion returns a list of OpenAIMessage
            keywords = "\n".join([msg['content'] for msg in completion])
            return keywords

        except Exception as e:
            print(
                f"An error occurred while processing 'keywords' request: {e}")
            return ""

    def get_persons_from_content(self, content: str) -> str:
        """
        Use OpenAI to extract important persons from the given content.

        :param content: The content of the file
        :return: Extracted persons
        """

        try:
            messages = [
                {"role": "system",
                 "content": """
                 Your task is to identify only persons names for givent content.
                 Follow rules:
                 1. Extract names of persons and separate names with comma.
                 2. Output only names.
                 3. If there is no identified persons type 'None'.
                 4. If there is misspelling in name, choose that which occurs more often. 
                 5. Output only full name. Do not duplicate names or similar sounded.
                 """},
                {"role": "user", "content": content}
            ]
            completion = self.openai_client.text_completion(messages)
            persons = "\n".join([msg['content'] for msg in completion])
            return persons

        except Exception as e:
            print(
                f"An error occurred while processing 'persons' request: {e}")
            return ""

    def save_keywords_to_json(self, results: list, output_file: str):
        """
        Save the extracted keywords to a JSON file.

        :param results: List of dictionaries with filename and tags
        :param output_file: The output JSON file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

    def process_files(self, directory: str, output_file: str):
        """
        Process .txt and .md files in the given directory to extract keywords.

        :param directory: Directory path to scan
        :param output_file: The output JSON file path
        :return: A tuple containing the results and a boolean indicating success
        """
        try:
            # Check if output file already exists
            if os.path.exists(output_file):
                print(f"Output file '{
                      output_file}' already exists. Skipping processing.")
                return [], False

            # Ensure directory exists
            if not os.path.exists(directory):
                print(f"Directory '{directory}' does not exist!")
                return [], False

            # Get all files sorted by type
            print(f"\nScanning directory: {directory}")
            sorted_files = FileProcessor.sort_files_by_type(directory)

            # Process .txt and .md files
            results = []
            for file_type in ['.txt', '.md']:
                files = sorted_files.get(file_type, [])
                for file_path in files:
                    print(f"\nProcessing file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                    file_name_split = os.path.basename(file_path).replace(
                        '_', ' ').replace('-', ' ').rsplit('.', 1)[0]

                    # Get keywords from OpenAI
                    keywords = self.get_keywords_from_openai(content)
                    persons = self.get_persons_from_content(content)

                    results.append({
                        "filename": os.path.basename(file_path),
                        "content": f"{content}",
                        "tags": f"{keywords}, {file_name_split}",
                        "persons": f"{persons}",
                        "uuid": str(uuid.uuid4())
                    })

            # Save results to JSON
            self.save_keywords_to_json(results, output_file)
            print(f"Keywords saved to {output_file}")

            return results, True

        except Exception as e:
            print(f"Code error: {e}")
            return [], False
