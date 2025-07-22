from login import login_with_selenium
from downloader import traverse_and_download

import dotenv


credentials = dotenv.dotenv_values('.env')
USERNAME, PASSWORD = credentials['USERNAME'], credentials['PASSWORD']

# Links to the ninova course
BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324' # Must be a link that will send u to login webpage
COURSE_URL = 'https://ninova.itu.edu.tr/tr/dersler/bilgisayar-bilisim-fakultesi/21/blg-252e/ekkaynaklar?g397'

# 1. Perform login with Selenium
session = login_with_selenium(
    USERNAME,
    PASSWORD,
    INITIAL_LOGIN_REDIRECT_URL,
)

traverse_and_download(session, COURSE_URL, 'OOP')