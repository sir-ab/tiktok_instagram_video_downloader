import os
import re
import requests
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import Config
from utils import log_error, load_urls_from_file_ig
from requests.exceptions import RequestException
import urllib3
import asyncio
import json
import random
import zlib
import zstandard as zstd
import io

class DownloadError(Exception):
    pass


def interceptor(request, response):
    request
    response

class InstagramDownloader:
    def __init__(self):
        self.downloaded_urls = self.load_progress()

        # Selenium setup with Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_argument("--headless")  # Uncomment to run headless
        chrome_options.add_argument("--mute-audio")  # Mute audio
        chrome_options.add_argument("--enable-unsafe-swiftshader")  # Mute 
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")


        sw_options = {
            'port': 12345  # This must match what you passed to Chrome
        }

        if Config.CHROME_DRIVER_PATH:
          self.service = Service(Config.CHROME_DRIVER_PATH)
          self.driver = webdriver.Chrome(service=self.service, options=chrome_options, seleniumwire_options=sw_options)
        else:
          self.driver = webdriver.Chrome(options=chrome_options)
       
        self.driver.response_interceptor = interceptor
       
        # Ensure the output directory exists
        os.makedirs(Config.OUTPUT_DIR_Instagram, exist_ok=True)


    def load_progress(self):
        """Load the list of already downloaded URLs."""
        if os.path.exists(Config.PROGRESS_FILE_Instagram):
            with open(Config.PROGRESS_FILE_Instagram, "r", encoding="utf-8") as f:
                return set(f.read().splitlines())
        return set()

    def save_progress(self, url):
        """Save a processed URL to the progress file."""
        with open(Config.PROGRESS_FILE_Instagram, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        self.downloaded_urls.add(url)


    def extract_username_and_post_id(self, url):
        """Extract the post ID and username from the Instagram URL."""
        match = re.search(r"instagram\.com/(?:p|reel)/([^/]+)", url)
        if not match:
            raise ValueError(f"Invalid Instagram URL format: {url}")
        post_id = match.group(1)


        username = "unknown_user"

        # Extract username from the page
        # try:
        #     meta_tag = WebDriverWait(self.driver, 2).until(
        #       EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[name="twitter:title"]'))
        #     )
        #     content = meta_tag.get_attribute("content")
        #     username_match = re.search(r"\(([^)]+)\)", content)
        #     if username_match:
        #         username = username_match.group(1).strip()
        #     else:
        #         username = "unknown_user"
        # except Exception:
        #     username = "unknown_user"

        return username, post_id


    def construct_file_path(self, username, post_id, extension):
        """Construct the file path for the downloaded media."""
        file_name = f"{username}_{post_id}.{extension}"
        return os.path.join(Config.OUTPUT_DIR_Instagram, file_name)

    def download_file(self, file_url, output_path, retries = 3, delay=1):
        """Download a file (image or video) and save it."""
        for attempt in range(retries):
            try:
                response = requests.get(file_url, stream=True, timeout=10)
                if response.status_code == 401:
                    print(f"Unauthorized access: {file_url}, status_code: 401")
                    raise DownloadError("Unauthorized access (401). Stopping all downloads.")
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(1024 * 512):
                            f.write(chunk)
                    print(f"Downloaded: {output_path}")
                    return # Exit if successful
                else:
                    print(f"Failed to download: {file_url}, status_code: {response.status_code}")
                    raise DownloadError(f"Failed to download: {file_url}, status_code: {response.status_code}")

            except (RequestException, urllib3.exceptions.MaxRetryError, urllib3.exceptions.NameResolutionError) as e:
                if attempt == retries - 1:
                    print(f"Failed to download {file_url} after {retries} retries")
                    # log_error(file_url, f"Error downloading file: {e}", file_path=output_path, source="instagram")
                    raise DownloadError(f"Failed to download {file_url} after {retries} retries with error {e}")
                wait_time = delay * (2 ** attempt)
                print(f"Download failed for {file_url}, retrying in {wait_time} seconds")
                time.sleep(wait_time)
            except Exception as e:
                print(f"Error downloading file: {e}")
                # log_error(file_url, f"Error downloading file: {e}", file_path = output_path, source="instagram")
                raise DownloadError(f"Error downloading file: {e}")


    def process_url(self, url):
        """Process a single Instagram URL to download the media."""
        output_path = None
        try:
            del self.driver.requests  # Clear previous requests

            self.driver.get(url)
            # WebDriverWait(self.driver, 30).until(
            #     EC.presence_of_element_located((By.TAG_NAME, "body"))
            # )
            # WebDriverWait(self.driver, 20).until(
            #         EC.presence_of_element_located((By.TAG_NAME, "img"))
            #     )

            print("\n done wait") # Give time for network requests to complete
            time.sleep(3)  # Give time for network requests to complete
            print("done sleep") # Give time for network requests to complete
            # print(self.driver.requests)
            for request in self.driver.requests:
                if request.url == url and request.method == 'GET':
                    print("Found the GraphQL query request!")

                    if request.response:
                        print(f"Response Status: {request.response.status_code}")
                        try:
                            content_encoding = request.response.headers.get('Content-Encoding', '').lower()
                            print(f"Content-Encoding: {content_encoding}")  # Add this line

                            response_body = request.response.body
                            with open("compressed_body.bin", "wb") as f:
                                f.write(response_body)
                            
                            # print(response_body)

                            if content_encoding == "gzip":
                                response_body = zlib.decompress(
                                    response_body, zlib.MAX_WBITS | 32
                                )
                            elif content_encoding == "zstd":
                                try:
                                    decompressor = zstd.ZstdDecompressor()
                                    with decompressor.stream_reader(io.BytesIO(response_body)) as reader:
                                        decompressed_data = reader.read()
                                    response_body = decompressed_data                            
                                except Exception as e:
                                    print(f"Error decompressing zstd data: {e}")
                                    raise DownloadError(f"Error decompressing zstd data: {e}")

                                
                            # # Find the end of data by  "commenting_disabled_for_viewer"
                            # with open("1.txt", "w", encoding='utf-8') as file:
                            #     file.write(response_body.decode('utf-8'))

                            try:
                                response_body_str = response_body.decode("utf-8")
                            except UnicodeDecodeError as e:
                                print(f"Error decoding response body to string: {e}")
                                raise DownloadError(f"Error decoding response body to string: {e}")

                            match = re.search(
                                r'{"xdt_api__v1__media__shortcode__web_info".*?"commenting_disabled_for_viewer":.*?\}',
                                response_body_str,
                            )

                            if match:
                                json_string = match.group(0)
                                json_string = json_string + "]}}"
                            else:
                                raise DownloadError("Could not find json end in the response")
                            
                            with open("1.txt", "w", encoding='utf-8') as file:
                                file.write(json_string)                            
                            # print(1)
                            json_data = json.loads(json_string)
                            print(2)
                            username, post_id = self.extract_username_and_post_id(url)

                            if  "xdt_api__v1__media__shortcode__web_info" in json_data and "items" in json_data["xdt_api__v1__media__shortcode__web_info"]:
                                items = json_data["xdt_api__v1__media__shortcode__web_info"]["items"]
                                if not items:
                                    print("No items found in the response.")
                                    return None

                                for item in items:
                                     # Extract Username (if available in the first item)
                                    if 'user' in item and 'username' in item['user']:
                                        username = item['user']['username']

                                    # Check for carousel media first
                                    if 'carousel_media' in item and item['carousel_media']:
                                        for index, media in enumerate(item['carousel_media']):
                                            if 'video_versions' in media and media['video_versions']:
                                                video_url = media['video_versions'][0]['url']
                                                extension = 'mp4'
                                                output_path = self.construct_file_path(username, f"{post_id}_{index}", extension)
                                                self.download_file(video_url, output_path)

                                            elif 'image_versions2' in media and media['image_versions2'] and media['image_versions2']['candidates']:
                                                img_url = media['image_versions2']['candidates'][0]['url']
                                                extension = 'png'
                                                output_path = self.construct_file_path(username, f"{post_id}_{index}", extension)
                                                self.download_file(img_url, output_path)
                                            else:
                                                print(f"No valid video or image found in carousel {index}")
                                        return output_path

                                    elif "video_versions" in item and item["video_versions"]:
                                        video_url = item["video_versions"][0]["url"]
                                        extension = "mp4"
                                        output_path = self.construct_file_path(username, post_id, extension)
                                        self.download_file(video_url, output_path)
                                        return output_path

                                    elif 'image_versions2' in item and item["image_versions2"] and item["image_versions2"]["candidates"]:
                                        img_url = item["image_versions2"]["candidates"][0]["url"]
                                        extension = "png"
                                        output_path = self.construct_file_path(username, f"{post_id}", extension)
                                        self.download_file(img_url, output_path)
                                        return output_path
                                    else:
                                        print(f"No video or image found in this item.")
                                       

                            else:
                                print("No 'xdt_api__v1__media__shortcode__web_info' or 'items' found in the GraphQL response.")

                        except json.JSONDecodeError:
                            raise DownloadError("Response body is not valid JSON.")
                        except Exception as e:
                           
                            raise DownloadError(f"Error processing data {e}")
                    else:
                        raise DownloadError("No response received for this request.")
            del self.driver.requests # remove requests
            print(self.driver.requests)
            return output_path

        except Exception as e:
            file_path = output_path if output_path else "N/A"
            print(f"Error processing URL {url}: {e}")
            raise DownloadError(f"Error processing URL {url}: {e}")
        

    def close(self):
        """Close the Selenium WebDriver."""
        self.driver.quit()


async def process_instagram_urls_with_progress(url_input, file_input):
    global cancel_flag

    downloader = InstagramDownloader()
    log_output = []
    downloaded_list = []
    try:
      if url_input.strip():
          urls = url_input.strip().split("\n")
      elif file_input:
          file_path = file_input.name
          urls = load_urls_from_file_ig(file_path)
      else:
            # Yield an error message instead of returning
            yield "Please provide URLs or upload a file.", [], None
            return  # Exit the function early if input is invalid C3yWle0ABX-

      total_urls = len(urls)

      for i, url in enumerate(urls):
        if cancel_flag:
            yield "Processing canceled.", log_output, downloaded_list
            while cancel_flag:
                time.sleep(5)

        if url in downloader.downloaded_urls:
            print(f"Skipping already downloaded URL: {url}")
            continue
        


        if url == "":
                print(f"Reached target video ID {url}. Stopping.")
                break
        try:
            print(f"\n********************Processing URL: {url} ********************")
            output_path = downloader.process_url(url)
            downloader.save_progress(url)

            log_output.append(f"Processed: {url}")

            video_path = os.path.join(Config.OUTPUT_DIR_Instagram, output_path)


            downloaded_list.append((output_path, f"label {i}"))
            print(downloaded_list[-1])
            # print(video_path)

        except Exception as e:
            if "401" in str(e):
                print("Encountered 401 error. Stopping all processing.")
                yield f"Error: Unauthorized access (401). Stopping all downloads.", log_output, None
                log_error(url, f"Error: Unauthorized access (401). Stopping all downloads.", file_path="N/A", source="instagram")

                break
            else:
                log_output.append(f"Error processing {url}: {e}")
                log_error(url, f"Error processing URL: {e}", file_path="N/A", source="instagram")
                downloader.save_progress(url)


        if i - total_urls < 10 or (i - total_urls >= 10 and (i + 1) % 5 == 0):
          yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), downloaded_list
        #   yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), None
          await asyncio.sleep(0.1)  # Non-blocking sleep for async loop
        else:
          yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), None
          await asyncio.sleep(0.1)  # Non-blocking sleep for async loop
        # time.sleep(5)
        time.sleep(min(random.expovariate(0.2), 7))

      yield f"Processing complete!", "\n".join(log_output), downloaded_list

    except Exception as e:
      yield f"An error occurred: {e}", [], None

    # finally:
    #     downloader.close()


cancel_flag = False


def cancel_process_ig():
    global cancel_flag
    cancel_flag = True

def resume_process_ig():
    global cancel_flag
    cancel_flag = False

# async def main():
#     async for result in process_instagram_urls_with_progress("https://www.instagram.com/p/DEbTQknSIHb/?img_index=1", None):
#         print(result)

# asyncio.run(main())
