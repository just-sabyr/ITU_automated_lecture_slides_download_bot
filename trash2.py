from login import login_with_selenium

import dotenv
credentials = dotenv.dotenv_values('.env')
USERNAME, PASSWORD = credentials['USERNAME'], credentials['PASSWORD']

# Links to the ninova course
BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324' # Must be a link that will send u to login webpage
DOWNLOAD_URL = 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g7911458'


# 1. Perform login with Selenium
session = login_with_selenium(
    USERNAME,
    PASSWORD,
    INITIAL_LOGIN_REDIRECT_URL
)


import requests
import os
from login import login_with_selenium # Assuming login.py is in the same directory

import dotenv
credentials = dotenv.dotenv_values('.env')
USERNAME, PASSWORD = credentials['USERNAME'], credentials['PASSWORD']

# Links to the ninova course
BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324' # Must be a link that will send u to login webpage
DOWNLOAD_URL = 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g7911458'

# Define the directory where you want to save the downloaded file
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 1. Perform login with Selenium
print("Attempting to log in...")
session = login_with_selenium(
    USERNAME,
    PASSWORD,
    INITIAL_LOGIN_REDIRECT_URL
)
print("Login successful. Initiating download...")

# 2. Use the session to download the PDF
try:
    with session as s:
        response = s.get(DOWNLOAD_URL, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Extract filename from Content-Disposition header or use a default
        filename = "downloaded_file.pdf"
        if 'Content-Disposition' in response.headers:
            cd = response.headers['Content-Disposition']
            # Find filename*=UTF-8'' or filename="filename.pdf"
            if "filename*=" in cd:
                import urllib.parse
                filename = urllib.parse.unquote(cd.split("filename*=")[1].strip())
            elif "filename=" in cd:
                filename = cd.split('filename=')[1].strip('"\'')
        
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded '{filename}' to '{DOWNLOAD_DIR}'! ✅")

except requests.exceptions.RequestException as e:
    print(f"An error occurred during download: {e} ❌")
except Exception as e:
    print(f"An unexpected error occurred: {e} ❌")


