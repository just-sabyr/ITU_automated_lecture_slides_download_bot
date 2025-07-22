import re
import dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import urllib.parse # Added for filename unquoting

from login import login_with_selenium

# --- Configs ---
# Load credentials from .env file
credentials = dotenv.dotenv_values('.env')
USERNAME = credentials.get('USERNAME')
PASSWORD = credentials.get('PASSWORD')

# Base URL for Ninova
BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
# A URL that redirects to the login page if not authenticated
INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324'
# Default directory for downloads
DOWNLOAD_DIRECTORY = 'ITU_Ninova_Lecture_Slides'

# Ensure the download directory exists
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)
# ---------------

def download_file(session: requests.Session, url: str, directory: str, filename: str = None):
    """
    Downloads a file using the provided requests session.

    Args:
        session (requests.Session): The authenticated requests session.
        url (str): The URL of the file to download.
        directory (str): The local directory where the file should be saved.
        filename (str, optional): The desired name for the downloaded file.
                                  If None, the filename is extracted from the URL or
                                  Content-Disposition header.
    """
    try:
        response = session.get(url, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Determine filename
        if filename is None:
            # Try to get filename from Content-Disposition header
            if 'Content-Disposition' in response.headers:
                cd = response.headers['Content-Disposition']
                # Handles both filename*=UTF-8'' and filename=
                if "filename*=" in cd:
                    filename = urllib.parse.unquote(cd.split("filename*=")[1].strip())
                elif "filename=" in cd:
                    filename = cd.split('filename=')[1].strip('"\'')
            # Fallback to extracting from URL if not found in headers
            if filename is None:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename: # If path is just a slash or empty, use a default
                    filename = "downloaded_file.pdf" # Default fallback

        # Clean the filename to remove invalid characters
        filename = clean_filename(filename)
        file_path = os.path.join(directory, filename)

        # Ensure the target directory exists
        os.makedirs(directory, exist_ok=True)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Successfully downloaded '{filename}' to '{file_path}' from '{url}' ✅")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file from {url}: {e} ❌")
    except Exception as e:
        print(f"An unexpected error occurred during download of {url}: {e} ❌")

def get_session_cookies_from_selenium(driver):
    """
    DEPRECATED: This function is now integrated directly into login_with_selenium.
    Extracts cookies from a Selenium WebDriver and returns them in requests.Session format.
    """
    s = requests.Session()
    for cookie in driver.get_cookies():
        s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
    return s

def extract_path_from_breadcrumb(soup):
    """
    Extracts the current path from the blue breadcrumb bar.
    Example: "/Lecture Notes (Feza BUZLUCA)/02.Non_object_oriented features/" -> "Lecture Notes (Feza BUZLUCA)/02.Non_object_oriented features"
    """
    path_div = soup.find('div', style='background-color: #90D1E7; color: #fff;padding:4px;')
    if path_div:
        full_path_str = path_div.get_text(strip=True)
        # Remove leading/trailing slashes and split by '/' to handle directory structure
        # Use re.split to handle multiple slashes as a single delimiter
        path_parts = [part for part in re.split(r'\/+', full_path_str) if part]

        cleaned_path = os.path.join(*path_parts)
        return cleaned_path
    return ""

def clean_filename(filename):
    """Cleans a string to be a valid filename."""
    # Remove characters that are invalid in filenames
    cleaned_name = re.sub(r'[\\/:*?"<>|]', '', filename)
    # Replace common problematic suffixes like "/page"
    if cleaned_name.lower().endswith("page"):
        cleaned_name = cleaned_name[:-len("page")].strip()
    return cleaned_name.strip()

