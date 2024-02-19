from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re


def expand_all_nodes(driver):
    while True:
        expandable_nodes = driver.find_elements(
            By.XPATH, "//li[@class='node' and @aria-expanded='false']"
        )
        if not expandable_nodes:
            break  # Exit loop if no expandable nodes are found

        for node in expandable_nodes:
            try:
                expand_collapse_button = node.find_element(By.CSS_SELECTOR, ".expand-collapse")
                driver.execute_script("arguments[0].click();", expand_collapse_button)
                time.sleep(0.01)  # Adjust based on the site's response time
            except Exception as e:
                print(f"Error expanding node: {e}")


def is_uuid_format(url):
    # Check if the URL contains a UUID in the specified format
    return bool(
        re.search(
            r"\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b",
            url,
        )
    )


def fetch_content_from_nodes_and_save_filtered_urls(url):
    options = Options()
    options.headless = True  # Set to False if you want to see the browser actions
    driver = webdriver.Firefox(options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "node")))

        # Expand all nodes
        expand_all_nodes(driver)

    finally:
        driver.quit()


url = "https://help.autodesk.com/view/fusion360/ENU/"
fetch_content_from_nodes_and_save_filtered_urls(url)
