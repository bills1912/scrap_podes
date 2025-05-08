import numpy as np
import pandas as pd
import requests, os
import time

from bs4 import BeautifulSoup

# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from selenium import webdriver

options = Options()
chromeOptions = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")

prefs = {'profile.managed_default_content_settings.images': 2,
         'disk-cache-size': 4096*15}
chromeOptions.add_experimental_option("prefs", prefs)

chrome_path = "F:/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"
main_window = webdriver.Chrome(chrome_path, options=chromeOptions)

FILENAME = 'alternative.csv'
FEATURES_NAME = 'Faskes'
FOLDER_SAVING_HTML = 'assets'
SOURCE = 'https://faskes.bpjs-kesehatan.go.id/aplicares/#/app/dashboard'
failed_properties = []

