from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time   
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, BASE_DIR)
from urllib.parse import urljoin
from scraping_gol import accept_cookies
from scraping.Scripts.driver import iniciar_driver

if __name__ == '__main__':
    driver = iniciar_driver()
    if driver:
        accept_cookies(driver)
        time.sleep(5)
    else:
        print("❌ El driver no se pudo iniciar correctamente.")
