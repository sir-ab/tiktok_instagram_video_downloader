# tiktok_downloader/tiktok_downloader.py

import os
import requests
import re
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import base64
from config import Config
from utils import log_error, load_urls_from_file_tiktok
from requests.exceptions import RequestException
import urllib3

class DownloadError(Exception):
    pass

class TikTokDownloader:
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
        chrome_options.add_argument("--enable-unsafe-swiftshader")  # Mute audio
        if Config.CHROME_DRIVER_PATH:
            self.service = Service(Config.CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)


        # Ensure the output directory exists
        os.makedirs(Config.OUTPUT_DIR_Tiktok, exist_ok=True)

    def load_progress(self):
        """Load the list of already downloaded URLs."""
        if os.path.exists(Config.PROGRESS_FILE_Tiktok):
            with open(Config.PROGRESS_FILE_Tiktok, "r", encoding="utf-8") as f:
                return set(f.read().splitlines())
        return set()

    def save_progress(self, url):
        """Save a processed URL to the progress file."""
        with open(Config.PROGRESS_FILE_Tiktok, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        self.downloaded_urls.add(url)


    def extract_username_and_video_id(self, url):
        """Extract the username and video ID from the TikTok embed URL."""
        match = re.search(r"https://www\.tiktok\.com/embed/v3/(\d+)", url)
        if not match:
            raise ValueError(f"Invalid URL format: {url}")
        video_id = match.group(1)

        # Extract username from the page
        try:
            username_element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".sc-kAyceB.eqSpfN.unique-id"))
            )
            username = username_element.text
        except Exception:
            username = "unknown_user"

        return username, video_id

    def construct_file_path(self, username, video_id, extension):
        """Construct the file path for the video or image."""
        file_name = f"{username}_{video_id}.{extension}"
        return os.path.join(Config.OUTPUT_DIR_Tiktok, file_name)


    def download_file(self, file_url, output_path, retries = 3, delay=1):
            """Download a file (image or video) and save it, with retry."""
            for attempt in range(retries):
                try:
                    # Check if the URL is a base64 data URL
                    if file_url.startswith("data:image") or file_url.startswith("data:video"):
                        # Extract the base64 string after the comma
                        base64_data = file_url.split(",", 1)[1]
                        # Decode the base64 string
                        file_data = base64.b64decode(base64_data)
                        # Write the decoded data to a file
                        with open(output_path, "wb") as f:
                            f.write(file_data)
                        print(f"Downloaded from base64: {output_path}")
                        return # Exit after a success

                    else:
                        # Handle regular URL download
                        response = requests.get(file_url, stream=True, timeout=10)  # Added timeout
                        if response.status_code == 200:
                            with open(output_path, "wb") as f:
                                for chunk in response.iter_content(1024 * 512):
                                    f.write(chunk)
                            print(f"Downloaded: {output_path}")
                            return # Exit after a success

                        else:
                            print(f"Failed to download: {file_url}, status_code: {response.status_code}")
                            raise DownloadError(f"Failed to download: {file_url}, status_code: {response.status_code}") # Added Download Error


                except (RequestException, urllib3.exceptions.MaxRetryError, urllib3.exceptions.NameResolutionError) as e:
                    if attempt == retries-1:
                        print(f"Failed to download {file_url} after {retries} retries")
                        # log_error(file_url, f"Error downloading file: {e}", file_path=output_path)
                        raise DownloadError(f"Failed to download {file_url} after {retries} retries with error {e}")  #Added DownloadError

                    wait_time = delay * (2 ** attempt)
                    print(f"Download failed for {file_url}, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                except Exception as e:
                    print(f"Error downloading file: {e}")
                    # log_error(file_url, f"Error downloading file: {e}", file_path = output_path)
                    raise DownloadError(f"Error downloading file: {e}")# Added DownloadError


    def process_url(self, url):
        """Process a single embed URL to download the video or image."""
        try:
            self.driver.get(url)
            # time.sleep()
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract username and video ID
            username, video_id = self.extract_username_and_video_id(url)

            # Wait for all images and videos to load
            try:
                video_element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                file_url = video_element.get_attribute("src")
                extension = "mp4"
                output_path = self.construct_file_path(username, video_id, extension)
                self.download_file(file_url, output_path)
                # print(f"File saved: {output_path}")
            except Exception:
                # Fall back to images if video is not available
                image_elements = self.driver.find_elements(By.XPATH, "//picture//img")
                if image_elements:
                    for idx, img in enumerate(image_elements):
                        try:
                            # Attempt to find the second button with the specified class
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, ".sc-dtInlm.bewocV")
                            if len(buttons) > 0:
                                second_button = buttons[-1]
                                # Execute a click on the second button if found
                                second_button.click()
                                print("Clicked on the second button")
                                time.sleep(0.2) # Give time for the change to occur
                            else:
                                print(f"Could not find the second button for image with index {idx}")
                        except Exception as click_error:
                            print(f"Error clicking on button for image with index {idx}: {click_error}")

                        file_url = img.get_attribute("src")
                        extension = "png"
                        output_path = self.construct_file_path(username, f"{video_id}_{idx}", extension)
                        self.download_file(file_url, output_path)
                        # print(f"Image saved: {output_path}")

            return output_path

        except Exception as e:
            file_path = output_path if output_path else "N/A" # ternary operator to handle output path not set
            print(f"Error processing URL {url}: {e}")
            # log_error(url, f"Error processing URL: {e}", file_path=file_path)
            raise DownloadError(f"Error processing URL {url}: {e}") # Changed to Download Error

            # return None

    def close(self):
        """Close the Selenium WebDriver."""
        self.driver.quit()


