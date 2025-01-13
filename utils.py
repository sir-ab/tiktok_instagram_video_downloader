import os
import logging
from datetime import datetime, timedelta, timezone
import json
from config import Config

# Ensure that the directories for error logs exist
os.makedirs(os.path.dirname(Config.ERROR_LOG_FILE_Tiktok), exist_ok=True)
os.makedirs(os.path.dirname(Config.ERROR_LOG_FILE_Instagram), exist_ok=True)

# Set up logging with error logger for TikTok
error_logger_Tiktok = logging.getLogger('error_logger_tiktok')
error_logger_Tiktok.setLevel(logging.DEBUG)
error_handler_Tiktok = logging.FileHandler(Config.ERROR_LOG_FILE_Tiktok)
error_formatter_Tiktok = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
error_handler_Tiktok.setFormatter(error_formatter_Tiktok)
error_logger_Tiktok.addHandler(error_handler_Tiktok)

# Set up logging with error logger for Instagram
error_logger_Instagram = logging.getLogger('error_logger_instagram')
error_logger_Instagram.setLevel(logging.DEBUG)
error_handler_Instagram = logging.FileHandler(Config.ERROR_LOG_FILE_Instagram)
error_formatter_Instagram = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
error_handler_Instagram.setFormatter(error_formatter_Instagram)
error_logger_Instagram.addHandler(error_handler_Instagram)

def load_urls_from_file_tiktok(file_path):
    """Load URLs from a file and return them as a list, supporting JSON and TXT format for TikTok."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                # Attempt to load as JSON
                data = json.load(f)
                favorite_videos = data.get("Activity", {}).get("Like List", {}).get("ItemFavoriteList", [])
                original_links = []
                modified_links = []
                for video in favorite_videos:
                    original_link = video.get("link", "")
                    if original_link:
                        original_links.append(original_link)
                        modified_link = original_link.replace("www.tiktokv.com/share/video", "www.tiktok.com/embed/v3")
                        modified_links.append(modified_link)
                print(f"Successfully loaded {len(modified_links)} urls from JSON file: {file_path}")
                return modified_links

            except json.JSONDecodeError:
                # If not a JSON, treat as a regular text file
                f.seek(0)
                urls = [line.strip() for line in f.readlines() if line.strip()]
                print(f"Successfully loaded {len(urls)} urls from Text file: {file_path}")
                return urls

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []


def load_urls_from_file_ig(file_path):
    """Load URLs from a file, convert reel URLs to post URLs, and return as a list.
       Supports JSON and TXT formats."""
    def convert_reel_to_post_url(url):
        """Converts an Instagram reel URL to a post URL."""
        if "/reel/" in url:
           return url.replace("/reel/", "/p/")
        return url

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                # Attempt to load as JSON
                data = json.load(f)
                saved_media = data.get("saved_saved_media", [])
                urls = []
                for item in saved_media:
                    string_map_data = item.get("string_map_data", {})
                    for key, value in string_map_data.items():
                        if key == "Saved on":
                           url = value.get("href")
                           if url:
                             urls.append(convert_reel_to_post_url(url))

                # Handle liked media
                likes_media_likes = data.get("likes_media_likes", [])
                for item in likes_media_likes:
                    string_list_data = item.get("string_list_data", [])
                    for entry in string_list_data:
                        url = entry.get("href")
                        if url:
                            urls.append(convert_reel_to_post_url(url))

                print(f"Successfully loaded {len(urls)} urls from JSON file: {file_path}")
                return urls

            except json.JSONDecodeError:
                # If not a JSON, treat as a regular text file
                f.seek(0)
                urls = [convert_reel_to_post_url(line.strip()) for line in f.readlines() if line.strip()]
                print(f"Successfully loaded {len(urls)} urls from Text file: {file_path}")
                return urls

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def log_error(url, error_message, file_path=None, source="tiktok"):
    """Log errors to the respective error log file based on the source (tiktok or instagram)."""
    try:
        utc_plus_7 = timezone(timedelta(hours=7))

        # Get the current time in UTC+7
        timestamp = datetime.now(utc_plus_7).strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"Error with URL {url}: {error_message}"
        if file_path:
            log_entry += f" | File Path: {file_path}"

        if source == "tiktok":
          error_logger_Tiktok.debug(log_entry)
        elif source == "instagram":
          error_logger_Instagram.debug(log_entry)
        else:
           print("[DEBUG] Invalid source for logging")

        print(f"[DEBUG] Logged error: {log_entry}")  # Debug log
    except Exception as log_exception:
        print(f"[DEBUG] Failed to log error: {log_exception}")