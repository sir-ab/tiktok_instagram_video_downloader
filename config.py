# tiktok_downloader/config.py

import os

class Config:
    BASE_DIR_Tiktok = "download_tiktok_ig/tiktok"  # Or set this relative to your script
    BASE_DIR_Instagram = "download_tiktok_ig/instagram"  # Or set this relative to your script
    OUTPUT_DIR_Tiktok = os.path.join(BASE_DIR_Tiktok, "Downloaded_Files_Tiktok")
    OUTPUT_DIR_Instagram = os.path.join(BASE_DIR_Instagram, "Downloaded_Files_Instagram")

    PROGRESS_FILE_Tiktok = os.path.join(BASE_DIR_Tiktok, "downloaded_urls_Tiktok.txt")
    PROGRESS_FILE_Instagram = os.path.join(BASE_DIR_Instagram, "downloaded_urls_Instagram.txt")

    ERROR_LOG_FILE_Tiktok = os.path.join(BASE_DIR_Tiktok, "error_log_Tiktok.txt")
    ERROR_LOG_FILE_Instagram = os.path.join(BASE_DIR_Instagram, "error_log_Instagram.txt")
    # URL_FILE = os.path.join(BASE_DIR, "modified_links.txt")
    # URL_FILE = os.path.join(BASE_DIR, "modified_links.txt")
    CHROME_DRIVER_PATH = r"C:\Users\ADMIN\Downloads\chromedriver-win64\chromedriver.exe" #  Set to None when deploying to Colab