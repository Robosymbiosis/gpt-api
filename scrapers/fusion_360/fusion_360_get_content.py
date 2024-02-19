from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import os


def expand_all_nodes(driver):
    expandable_nodes = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//li[@class='node' and @aria-expanded='false']")
        )
    )
    while expandable_nodes:
        for node in expandable_nodes:
            try:
                expand_collapse_button = node.find_element(By.CSS_SELECTOR, ".expand-collapse")
                driver.execute_script("arguments[0].click();", expand_collapse_button)
            except StaleElementReferenceException:
                print("Encountered a stale element reference while trying to expand nodes.")
                return  # Exit the function or handle as needed
        expandable_nodes = driver.find_elements(
            By.XPATH, "//li[@class='node' and @aria-expanded='false']"
        )


def safe_filename(filename):
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c == " "]).rstrip()


def process_node(driver, node, save_path):
    try:
        # Click the node to load its content
        driver.execute_script("arguments[0].click();", node)

        # Wait for the content to become available
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body-content")))

        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@itemprop='name']"))
        )
        title = safe_filename(title_element.text)
        filename = os.path.join(save_path, f"{title}.txt")

        content = driver.find_element(By.ID, "body-content").text
        url = driver.current_url

        with open(filename, "w") as file:
            file.write(url + "\n\n" + content)
        print(f"Content saved for node: {title}")
    except NoSuchElementException as e:
        print("Content not found for this node: ", e)
    except StaleElementReferenceException as e:
        print("Encountered a stale element reference: ", e)
    except Exception as e:
        print("An error occurred while processing the node: ", e)


def fetch_content_and_process(url, save_path):
    options = Options()
    options.add_argument("--headless")
    service = FirefoxService(executable_path="./geckodriver")
    driver = webdriver.Firefox(service=service, options=options)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "node")))
        expand_all_nodes(driver)

        content_nodes = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@data-type='guid']"))
        )
        for node in content_nodes:
            process_node(driver, node, save_path)
    finally:
        driver.quit()


if __name__ == "__main__":
    url = "https://help.autodesk.com/view/fusion360/ENU/"
    save_path = "fusion_360_API_documentation"
    fetch_content_and_process(url, save_path)
