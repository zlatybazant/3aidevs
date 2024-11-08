import os
import json
from file_processor import FileProcessor, ResultManager
from media_downloader import MediaDownloader
from web_content_scraper import WebContentScraper
from dotenv import load_dotenv
from src.services.openai import OpenAIService
from tag_generator import KeywordExtractor
from endpoint_sender import EndpointSender

endpoint = os.getenv("REPORT_URL")
task = 'dokumenty'
url = os.getenv("ARXIV_ART_URL")
api_key = os.getenv("AIDEV3_API")

load_dotenv()
openai_client = OpenAIService()


def extract_persons_from_report(report_filename, report_tags):
    """
    Use OpenAI API to extract names of persons mentioned in the report tags.
    """
    prompt = f"Identify all persons mentioned in the content: {
        report_tags}"
    messages = [
        {"role": "system", "content": f"Extract names of persons from the provided keywords of file: {
            report_filename}."},
        {"role": "user", "content": prompt}
    ]

    completion = openai_client.text_completion(messages=messages)
    persons = [comp['content'] for comp in completion]
    return persons


def compare_persons_from_report_with_fact(fact_filename, fact_tags, person):
    """
    Use OpenAI API to compare extracted names of person to tags from facts.

    """
    prompt = f"Here are given keywords {
        fact_tags} and person description: {person}."

    messages = [
        {"role": "system", "content": f"For keyword tags in file: {
            fact_filename} estimate if are consistent with given person description."},
        {"role": "user", "content": prompt}
    ]

    completion = openai_client.text_completion(messages=messages)
    compare = [comp['content'] for comp in completion]
    return compare


def main():

    extractor = KeywordExtractor()
    processor = FileProcessor()
    directory = "./pliki_z_fabryki"
    output_file = "keywords.json"

    try:

        # Ensure directory exists
        # if not os.path.exists(directory):
        #    print(f"Directory '{directory}' does not exist!")

        # Get all files sorted by type
        print(f"\nScanning directory: {directory}")
        sorted_files = FileProcessor.sort_files_by_type(directory)

        # Print summary of found files
        print("\nFound files:")
        for file_type, files in sorted_files.items():
            if processor.is_supported_file_type(file_type):
                category = processor.get_file_category(file_type)
                print(f"{category.upper()} files ({
                      file_type}): {len(files)} files")

                if file_type in processor.supported_text_types:
                    print(f"Attempting to process files of type: {file_type}")
                    result, success = extractor.process_files(
                        directory, output_file)
                    if not success:
                        print("Keyword file already exists. Reading existing one.")
                        with open(output_file, 'r', encoding='utf-8') as file:
                            results = json.load(file)
                    else:
                        print(f"results: {results}")

                else:
                    print(f"Unsupported files ({file_type}): {
                          len(files)} files")

        print("========")
        persons_list = []
        answer = {}

        for result in results:
            filename = result['filename']

            if 'report' in filename:
                persons_field = result.get('persons', None)
                reportname = result['filename']
                person = result['persons']
                reportcontent = result['content']
                reportkeywords = result['tags']

                if persons_field is None or persons_field.lower() == 'none':
                    answer[reportname] = reportkeywords
                    continue
                # individual_names = [name.strip()
                #                    for name in persons_field.split(',')]
                # persons_list.extend(individual_names)

                for result in results:
                    filename = result['filename']
                    if 'f0' in filename:
                        factname = result['filename']
                        factcontent = result['content']
                        factskeywords = result['tags']

                        print("--------------")
                        # filenames = [result['filename']
                        # filenames_str = ', '.join(filenames)

                        system_prompt = f"""
                                   Here is a content of some fact documents.
                                   <metadata>
                                   {factcontent}
                                   </metadata>
                                   """
                        # Prepare the user message
                        user_message = f"""
                                   For received content check if it is related to person.
                                   Process steps:
                                   <process>
                                   1. Check does document says about one or more given personal data: {person}'.
                                   2. If related data found, output an answer only: 'True'
                                   3. In not found, output 'False' {person} | {factname} | {reportname}
                                   </process>
                                   """

                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ]

                        completion = openai_client.text_completion(
                            messages=messages)

                        for comp in completion:
                            print(f"{comp['role']}: {
                                comp['content']}")

                        if comp['content'] == 'True':
                            # Ensure reportkeywords and factskeywords are strings
                            reportkeywords_str = ''.join(reportkeywords) if isinstance(
                                reportkeywords, list) else reportkeywords
                            factskeywords_str = ''.join(factskeywords) if isinstance(
                                factskeywords, list) else factskeywords

                            # Merge the keywords with a separator
                            merged_keywords = ', '.join(
                                [reportkeywords_str, factskeywords_str])

                            # Assign the merged keywords to the answer dictionary
                            answer[reportname] = merged_keywords
        print(json.dumps(answer, indent=4))

    except Exception as e:
        print(f"main(): Code error: {e}")

    sender = EndpointSender(task=task, apikey=api_key, endpoint=endpoint)
    sender.send_answer(answer)


if __name__ == "__main__":
    main()
