# file_processor.py

import base64
from collections import defaultdict
import json
import os
from typing import Dict, List, Optional, Set
import inspect
from src.services.openai import OpenAIService


VISION_PROMPTS = {
    "default": """
    You are a highly analytical image-processing assistant designed to analyze\
    base64-encoded images. Your task is to provide a detailed, structured, and\
    insightful analysis of each image, focusing on all visible elements and\
    their relationships.

    Output Structure:
        Overall Description: A concise summary of the image content.
        Detailed Element Breakdown: Analyze individual components, their\
        appearance, position, relationships, and significance in the image.
        Anomalies or Issues: Identify and describe any irregularities,\
        corruptions, or glitches in the image.
        Reasoning: Provide logical reasoning or contextual analysis to\
        explain the observed elements and their potential meaning.

    Corrupted Images:
        If the image is partially corrupted or contains glitches, attempt\
        to analyze the undamaged portions. Provide detailed notes on the \
        nature and extent of the corruption.
        If the image is fully unreadable, clearly state this along with\
        possible causes based on the data provided.

    Precision and Objectivity:
        Avoid speculation unless explicitly requested. Base your analysis\
        strictly on the image data.
        Be as comprehensive as possible without leaving out any observable\
        detail, no matter how minor.

    Your response must be structured, precise, and informative, aiming to\
    assist users in understanding every aspect of the image.
    """
}


