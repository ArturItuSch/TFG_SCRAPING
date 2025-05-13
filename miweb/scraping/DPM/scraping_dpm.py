import os
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time


def accept_cookies(driver):
    try:
        driver.get("https://dpm.lol/")
        time.sleep(5)
        agree_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[span[text()="AGREE"]]'))
        )
        agree_button.click()
        print("Cookies aceptadas.")
    except Exception as e:
        print("No se pudo aceptar cookies:", e)