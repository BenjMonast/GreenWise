from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

# Replace these with your actual login credentials
username = ''
password = ''

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Open the login page

driver.get("https://apps.carboncloud.com/climatehub/")
driver.find_element(By.CSS_SELECTOR, "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
driver.find_element(By.CSS_SELECTOR, "div > header > div > button[role=\"button\"]:first-child").click()

# Find the username and password fields and enter the login credentials
username_field = driver.find_element(By.ID, "username")  # Replace with the actual ID or name
username_field.send_keys(username)
driver.find_element(By.CSS_SELECTOR, "div button").click()
time.sleep(0.5)

password_field = driver.find_element(By.ID, "password")  # Replace with the actual ID or name
password_field.send_keys(password)
driver.find_element(By.CSS_SELECTOR, "button[type=\"submit\"]").click()
time.sleep(1)

driver.get("https://apps.carboncloud.com/climatehub/search?q=&market=USA&gate=StoreShelf/")
time.sleep(1)
driver.find_element(By.CSS_SELECTOR, "#StoreShelf").click()
time.sleep(5)

out = ""

for i in range(494):
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        c1 = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        c2 = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        c3 = row.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.split("\n")[0]
        out += f"{c1}|{c2}||||{c3}\n"

    driver.find_element(By.CSS_SELECTOR, "a[title=\"Next page\"]").click()
    time.sleep(0.5)

    if i != 0 and i % 50 == 0:
        with open("data.csv", "w") as f:
            f.write(out)

with open("data.csv", "w") as f:
    f.write(out)

driver.quit()
