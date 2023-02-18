from selenium import webdriver
import json
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
import time
from bs4 import BeautifulSoup
import requests


class pitchbook_scraper():

    def __init__(self, dso_lst, url, id):
        self.dsolist = dso_lst
        self.data = {}
        self.url = url
        self.id = id


    #Method to attach to previously opened Chrome Browser
    #Necessary because Pitchbook limits the number of new browsers you can log into, this allows us to bypass that
    def attach_to_session(self, executor_url, session_id):
        original_execute = WebDriver.execute
        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return original_execute(self, command, params)
        # Patch the function before creating the driver object
        WebDriver.execute = new_command_execute
        driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        driver.session_id = session_id
        # Replace the patched function with original function
        WebDriver.execute = original_execute
        return driver


    # USE THIS METHOD TO START RUNNING IF NOT LOGGED IN
    def start(self):
        driver = self.attach_to_session(self.url, self.id)
        url = driver.command_executor._url     
        session_id = driver.session_id 
        print(url)
        print(session_id)
        self.login(driver)

    #USE THIS METHOD IF ALREADY LOGGED IN
    def debug_start(self):
        driver = self.attach_to_session(self.url, self.id)
        url = driver.command_executor._url     
        session_id = driver.session_id 
        print(url)
        print(session_id)
        self.conduct_searches(driver)


    #Method to log in. 
    #Note: If captcha appears, you must manually complete 
    def login(self, driver):
        driver.get('https://my.pitchbook.com/')
        username = WebDriverWait(driver, timeout=30).until(lambda d: d.find_element(By.ID, "login-page-login"))
        password = driver.find_element(By.ID, "login-page-pass")
        username.send_keys("YOUR_EMAIL_HERE")
        time.sleep(1)
        password.send_keys("YOUR_PASSWORD_HERE")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        login_button = driver.find_element(By.CLASS_NAME, "submit-button")
        login_button.click()
        self.conduct_searches(driver)


    #Loops through list of companies (in this case DSOs), conducting searches on Pitchbook
    def conduct_searches(self, driver):
        search_bar = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.XPATH, "//*[@id='page-header']/div/div[2]/div/div/div/input")) 
        for name in self.dsolist:
            self.data[name] = {}
            self.data[name]["Company Name"] = name
            search_bar.clear()
            search_bar.send_keys(name)
            search_bar.send_keys(Keys.RETURN)
            try:
                pg_btn = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.XPATH, "//span[text()='Go to full profile']"))
                pg_btn.click()
                self.collect_data(driver, name)
            except TimeoutException:
                self.data[name] = "Limited or Missing Data"


        with open("dsos_data1.json", "w") as outfile:
            json.dump(self.data, outfile)


    #Collects data from numerous locations on company page
    #Checks for "Highlights" at top of page, which indicates that the page contains data
    def collect_data(self, driver, name):
        try:
            WebDriverWait(driver, timeout=15).until(lambda d: d.find_element(By.XPATH, "//div[text()='Highlights']"))
            self.data[name]["Total Raised"] = self.get_total_raised(driver)
            self.data[name]["Year Founded"] = self.get_year_founded(driver)
            self.data[name]["Post Valuation"] = self.get_post_val(driver)
            self.data[name]["Company Description"] = self.get_description(driver)
            self.data[name]["Deals"] = self.get_recent_deals(driver)
            self.data[name]["Comps"] = self.get_comps(driver)
        except TimeoutException:
            self.data[name] = "Limited or Missing Data"
        print(self.data[name])

    
    #Grabs total amount raised, if available
    def get_total_raised(self, driver):
        try:
            container = driver.find_element(By.XPATH, "//span[text()='Total Raised to Date']")
            parent_div = container.find_element(By.XPATH, "..")
            value_div = parent_div.find_element(By.XPATH, "following-sibling::div[1]")
            value = value_div.text
        except NoSuchElementException:
            value = "n/a"
        return(value)


    #Grabs company valuation, if available
    def get_post_val(self, driver):
        try:
            container = driver.find_element(By.XPATH, "//span[text()='Post Valuation']")
            parent_div = container.find_element(By.XPATH, "..")
            value_div = parent_div.find_element(By.XPATH, "following-sibling::div[1]")
            value = value_div.text
        except NoSuchElementException:
            value = "n/a"
        return(value)


    #Grabs year company was founded, if available
    def get_year_founded(self, driver):
        try:
            year_founded = driver.find_element(By.XPATH, "//span[text()='Year Founded']/../../../following-sibling::div/div")
            year = year_founded.text
        except NoSuchElementException:
            year = "n/a"
        return year


    #Grabs company description, if available
    def get_description(self, driver):
        try:
            description = driver.find_element(By.XPATH, "//div[text()='Description']/../following-sibling::p")
            desc = description.text
        except NoSuchElementException:
            description = "n/a"
        return desc


    #Grabs info on recent deals
    #Note: Deal amount and data are frequently not available
    def get_recent_deals(self, driver):
        deals = {}

        try:
            lst_of_deal_types = driver.find_elements(By.XPATH, "//section[@id='deal-history']/div/div/div/div/div/div/div/div/table/tbody/tr/td[2]/span/a")
            for i in range(len(lst_of_deal_types)):
                deals["Deal "+str(len(lst_of_deal_types)-i)] = {}
                deals["Deal "+str(len(lst_of_deal_types)-i)]["Deal Type"] = lst_of_deal_types[i].text
        except NoSuchElementException:
            print("No Deal Type Info")

        try:
            lst_of_deal_amounts = driver.find_elements(By.XPATH, "//section[@id='deal-history']/div/div/div/div/div/div/div/div/table/tbody/tr/td[4]")
            for i in range(len(lst_of_deal_amounts)):
                deals["Deal "+str(len(lst_of_deal_amounts)-i)]["Deal Amount"] = lst_of_deal_amounts[i].text
        except NoSuchElementException:
            print("No Deal Type Info")

        try:
            lst_of_deal_dates = driver.find_elements(By.XPATH, "//section[@id='deal-history']/div/div/div/div/div/div/div/div/table/tbody/tr/td[3]/span")
            for i in range(len(lst_of_deal_dates)):
                deals["Deal "+str(len(lst_of_deal_dates)-i)]["Deal Date"] = lst_of_deal_dates[i].text
        except NoSuchElementException:
            print("No Deal Type Info")

        try:
            lst = driver.find_elements(By.XPATH, "//div[text()='Deal Synopsis']/../following-sibling::p")
            print(len(lst))
            for i in range(len(lst)):
                deals["Deal "+str(len(lst)-i)]["Deal Description"] = lst[i].text
        except NoSuchElementException:
            print("No Deal Description Info")


        return(deals)


    #Grabs company comps
    def get_comps(self, driver):
        try:
            lst = driver.find_elements(By.XPATH, "//section[@id='similar-companies']/div/div/div/table/tbody/tr/td[3]/span/a")
            comps = []
            for item in lst:
                comps.append(item.text)
        except NoSuchElementException:
            comps = []
        return(comps)





company_list = ["YOUR_COMPANY_LIST_HERE"]
test = pitchbook_scraper(company_list, "YOUR_URL_HERE", "YOUR_SERVER_ID_HERE")
test.start()

    
