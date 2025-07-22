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


# --- Configs ---
credentials = dotenv.dotenv_values('.env')
USERNAME, PASSWORD = credentials['USERNAME'], credentials['PASSWORD']
BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324' # Must be a link that will send u to login webpage
TARGET_COURSE_RESOURCE_URL = 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g397'
# https://ninova.itu.edu.tr/Sinif/21.110362/DersDosyalari?g397
DOWNLOAD_DIRECTORY = 'ITU_Ninova_Lecture_Slides'
# ---------------

def get_session_cookies_from_selenium(driver):
    """Extracts cookies from a Selenium WebDriver and returns them in requests.Session format."""
    s = requests.Session()
    for cookie in driver.get_cookies():
        s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
    return s

def download_file(session: requests.Session, url, directory, filename=None):
    """Downloads a file using the provided session.

    Params: 
        session: logged in session on Ninova
        url: A URL link for a download, sample 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g7911453'
        directory: the download directory in which the files are to be saved
        filename: if u want to change the name of the file, otherwise, will be the same if the file was downloaded using the link, or a default of 'download_file.pdf'
    """
    response = session.get(url, stream=True)
    response.raise_for_status()

    # Extract filename from Content-Description header or use a default
    filename = "download_file.pdf"
    if 'Content-Disposition' in response.headers:
        cd = response.headers['Content-Disposition']
        # Find filename
        if 'filename*=' in cd:
            import urllib.parse
            filename = urllib.parse.unquote(cd.split('filename*=')[1].strip())
        elif 'filename=' in cd:
            filename = cd.split('filename=')[1].strip('"\'') # TODO: ?
    
    file_path = os.path.join(directory, filename)

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Successfully downloaded '{filename}' to '{url}'!")

def extract_path_from_breadcrumb(soup):
    """
    Extracts the current path from the blue breadcrumb bar.
    Example: "/Lecture Notes (Feza BUZLUCA)/02.Non_object_oriented features/" -> "Lecture Notes (Feza BUZLUCA)/02.Non_object_oriented features"
    """
    path_div = soup.find('div', style='background-color: #90D1E7; color: #fff;padding:4px;')
    if path_div:
        full_path_str = path_div.get_text(strip=True)
        # Remove leading/trailing slahes and split by '/' to handle directory structure
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
        
def traverse_and_download(session, url, base_download_path, visited_urls=None):
    """
    Recursively traverses the Ninova directory structure and downloads lecture files.

    Params:
        base_download_path: the directory to which files need to be saved
    """

    if visited_urls is None:
            visited_urls = set()
    
    if url in visited_urls:
        print(f"Already visited: {url}, skipping.")
        return
    visited_urls.add(url) # TODO move this to the last line

    print(f"\nVisiting: {url}")
    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access {url}: {e}")
        return
    
    soup = BeautifulSoup(response.content,  "html.parser")

    # Determine the current path for saving files
    current_relative_path = extract_path_from_breadcrumb(soup)
    current_save_dir = os.path.join(base_download_path, current_relative_path)
    os.makedirs(current_save_dir, exist_ok=True)
    print(f"Saving files to: {current_save_dir}")

    # Find and download Lecture Files
    # Corrected the ID to target the table more accurately
    rows = soup.find_all('td')
    for row in rows:
        link_tag = row.find('a')
        img_tag = row.find('img')
        if link_tag and img_tag:
            # URL
            href = link_tag.get('href')
            absolute_url = urljoin(BASE_NINOVA_URL, href)

            if 'folder.png' in img_tag.get('src', ''):
                folder_name = link_tag.get_text()
                # TODO: preprocess the folder name
                new_folder_path = os.path.join(current_save_dir, folder_name)
                traverse_and_download(session, absolute_url, new_folder_path, visited_urls=visited_urls)
            elif 'ikon-pdf.png' in img_tag.get('src', ''):
                download_file(session, absolute_url, current_save_dir)
