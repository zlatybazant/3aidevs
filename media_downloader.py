import os
import requests
from pathlib import Path
from typing import Dict, Any
import logging
import json
from datetime import datetime
from urllib.parse import unquote, urlparse


class MediaDownloader:
    def __init__(self, logger: logging.Logger, timeout: int = 18):
        self.logger = logger
        self.timeout = timeout

    def _get_safe_filename(self, url: str, index: int, media_type: str) -> str:
        parsed_url = urlparse(unquote(url))
        original_filename = os.path.basename(parsed_url.path)
        filename = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext_map = {
                'image': '.png',
                'audio': '.mp3',
                'link': '.txt'
            }
            ext = ext_map.get(media_type, '.bin')
        safe_filename = f"{filename}{ext}"
        return safe_filename

    def download_media(self, content_dict: Dict[str, Any], download_path: str = './article_downloads') -> None:
        Path(download_path).mkdir(parents=True, exist_ok=True)
        captions_dict = {}

        for media_type in ['audio', 'links']:
            urls = content_dict.get(media_type, [])
            if isinstance(urls, str):
                urls = [urls] if urls else []

            self.logger.info(f"Processing {len(urls)} {media_type}")

            for i, media_url in enumerate(urls):
                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        media_type[:-1]
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        images = content_dict.get('images', [])
        if images:
            self.logger.info(f"Processing {len(images)} images with captions")

            for i, image_data in enumerate(images):
                if not isinstance(image_data, dict):
                    self.logger.warning(
                        f"Skipping invalid image data: {image_data}")
                    continue

                media_url = image_data.get('url')
                caption = image_data.get('caption')

                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        'image'
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    captions_dict[safe_filename] = caption or 'No caption available'

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")
                    if caption:
                        self.logger.info(f"Saved caption for {safe_filename}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        if captions_dict:
            captions_path = os.path.join('./', 'image_captions.json')
            try:
                with open(captions_path, 'w', encoding='utf-8') as f:
                    json.dump(captions_dict, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Captions saved to {captions_path}")
            except Exception as e:
                self.logger.error(f"Error saving captions to JSON: {e}")

            captions_file = os.path.join('./', 'captions.txt')
            with open(captions_file, 'a', encoding='utf-8') as caption_file:
                caption_file.write(f"\nDownloaded on: {
                                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                caption_file.write("-" * 50 + "\n")

                for i, image_data in enumerate(images):
                    if not isinstance(image_data, dict):
                        self.logger.warning(
                            f"Skipping invalid image data: {image_data}")
                        continue

                    media_url = image_data.get('url')
                    caption = image_data.get('caption')

                    if not media_url:
                        continue

                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(
                            media_url,
                            timeout=self.timeout,
                            headers=headers,
                            stream=True
                        )
                        response.raise_for_status()

                        safe_filename = self._get_safe_filename(
                            media_url,
                            i,
                            'image'
                        )
                        full_path = os.path.join(download_path, safe_filename)

                        with open(full_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        caption_entry = f"Image: {safe_filename}\n"
                        if caption:
                            caption_entry += f"Caption: {caption}\n"
                        else:
                            caption_entry += "Caption: No caption available\n"
                        caption_entry += "-" * 30 + "\n"
                        caption_file.write(caption_entry)

                        self.logger.info(f"Successfully downloaded {
                                         media_url} to {full_path}")
                        if caption:
                            self.logger.info(
                                f"Saved caption for {safe_filename}")

                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"Network error downloading {
                                          media_url}: {str(e)}")
                    except IOError as e:
                        self.logger.error(
                            f"File I/O error saving {media_url}: {str(e)}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error downloading {
                                          media_url}: {str(e)}")


class MediaDownloader:
    def __init__(self, logger: logging.Logger, timeout: int = 10):
        self.logger = logger
        self.timeout = timeout

    def _get_safe_filename(self, url: str, index: int, media_type: str) -> str:
        parsed_url = urlparse(unquote(url))
        original_filename = os.path.basename(parsed_url.path)
        filename = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext_map = {
                'image': '.png',
                'audio': '.mp3',
                'link': '.txt'
            }
            ext = ext_map.get(media_type, '.bin')
        safe_filename = f"{filename}{ext}"
        return safe_filename

    def download_media(self, content_dict: Dict[str, Any], download_path: str = './article_downloads') -> None:
        Path(download_path).mkdir(parents=True, exist_ok=True)
        captions_dict = {}

        for media_type in ['audio', 'links']:
            urls = content_dict.get(media_type, [])
            if isinstance(urls, str):
                urls = [urls] if urls else []

            self.logger.info(f"Processing {len(urls)} {media_type}")

            for i, media_url in enumerate(urls):
                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        media_type[:-1]
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        images = content_dict.get('images', [])
        if images:
            self.logger.info(f"Processing {len(images)} images with captions")

            for i, image_data in enumerate(images):
                if not isinstance(image_data, dict):
                    self.logger.warning(
                        f"Skipping invalid image data: {image_data}")
                    continue

                media_url = image_data.get('url')
                caption = image_data.get('caption')

                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        'image'
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    captions_dict[safe_filename] = caption or 'No caption available'

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")
                    if caption:
                        self.logger.info(f"Saved caption for {safe_filename}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        if captions_dict:
            captions_path = os.path.join('./', 'image_captions.json')
            try:
                with open(captions_path, 'w', encoding='utf-8') as f:
                    json.dump(captions_dict, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Captions saved to {captions_path}")
            except Exception as e:
                self.logger.error(f"Error saving captions to JSON: {e}")

            captions_file = os.path.join('./', 'captions.txt')
            with open(captions_file, 'a', encoding='utf-8') as caption_file:
                caption_file.write(f"\nDownloaded on: {
                                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                caption_file.write("-" * 50 + "\n")

                for i, image_data in enumerate(images):
                    if not isinstance(image_data, dict):
                        self.logger.warning(
                            f"Skipping invalid image data: {image_data}")
                        continue

                    media_url = image_data.get('url')
                    caption = image_data.get('caption')

                    if not media_url:
                        continue

                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(
                            media_url,
                            timeout=self.timeout,
                            headers=headers,
                            stream=True
                        )
                        response.raise_for_status()

                        safe_filename = self._get_safe_filename(
                            media_url,
                            i,
                            'image'
                        )
                        full_path = os.path.join(download_path, safe_filename)

                        with open(full_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        caption_entry = f"Image: {safe_filename}\n"
                        if caption:
                            caption_entry += f"Caption: {caption}\n"
                        else:
                            caption_entry += "Caption: No caption available\n"
                        caption_entry += "-" * 30 + "\n"
                        caption_file.write(caption_entry)

                        self.logger.info(f"Successfully downloaded {
                                         media_url} to {full_path}")
                        if caption:
                            self.logger.info(
                                f"Saved caption for {safe_filename}")

                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"Network error downloading {
                                          media_url}: {str(e)}")
                    except IOError as e:
                        self.logger.error(
                            f"File I/O error saving {media_url}: {str(e)}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error downloading {
                                          media_url}: {str(e)}")


class MediaDownloader:
    def __init__(self, logger: logging.Logger, timeout: int = 10):
        self.logger = logger
        self.timeout = timeout

    def _get_safe_filename(self, url: str, index: int, media_type: str) -> str:
        parsed_url = urlparse(unquote(url))
        original_filename = os.path.basename(parsed_url.path)
        filename = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext_map = {
                'image': '.png',
                'audio': '.mp3',
                'link': '.txt'
            }
            ext = ext_map.get(media_type, '.bin')
        safe_filename = f"{filename}{ext}"
        return safe_filename

    def download_media(self, content_dict: Dict[str, Any], download_path: str = './article_downloads') -> None:
        Path(download_path).mkdir(parents=True, exist_ok=True)
        captions_dict = {}

        for media_type in ['audio', 'links']:
            urls = content_dict.get(media_type, [])
            if isinstance(urls, str):
                urls = [urls] if urls else []

            self.logger.info(f"Processing {len(urls)} {media_type}")

            for i, media_url in enumerate(urls):
                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        media_type[:-1]
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        images = content_dict.get('images', [])
        if images:
            self.logger.info(f"Processing {len(images)} images with captions")

            for i, image_data in enumerate(images):
                if not isinstance(image_data, dict):
                    self.logger.warning(
                        f"Skipping invalid image data: {image_data}")
                    continue

                media_url = image_data.get('url')
                caption = image_data.get('caption')

                if not media_url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(
                        media_url,
                        timeout=self.timeout,
                        headers=headers,
                        stream=True
                    )
                    response.raise_for_status()

                    safe_filename = self._get_safe_filename(
                        media_url,
                        i,
                        'image'
                    )
                    full_path = os.path.join(download_path, safe_filename)

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    captions_dict[safe_filename] = caption or 'No caption available'

                    self.logger.info(f"Successfully downloaded {
                                     media_url} to {full_path}")
                    if caption:
                        self.logger.info(f"Saved caption for {safe_filename}")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Network error downloading {
                                      media_url}: {str(e)}")
                except IOError as e:
                    self.logger.error(
                        f"File I/O error saving {media_url}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {
                                      media_url}: {str(e)}")

        if captions_dict:
            captions_path = os.path.join('./', 'image_captions.json')
            try:
                with open(captions_path, 'w', encoding='utf-8') as f:
                    json.dump(captions_dict, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Captions saved to {captions_path}")
            except Exception as e:
                self.logger.error(f"Error saving captions to JSON: {e}")

            captions_file = os.path.join('./', 'captions.txt')
            with open(captions_file, 'a', encoding='utf-8') as caption_file:
                caption_file.write(f"\nDownloaded on: {
                                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                caption_file.write("-" * 50 + "\n")

                for i, image_data in enumerate(images):
                    if not isinstance(image_data, dict):
                        self.logger.warning(
                            f"Skipping invalid image data: {image_data}")
                        continue

                    media_url = image_data.get('url')
                    caption = image_data.get('caption')

                    if not media_url:
                        continue

                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(
                            media_url,
                            timeout=self.timeout,
                            headers=headers,
                            stream=True
                        )
                        response.raise_for_status()

                        safe_filename = self._get_safe_filename(
                            media_url,
                            i,
                            'image'
                        )
                        full_path = os.path.join(download_path, safe_filename)

                        with open(full_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        caption_entry = f"Image: {safe_filename}\n"
                        if caption:
                            caption_entry += f"Caption: {caption}\n"
                        else:
                            caption_entry += "Caption: No caption available\n"
                        caption_entry += "-" * 30 + "\n"
                        caption_file.write(caption_entry)

                        self.logger.info(f"Successfully downloaded {
                                         media_url} to {full_path}")
                        if caption:
                            self.logger.info(
                                f"Saved caption for {safe_filename}")

                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"Network error downloading {
                                          media_url}: {str(e)}")
                    except IOError as e:
                        self.logger.error(
                            f"File I/O error saving {media_url}: {str(e)}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error downloading {
                                          media_url}: {str(e)}")
