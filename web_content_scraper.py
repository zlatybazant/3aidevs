from urllib.parse import urljoin, urlparse, unquote
import logging
from logging.handlers import RotatingFileHandler
import os
import requests
from bs4 import BeautifulSoup as bs
from typing import Dict, Any, Optional, List


class WebContentScraper:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 10, log_file: str = 'web_scraper.log'):
        """
        Initialize web scraper with configurable timeout
        :param timeout: Request timeout in seconds
        :param base_url: Base URL for resolving relative links
        :param log_file: Path to log file
        """
        print("Initializing...")
        self.logger = logging.getLogger('WebContentScraper')
        self.logger.setLevel(logging.DEBUG)

        print("Creating log file...")
        log_dir = os.path.dirname(log_file) or '.'
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Scraper config
        self.timeout = timeout
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def safe_extract_images_with_captions(self, soup: bs) -> List[Dict[str, str]]:
        """
        :param soup: BS parsed document
        :return: List of dictionaries containing image URLs and captions
        """
        images_with_captions = []
        try:
            # Find all figure elements
            figures = soup.find_all('figure')
            for figure in figures:
                img_element = figure.find('img')
                caption_element = figure.find('figcaption')
                if img_element and img_element.get('src'):
                    try:
                        image_url = img_element.get('src')
                        resolved_url = self.resolve_url(image_url)
                        if self.is_valid_url(resolved_url):
                            image_data = {
                                'url': resolved_url,
                                'caption': caption_element.get_text(strip=True) if caption_element else None
                            }
                            images_with_captions.append(image_data)
                    except Exception as e:
                        self.logger.warning(
                            f"Error processing image URL {image_url}: {e}")
            # Also look for standalone images (not in figure tags)
            standalone_images = soup.find_all('img', src=True)
            for img in standalone_images:
                # Skip images we've already processed (those inside figure tags)
                if any(img_data['url'] == self.resolve_url(img['src'])
                       for img_data in images_with_captions):
                    continue

                try:
                    resolved_url = self.resolve_url(img['src'])
                    if self.is_valid_url(resolved_url):
                        image_data = {
                            'url': resolved_url,
                            'caption': None
                        }
                        images_with_captions.append(image_data)

                except Exception as e:
                    self.logger.warning(
                        f"Error processing standalone image URL {img['src']}: {e}")

            return images_with_captions

        except Exception as e:
            self.logger.error(f"Error extracting images with captions: {e}")
            return []

    def safe_extract_urls(self, soup: bs, tag: str, attr: str) -> List[str]:
        """
        Safely extract URLs from specified HTML tags

        :param soup: BS parsed document
        :param tag: HTML tag to search ('a', 'img')
        :param attr: Attribute to extract ('href', 'src')
        :return: List of validated and resolved URLs
        """
        try:
            elements = soup.find_all(tag, **{attr: True})
            urls = []

            for element in elements:
                url = element.get(attr)

                if not url:
                    continue
                try:
                    resolved_url = self.resolve_url(url)

                    if self.is_valid_url(resolved_url):
                        urls.append(resolved_url)

                except Exception as e:
                    self.logger.warning(f"Error processing {tag} {
                                        attr} URL {url}: {e}")

            return urls

        except Exception as e:
            self.logger.error(f"Error extracting {tag} {attr} URLs: {e}")
            return []

    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch web page content with multiple parsing methods

        :param url: URL to resolve
        :return: Dictionary containing parsed content including images with captions
        :raises Exception: If URL cannot be resolved
        """
        try:
            print("Fetching content...")
            full_url = self.resolve_url(url)

            response = requests.get(
                full_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = bs(response.content, 'html.parser')

            return {
                'text': soup.get_text(strip=True),
                'html': response.text,
                'links': self.safe_extract_urls(soup, 'a', 'href'),
                'images': self.safe_extract_images_with_captions(soup),
                'audio': self.safe_extract_urls(soup, 'audio', 'src'),
            }

        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise Exception(f"Network error when fetching {url}")
        except Exception as e:
            self.logger.error(f"Unexpected scraping error: {e}")
            raise Exception(f"Scraping failed for {url}") from e

    def resolve_url(self, url: str) -> str:
        """
        Resolve relative URLs with robust handling

        :param url: URL to resolve
        :return: Fully qualified URL
        :raises WebScraperException: If URL cannot be resolved
        """
        try:
            print("Resolving URL...")
            url = url.replace('view-source:', '')
            if not self.base_url:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    self.base_url = f"{parsed.scheme}://{parsed.netloc}"

            if url.startswith('i/'):
                resolved_url = urljoin(self.base_url + '/dane/', url)
            else:
                resolved_url = urljoin(self.base_url, url)

            parsed_resolved = urlparse(resolved_url)
            if not all([parsed_resolved.scheme, parsed_resolved.netloc]):
                raise ValueError("Invalid resolved URL")

            return resolved_url

        except Exception as e:
            self.logger.error(f"URL resolution error: {e}")
            raise Exception(f"Cannot resolve URL: {url}") from e

    def is_valid_url(self, url: str) -> bool:
        """
        Validate URL format

        :param url: URL to validate
        :return: Boolean indicating URL validity
        """
        try:
            print("Checking if URL is valid...")
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _get_safe_filename(self, url: str, index: int, media_type: str) -> str:
        """
        Generate a safe filename with proper extension from URL
        """
        # Parse the URL and get the path
        parsed_url = urlparse(unquote(url))
        original_filename = os.path.basename(parsed_url.path)

        # Extract extension and filename from original filename or default to '.bin'
        filename = os.path.splitext(original_filename)[0]
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            # Map common media types to extensions if no extension in URL
            ext_map = {
                'image': '.png',
                'audio': '.mp3',
                'link': '.txt'
            }
            ext = ext_map.get(media_type, '.bin')

        # Create safe filename with index and extension
        safe_filename = f"{filename}{ext}"
        return safe_filename