def traverse_and_download(session: requests.Session, url: str, base_download_path: str, visited_urls=None):
    """
    Recursively traverses the Ninova directory structure and downloads lecture files.

    Args:
        session (requests.Session): The authenticated requests session.
        url (str): The current URL to traverse.
        base_download_path (str): The root directory where all files will be saved.
        visited_urls (set, optional): A set to keep track of visited URLs to prevent infinite loops.
    """
    if visited_urls is None:
        visited_urls = set()

    # Normalize URL to prevent issues with slight variations
    normalized_url = url.split('?')[0] # Remove query parameters for visited check

    if normalized_url in visited_urls:
        print(f"Already visited: {url}, skipping. ⏭️")
        return
    visited_urls.add(normalized_url)

    print(f"\nVisiting: {url}")
    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access {url}: {e} ❌")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    # Determine the current path for saving files based on breadcrumb
    current_relative_path = extract_path_from_breadcrumb(soup)
    current_save_dir = os.path.join(base_download_path, current_relative_path)
    os.makedirs(current_save_dir, exist_ok=True)
    print(f"Saving files to: {current_save_dir}")

    # Find all table rows within the specific content area
    # Assuming content is within a table or a structured list
    # Look for the table that contains the file/folder listings.
    # This might need adjustment based on the actual HTML structure.
    # A common pattern is to look for a table with a specific class or ID.
    # For now, let's assume the relevant rows are under a general 'table' or 'div'
    # and contain 'td' elements with links and images.

    # A more robust way to find file/folder entries:
    # Look for elements that contain both an <a> tag and an <img> tag
    # where the <img> src indicates a file type or folder.
    
    # Example: Find all <tr> tags that are likely to contain file/folder info
    # This is a generic approach; you might need to refine the selector
    # based on the actual HTML structure of Ninova's resource pages.
    
    # Finding elements that represent files or folders
    # Ninova often uses <td> elements containing <a> and <img> tags.
    # Let's find all <a> tags within a specific content area that might be links to files/folders.
    
    # Find the main content area, if identifiable (e.g., by ID or class)
    # For Ninova, often the main content is in a div with id 'mainContent' or similar.
    # If not, we'll iterate through all 'a' tags.
    
    # Let's target the table rows that contain the file/folder information
    # Based on the previous code, it seems the relevant elements are <td> tags.
    # We need to find the parent container of these <td> tags to ensure we're parsing the correct section.
    
    # A common pattern: find all <a> tags that have an <img> child
    # and whose href is relative or starts with /tr/dersler/
    
    # Find all <a> tags that link to files or sub-directories
    # and check their associated <img> tag to determine type.
    
    # Find all <td> elements that contain an <a> tag and an <img> tag
    # This is a more specific selection based on the original code's implied structure.
    
    # The original code had `rows = soup.find_all('td')` and then `for row in rows[1:0]:`
    # `[1:0]` will result in an empty list. This loop will never run.
    # It should probably be `for row in rows:` or a more targeted selection.
    
    # Let's refine the selection to target actual file/folder entries.
    # We're looking for <a> tags within <td> elements that have an <img> child.
    
    # Find the table that holds the file list (often has a specific class or ID)
    # If no specific table ID, we might need to be more general.
    # Let's assume the links are within a table.
    
    # Find all links within the main content area that could be files or folders
    for link_tag in soup.find_all('a', href=True):
        href = link_tag['href']
        full_url = urljoin(BASE_NINOVA_URL, href) # Ensure full URL

        # Check if there's an image associated with the link to determine type
        img_tag = link_tag.find('img')
        if img_tag:
            img_src = img_tag.get('src', '')

            # Check for folder links
            if 'folder.png' in img_src:
                # Ensure it's a valid Ninova internal folder link
                if 'ninova.itu.edu.tr' in full_url and '?' in full_url:
                    print(f"Found folder: {link_tag.get_text(strip=True)}")
                    # Recursively traverse into the folder
                    traverse_and_download(session, full_url, base_download_path, visited_urls)

            # Check for PDF file links
            elif 'ikon-pdf.png' in img_src:
                # Ensure it's a valid Ninova internal download link
                if 'ninova.itu.edu.tr' in full_url and '?' in full_url:
                    print(f"Found PDF file: {link_tag.get_text(strip=True)}")
                    # Download the file to the current determined directory
                    download_file(session, full_url, current_save_dir)

            # You can add more file types here (e.g., Word, PowerPoint)
            # elif 'ikon-word.png' in img_src or 'ikon-powerpoint.png' in img_src:
            #     if 'ninova.itu.edu.tr' in full_url and '?' in full_url:
            #         print(f"Found document: {link_tag.get_text(strip=True)}")
            #         download_file(session, full_url, current_save_dir)

# --- Main Execution ---
if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD in your .env file. ❌")
    else:
        try:
            # 1. Perform login with Selenium to get an authenticated session
            authenticated_session = login_with_selenium(
                USERNAME,
                PASSWORD,
                INITIAL_LOGIN_REDIRECT_URL
            )

            # Define the target course resource URL (example provided by user)
            # You can change this to any Ninova course resource page you want to download from.
            TARGET_COURSE_RESOURCE_URL = 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g397'

            # 2. Start traversing and downloading from the target URL
            print(f"\nStarting traversal and download from: {TARGET_COURSE_RESOURCE_URL}")
            traverse_and_download(
                authenticated_session,
                TARGET_COURSE_RESOURCE_URL,
                DOWNLOAD_DIRECTORY
            )
            print("\nDownload process completed! 🎉")

        except Exception as e:
            print(f"\nAn error occurred during the main execution: {e} 🛑")

