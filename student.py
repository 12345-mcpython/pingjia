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
            "aihao": "aihaotechang.json",
            "quedian": "quedian.json",
            "xingge": "xingge.json",
            "youdian": "youdian.json",
            "zhiyeliebiao": "zhiyeliebiao.json",
            "zhuanye": "zhuanye.json",
            "zuoyouming": "zuoyouming.json",
            "tiao": "tiao.json",
            "pingyu": "pingyu.json"
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
            username.send_keys(self.config["student"]["username"])
            password.send_keys(self.config["student"]["password"])

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

    def click_to_pingjia(self):
        self.wait_and_click(By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/a')
        self.wait_and_click(
            By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/ul/li[1]/a')
    
    def click_to_pingyu(self):
        self.wait_and_click(By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/a')
        self.wait_and_click(By.XPATH, '//*[@id="mainMenu"]/ul/li[1]/ul/li[7]/a')

    def fill_evaluation_form(self):
        """Fill the evaluation form with randomized data"""
        try:
            # Prepare randomized data
            base_data = self._generate_base_data()

            # Submit form data
            script = f'$.post({{url: "https://gzzp.jlipedu.cn/eedu_high/r_saveHischGrowPlan.do", data: JSON.stringify({json.dumps(base_data, ensure_ascii=False)}), contentType: "application/json"}})'
            self.driver.execute_script(script)
            print("Form data submitted.")

        except Exception as e:
            print(f"Error filling form: {str(e)}")
            self.driver.save_screenshot("form_error.png")
            raise
        finally:
            self.driver.switch_to.default_content()
    
    def fill_pingyu_form(self):
        """Fill the pingyu form with randomized data"""
        try:
            # Prepare randomized data
            base_data = {"comment": random.choice(self.data["pingyu"])}

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

    def _generate_base_data(self) -> Dict[str, Any]:
        """Generate randomized form data structure"""
        zys = random.choices(self.data["zhuanye"], k=3)
        aiha = random.sample(self.data["aihao"], 3)
        zhi = random.sample(self.data["zhiyeliebiao"], 3)
        tiao_data = self.data["tiao"]

        return {
            "plan": {
                "myCharacter": random.choice(self.data["xingge"]),
                "myMotto": random.choice(self.data["zuoyouming"]),
                "myMerit": random.choice(self.data["youdian"]),
                "myDefect": random.choice(self.data["quedian"]),
                "myInterest": aiha[0],
                "myInterest2": aiha[1],
                "myInterest3": aiha[2],
                "myProfession1": zhi[0],
                "myProfession2": zhi[1],
                "myProfession3": zhi[2]
            },
            "subjectStr1": ",".join(map(str, range(1, 16))),
            "subjectStr2": ",".join(map(str, range(1, 16))),
            "subjectStr3": ",".join(map(str, range(1, 16))),
            "professions": [{"professionName": zy[0], "schoolName": zy[1]} for zy in zys],
            "goals": self._generate_goals(tiao_data)
        }

    def _generate_goals(self, tiao_data: List[List[str]]) -> List[Dict]:
        """Generate goals section with randomized content"""
        aspects = [
            ("思想品德", 2, tiao_data[0]),
            ("学业水平", 1, tiao_data[1]),
            ("身心健康", 3, tiao_data[2]),
            ("艺术素养", 4, tiao_data[3]),
            ("劳动与社会实践", 5, tiao_data[4])
        ]

        goals = []
        uid = 8
        for aspect_name, aspect_id, items in aspects:
            selected_items = random.sample(items, 4)
            for item in selected_items:
                goals.append({
                    "aspectName": aspect_name,
                    "finishStatus": 3,
                    "goal": item,
                    "aspect": aspect_id,
                    "_id": uid,
                    "_uid": uid,
                    "_state": "modified"
                })
                uid += 1
        return goals

    def run(self):
        try:
            self.login()
            time.sleep(2)  # 适当等待页面跳转
            self.fill_evaluation_form()
            time.sleep(2)
            self.driver.execute_script("location.reload()")
            self.click_to_pingjia()
            time.sleep(2)
            self.driver.execute_script("location.reload()")
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
