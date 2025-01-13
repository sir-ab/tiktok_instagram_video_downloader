import os
import re

def extract_code_from_filename(filename):
    """
    Extract the Instagram code from a filename, removing any trailing _number before processing.
    """
    # Remove the extension first (e.g., .png, .jpg)
    filename_without_extension = os.path.splitext(filename)[0]
    
    # Check if the filename ends with _number and remove it
    match = re.search(r'_(\d+)$', filename_without_extension)
    if match:
        filename_without_extension = filename_without_extension[:match.start()]
    
    # Extract the last 11 characters as the code
    if len(filename_without_extension) >= 11:
        return filename_without_extension[-11:]
    else:
        raise ValueError(f"Filename '{filename}' is too short to extract 11 characters.")

def process_folder(folder_path):
    """
    Process a folder, extract Instagram codes, and format them as URLs.
    """
    try:
        filenames = os.listdir(folder_path)
        urls = set()  # Use a set to ensure uniqueness

        for filename in filenames:
            # Skip directories
            if os.path.isfile(os.path.join(folder_path, filename)):
                try:
                    code = extract_code_from_filename(filename)
                    # Format as Instagram URL
                    url = f"https://www.instagram.com/p/{code}/"
                    urls.add(url)  # Add URL to the set (automatically removes duplicates)
                except ValueError as e:
                    print(f"Error processing file '{filename}': {e}")

        # Return the set of URLs, which ensures uniqueness
        return urls
    except Exception as e:
        print(f"Error reading folder: {e}")
        return set()

def save_urls_to_file(urls, output_file):
    """
    Save the URLs to a file, ensuring each URL appears only once.
    """
    with open(output_file, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")

# Example usage
folder_path = r"download_tiktok_ig\instagram\Downloaded_Files_Instagram"  # Replace with the folder path
output_file = 'instagram_urls.txt'  # Specify the output file path

urls = process_folder(folder_path)
if urls:
    save_urls_to_file(urls, output_file)
    print(f"URLs saved to {output_file}")
else:
    print("No URLs to save.")