async def process_tiktok_urls_with_progress(url_input, file_input):
    global cancel_flag


    downloader = TikTokDownloader()
    downloaded_list = []
    log_output = []
    downloaded_number = len(downloader.downloaded_urls)

    try:
        if url_input.strip():
            urls = url_input.strip().split("\n")
        elif file_input:
            file_path = file_input.name
            urls = load_urls_from_file_tiktok(file_path)
        else:
            # Yield an error message instead of returning
            yield "Please provide URLs or upload a file.", [], None
            return  # Exit the function early if input is invalid

        total_urls = len(urls)

        for i, url in enumerate(urls):
            if cancel_flag:
                print("canceled")
                yield "Processing canceled.",  log_output, downloaded_list
                raise ValueError("Processing canceled" )

            if url in downloader.downloaded_urls:
                print(f"Skipping already downloaded URL: {url}")
                continue

            print(f"\n********************Processing URL: {url} ********************")
            username, video_id = downloader.extract_username_and_video_id(url)

            if video_id == "7451406838563736839":
                print(f"Reached target video ID {video_id}. Stopping.")
                break

            try:
                output_path = downloader.process_url(url)
                downloader.save_progress(url)

                log_output.append(f"Processed: {url}")

                video_path = os.path.join(Config.OUTPUT_DIR_Tiktok, output_path)
                # downloaded_list.append((video_path, f"label {i}"))
                # print(downloaded_list[-1])
                print(video_path)

            except Exception as e:
                log_output.append(f"Error processing {url}: {e}")
                log_error(url, f"Error processing during progress function: {e}", file_path= "N/A")
                downloader.save_progress(url)


            # Update progress but defer gallery update
            if i - total_urls < 10 or (i - total_urls >= 10 and (i + 1) % 5 == 0):
                # yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), downloaded_list
                yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), None
                await asyncio.sleep(0.1)  # Non-blocking sleep for async loop

            else:
                yield f"Progress: {i+1}/{total_urls}", "\n".join(log_output), None
                await asyncio.sleep(0.1)  # Non-blocking sleep for async loop


            # if i % 30 == 0:
            #     output.clear()

        yield "Processing complete!", "\n".join(log_output), downloaded_list

    except Exception as e:
        yield f"An error occurred: {e}", [], None

    finally:
        downloader.close()

cancel_flag = False


def cancel_process():
    global cancel_flag
    cancel_flag = True

    
def resume_process():
    global cancel_flag
    cancel_flag = False