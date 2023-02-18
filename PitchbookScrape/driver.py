from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
import time
from bs4 import BeautifulSoup
import requests

#Starts driver, printing the URL and session_id
driver = webdriver.Chrome()
url = driver.command_executor._url     
session_id = driver.session_id 
print(url)
print(session_id)
input() #Keeps the session running