class FileProcessor:
    """A class to process different types of files using OpenAI's APIs."""

    # Default supported file types
    SUPPORTED_TEXT_TYPES = {'.txt', '.md', '.log',
                            '.csv', '.rst', '.tex', '.doc', '.docx', '.pdf'}
    SUPPORTED_AUDIO_TYPES = {'.mp3', '.wav', '.m4a',
                             '.ogg', '.flac', '.aac', '.wma', '.aiff'}
    SUPPORTED_IMAGE_TYPES = {'.png', '.jpg', '.jpeg',
                             '.gif', '.webp', '.bmp', '.tiff', '.svg'}

    def __init__(
        self,
        default_text_model: str = "gpt-4o",
        default_audio_model: str = "whisper-1",
        default_vision_model: str = "gpt-4o",
        custom_text_types: Set[str] = None,
        custom_audio_types: Set[str] = None,
        custom_image_types: Set[str] = None
    ):
        """
        Initialize the FileProcessor with API credentials and custom file type support.

        Args:
            api_key: OpenAI API key
            default_text_model: Default model for text processing
            default_audio_model: Default model for audio processing
            default_vision_model: Default model for vision processing
            custom_text_types: Additional text file extensions to support
            custom_audio_types: Additional audio file extensions to support
            custom_image_types: Additional image file extensions to support
        """
        self.client = OpenAIService()
        self.default_text_model = default_text_model
        self.default_audio_model = default_audio_model
        self.default_vision_model = default_vision_model

        # Initialize supported types with defaults and any custom types
        self.supported_text_types = self.SUPPORTED_TEXT_TYPES | (
            custom_text_types or set())
        self.supported_audio_types = self.SUPPORTED_AUDIO_TYPES | (
            custom_audio_types or set())
        self.supported_image_types = self.SUPPORTED_IMAGE_TYPES | (
            custom_image_types or set())

    def is_supported_file_type(self, file_type: str) -> bool:
        """
        Check if the file type is supported.

        Args:
            file_type: File extension (e.g., '.txt', '.mp3')

        Returns:
            bool: True if the file type is supported
        """
        file_type = file_type.lower()
        return file_type in (
            self.supported_text_types |
            self.supported_audio_types |
            self.supported_image_types
        )

    def is_supported_file(self, file_path: str) -> bool:
        """
        Check if a specific file is supported based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if the file is supported
        """
        _, extension = os.path.splitext(file_path)
        return self.is_supported_file_type(extension.lower())

    def get_file_category(self, file_type: str) -> str:
        """
        Get the category of the file type.

        Args:
            file_type: File extension (e.g., '.txt', '.mp3')

        Returns:
            str: Category ('text', 'audio', 'image', or 'unsupported')
        """
        file_type = file_type.lower()
        if file_type in self.supported_text_types:
            return 'text'
        elif file_type in self.supported_audio_types:
            return 'audio'
        elif file_type in self.supported_image_types:
            return 'image'
        return 'unsupported'

    def get_supported_extensions(self, category: Optional[str] = None) -> Set[str]:
        """
        Get all supported file extensions, optionally filtered by category.

        Args:
            category: Optional category filter ('text', 'audio', 'image')

        Returns:
            Set of supported file extensions
        """
        if category == 'text':
            return self.supported_text_types
        elif category == 'audio':
            return self.supported_audio_types
        elif category == 'image':
            return self.supported_image_types
        return (
            self.supported_text_types |
            self.supported_audio_types |
            self.supported_image_types
        )

    def process_text(
        self,
        file_path: str,
        model: Optional[str] = None,
        system: str = "Process text file"
    ) -> str:
        """
        Process a text file using OpenAI's chat completion.

        Args:
            file_path: Path to the text file
            model: Optional model override
            system: System message for the chat completion

        Returns:
            Processed text content
        """
        if not self.is_supported_file(file_path):
            raise ValueError(f"Unsupported file type: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Use the OpenAIService to process the text
        completion = self.client.text_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content}
            ],
            model=model or self.default_text_model
        )
        return completion

    def process_audio(
        self,
        file_path: str,
        model: Optional[str] = None
    ) -> str:
        """
        Transcribe an audio file using OpenAI's whisper model.

        Args:
            file_path: Path to the audio file
            model: Optional model override

        Returns:
            Transcribed text
        """
        if not self.is_supported_file(file_path):
            raise ValueError(f"Unsupported file type: {file_path}")

        with open(file_path, "rb") as file:
            # Use the OpenAIService to transcribe the audio
            transcript = self.client.text_embedding(
                payload=file.read(),
                model=model or self.default_audio_model
            )
        return transcript

    @staticmethod
    def encode_image(image_path: str) -> str:
        """
        Encode an image file to base64.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    def process_vision(
        self,
        image_path: str,
        model: Optional[str] = None,
        prompt: str = VISION_PROMPTS["default"]
    ) -> str:
        """
        Process an image using OpenAI's vision model.

        Args:
            image_path: Path to the image file
            model: Optional model override
            prompt: Text prompt for the vision model

        Returns:
            Description of the image
        """
        if not self.is_supported_file(image_path):
            raise ValueError(f"Unsupported file type: {image_path}")

        base64_image = self.encode_image(image_path)
        # Use the OpenAIService to process the vision
        vision = self.client.text_completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": base64_image}
            ],
            model=model or self.default_vision_model
        )
        return vision

    @staticmethod
    def sort_files_by_type(directory: str) -> Dict[str, List[str]]:
        """
        Recursively sort files in a directory and its subdirectories by their extension.

        Args:
            directory: Directory path to scan

        Returns:
            Dictionary mapping file extensions to lists of file paths
        """
        files_by_type = defaultdict(list)
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                _, file_extension = os.path.splitext(filename)
                files_by_type[file_extension.lower()].append(file_path)
        return files_by_type


class ResultManager:
    """A class to manage processing results and their persistence."""

    def __init__(self, base_name: str = None, extension: str = "json"):
        """
        Initialize the ResultManager.

        Args:
            base_name: Base name for the results file (without extension).
                      If None, uses the calling script name.
            extension: File extension for the results file
        """
        if base_name is None:
            frame = inspect.stack()[1]
            calling_script = frame[0].f_code.co_filename
            base_name = os.path.splitext(os.path.basename(calling_script))[0]

        self.results_file = f"{base_name}.{extension}"

    def load_results(self) -> Dict:
        """Load existing results from the JSON file."""
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as file:
                return json.load(file)
        return {}

    def save_results(self, results: Dict):
        """Save results to the JSON file."""
        with open(self.results_file, 'w') as file:
            json.dump(results, file, indent=4)

    def process_files(
        self,
        processor: FileProcessor,
        sorted_files: Dict[str, List[str]]
    ) -> Dict:
        """
        Process files using the FileProcessor and manage results.

        Args:
            processor: FileProcessor instance
            sorted_files: Dictionary of files sorted by type

        Returns:
            Dictionary of processing results
        """
        results = self.load_results()

        for file_type, paths in sorted_files.items():
            file_type = file_type.lower()

            if not processor.is_supported_file_type(file_type):
                print(f"Skipping unsupported file type: {file_type}")
                continue

            for file_path in paths:
                file_name = os.path.basename(file_path)

                if file_name in results:
                    print(f"Skipping already processed file: {file_path}")
                    continue

                try:
                    category = processor.get_file_category(file_type)
                    print(f"Processing {category} file: {file_path}")

                    if category == 'text':
                        result = processor.process_text(file_path)
                    elif category == 'audio':
                        result = processor.process_audio(file_path)
                    elif category == 'image':
                        result = processor.process_vision(file_path)
                        print(f"image_result: {result}")
                    else:
                        continue

                    results[file_name] = result
                    print(f"results_before_save: {results[file_name]}")
                    print(f"Result saved for {file_path}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

        self.save_results(results)
        return results
