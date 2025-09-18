# https://gzzp.jlipedu.cn/eedu_base/r_changeUserSelfPwd.do

"""
Copyright (c) 2025 Laosun Studios.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import random
import json
from typing import List, Dict, Any
from pathlib import Path
import time
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge import options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import ddddocr

class WebAutomation:
    def __init__(self):
        self._init_driver()
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.data_path = Path("login")
        self.config = self._load_config()
        self.login_count = 3
        self._load_data_files()

    def _init_driver(self):
        """Initialize Edge WebDriver with proper settings"""
        print("Starting Edge...")
        edge_options = options.Options()
        edge_options.add_argument("--force-device-scale-factor=1")
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.set_window_size(1600, 1000)
        self.driver.set_window_position(0, 0)

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from JSON file"""
        with open("config.json", encoding="utf-8") as f:
            return json.load(f)

    def _load_data_files(self):
        """Load all required data files"""
        self.data_files = {
            "jiazhang": "jiazhang.json"
        }

        self.data = {}
        for key, filename in self.data_files.items():
            with open(self.data_path / filename, encoding="utf-8") as f:
                self.data[key] = json.load(f)

    def wait_and_click(self, by: By, value: str, timeout: int = 10):
        """Wait for element and click using ActionChains"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value)))
        webdriver.ActionChains(self.driver).move_to_element(
            element).click().perform()

    def find_element(self, by: By, value: str, timeout: int = 10) -> WebElement:
        """Find element with explicit wait"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value)))

    def find_elements(self, by: By, value: str, timeout: int = 10) -> List[WebElement]:
        """Find multiple elements with explicit wait"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value)))
        except TimeoutException:
            return []

    def handle_captcha(self, img_element: WebElement, input_element: WebElement):
        """Handle captcha recognition and input"""
        screenshot = img_element.screenshot_as_png
        captcha_text = self.ocr.classification(screenshot)
        input_element.send_keys(captcha_text)
        return captcha_text

    def login(self):
        """Handle login process"""
        url = "https://gzzp.jlipedu.cn/cas/login?service=https%3A%2F%2Fgzzp.jlipedu.cn%2Feedu_base%2FticketLogin.do"
        print("Opening website...")
        self.driver.get(url)

        try:
            # Find login elements
            username = self.find_element(By.ID, "username")
            password = self.find_element(By.ID, "password")
            captcha_img = self.find_element(By.ID, "verCodeImg")
            captcha_input = self.find_element(By.ID, "captcha")

            # Fill credentials
            username.send_keys(self.config["parent"]["username"])
            password.send_keys(self.config["parent"]["password"])

            # Handle captcha
            print("Processing captcha...")
            captcha_text = self.handle_captcha(captcha_img, captcha_input)
            print(f"Captcha recognized: {captcha_text}")

            # Submit login
            self.wait_and_click(By.CLASS_NAME, "log_submit")
            print("Login submitted.")
            time.sleep(.5)
            while self.login_count != 0:
                if not self.driver.current_url.startswith("https://gzzp.jlipedu.cn/cas/login"):
                    print(f"Login successful. Student {self.find_element(By.CLASS_NAME, 'userinfo').text}")
                    break
                else:
                    print("Login error! ")
                    print(f"Message: {self.find_element(By.ID, 'error_msg').text}.")
                    self.login_count -= 1
                    self.login()
            if self.login_count == 0:
                print("Login failed! ")
                sys.exit(1)
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Login failed: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            raise
    
    def click_to_pingyu(self):
        self.wait_and_click(By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/a')
        self.wait_and_click(By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/ul/li[7]/a')
    
    def fill_pingyu_form(self):
        """Fill the pingyu form with randomized data"""
        try:
            # Prepare randomized data
            base_data = {"comment": random.choice(self.data["jiazhang"])}

            # Submit form data
            script = f'$.post({{url: "https://gzzp.jlipedu.cn/eedu_high/r_saveComment.do", data: JSON.stringify({json.dumps(base_data, ensure_ascii=False)}), contentType: "application/json"}})'
            self.driver.execute_script(script)
            print("Pingyu data submitted.")
        except Exception as e:
            print(f"Error filling form: {str(e)}")
            self.driver.save_screenshot("form_error.png")
            raise
        finally:
            self.driver.switch_to.default_content()


    def run(self):
        try:
            self.login()
            time.sleep(2)
            self.fill_pingyu_form()
            time.sleep(2)
            self.driver.execute_script("location.reload()")
            self.click_to_pingyu()
            time.sleep(2)
            print("Filling successful!")
        finally:
            self.driver.quit()


if __name__ == "__main__":
    automation = WebAutomation()
    automation.run()
