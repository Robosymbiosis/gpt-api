"""Fetches and processes content from the Fusion 360 API documentation."""
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def expand_all_nodes(driver: webdriver.Firefox) -> None:
    """Expand all nodes in the Fusion 360 API documentation.

    Args:
        driver (webdriver.Firefox): The Firefox WebDriver instance to use.

    Returns:
        _type_: None
    """
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


def safe_filename(filename: str) -> str:
    """Sanitize a filename to use it as a valid filename.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c == " "]).rstrip()


def process_node(
    driver: webdriver.Firefox, node: webdriver.remote.webelement.WebElement, save_path: str
) -> None:
    """Process a node to extract and save its content.

    Args:
        driver (webdriver.Firefox): The Firefox WebDriver instance to use.
        node (webdriver.remote.webelement.WebElement): The node to process.
        save_path (str): The path to save the content to.
    """
    try:
        guid = node.get_attribute("href").split("=")[
            -1
        ]  # Extract GUID from the node's href attribute
        title = node.get_attribute("textContent").strip()  # Get the node's title
        title = safe_filename(title)  # Sanitize the title to use it as a filename
        filename = os.path.join(
            save_path, f"{guid} - {title}.txt"
        )  # Construct filename with GUID and title

        if os.path.exists(filename):
            print(f"Content for '{title}' (GUID: {guid}) has already been downloaded. Skipping...")
            return

        # Click the node to load its content
        driver.execute_script("arguments[0].click();", node)

        # Initialize an empty set to keep track of unique lines of text
        unique_content_set = set()

        # Define a recursive function to collect text from an element and its children
        def collect_text(element):
            # Add the element's text if it's not empty and not already in the set
            text = element.text.strip()
            if text and text not in unique_content_set:
                unique_content_set.add(text)
            # Recursively collect text from child elements
            for child in element.find_elements(By.XPATH, "./*"):
                collect_text(child)

        # Wait for the .caas_body element to become present and start text collection
        caas_body_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".caas_body"))
        )
        collect_text(caas_body_element)

        # Join the unique lines of text into one string, separated by newlines
        content = "\n".join(unique_content_set)

        if content:
            with open(filename, "w") as file:
                file.write(
                    driver.current_url + "\n\n" + content
                )  # Save the content along with the URL at the top
            print(f"Content saved for node: {title} (GUID: {guid})")
        else:
            print(f"No content found for {title} (GUID: {guid}).")
    except NoSuchElementException as e:
        print(f"Content not found for this node: {e}")
    except StaleElementReferenceException as e:
        print(f"Encountered a stale element reference: {e}")
    except Exception as e:
        print(f"An error occurred while processing the node: {node}, {e}")


def fetch_content_and_process(url: str, save_path: str) -> None:
    """Fetch content from the Fusion 360 API documentation and process it.

    Args:
        url (str): The URL of the documentation to fetch content from.
        save_path (str): The path to save the content to.
    """
    options = Options()
    options.add_argument("--headless")
    # service = FirefoxService(executable_path="./geckodriver")
    service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
    driver = webdriver.Firefox(service=service, options=options)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "node")))
        expand_all_nodes(driver)

        # Updated XPath to capture all relevant nodes
        content_nodes = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//li[@class='node']//a[contains(@href, '?guid=')]")
            )
        )
        for node in content_nodes:
            if type(node.get_attribute("textContent")) is None:
                continue
            title = node.get_attribute("textContent").strip()
            filename = os.path.join(save_path, f"{safe_filename(title)}.txt")

            if os.path.exists(filename):
                print(f"Content for '{title}' has already been downloaded. Skipping...")
                continue

            process_node(driver, node, save_path)
    finally:
        driver.quit()


if __name__ == "__main__":
    url = "https://help.autodesk.com/view/fusion360/ENU/"
    save_path = "fusion_360_API_documentation"
    fetch_content_and_process(url, save_path)
