from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

def login_with_selenium(username, password, login_redirect_url):
    """
    Handles the login process using Selenium and returns an authenticated requests.Session.
    """
    # Configure WebDriver (e.g., Chrome)
    # Ensure chromedriver.exe is in your PATH or provide its path like:
    # service = webdriver.chrome.service.Service(executable_path="path/to/chromedriver.exe")
    # driver = webdriver.Chrome(service=service)
    driver = webdriver.Chrome() # Assumes chromedriver.exe is in PATH
    driver.set_window_size(1200, 800) # Optional: Set window size

    try:
        print(f"Navigating to login page: {login_redirect_url}")
        driver.get(login_redirect_url)

        # Wait for the username field to be visible and interactable
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_tbUserName"))
        )
        password_field = driver.find_element(By.ID, "ContentPlaceHolder1_tbPassword")
        login_button = driver.find_element(By.ID, "ContentPlaceHolder1_btnLogin")

        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button.click()

        # After clicking login, the page might redirect to Ninova.
        # Wait until the URL changes or a specific element on the Ninova page appears.
        print("Waiting for successful login and redirect to Ninova...")
        WebDriverWait(driver, 30).until(
            EC.url_contains("ninova.itu.edu.tr") # Or check for a specific element
        )
        print("Successfully logged in via Selenium.")

        # Now, transfer the cookies from Selenium to a requests session
        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        return session

    except Exception as e:
        print(f"An error occurred during login: {e}")
        return None
    finally:
        driver.quit() # Always close the browser




# Example Use
if __name__ == "__main__":
    # Get the student credentials
    import dotenv
    credentials = dotenv.dotenv_values('.env')
    USERNAME, PASSWORD = credentials['USERNAME'], credentials['PASSWORD']

    # Links to the ninova course
    BASE_NINOVA_URL = "https://ninova.itu.edu.tr"
    INITIAL_LOGIN_REDIRECT_URL = 'https://ninova.itu.edu.tr/Sinif/7165.106324' # Must be a link that will send u to login webpage

    # 1. Perform login with Selenium
    authenticated_session = login_with_selenium(
        USERNAME,
        PASSWORD,
        INITIAL_LOGIN_REDIRECT_URL,
    )

    if authenticated_session:
        print("Now you can login to Ninova using the login_with _selenium function")

