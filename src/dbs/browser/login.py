import logging
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from dbs.gmail import Gmail
from dbs.settings import settings

logger = logging.getLogger(__name__)


class DbsAuthHandler:
    user_agent = " ".join(
        [
            "Mozilla/5.0 (X11; Linux x86_64)",
            "AppleWebKit/537.36 (KHTML, like Gecko)",
            "Chrome/120.0.0.0 Safari/537.36",
        ]
    )

    def __init__(self):
        self.webdriver = self.create_driver()

    def create_driver(self) -> webdriver.Chrome:
        logger.info("Creating Chrome driver")
        options = Options()
        # options.add_experimental_option("detach", True)
        options.add_argument(f"--user-agent={self.user_agent}")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)

    @staticmethod
    def get_otp() -> str:
        logger.info("Attempting to retrieve OTP")
        gmail = Gmail()
        message = gmail.wait_for_new_message()
        otp = gmail.extract_otp_from_message(message)

        if not otp:
            raise RuntimeError(f"OTP not found in email: {message.subject[:20]}")

        logger.info("OTP %s retrieved", "****" + otp[-2:])
        return otp

    def execute_auth_flow(
        self, driver: webdriver.Chrome, dbs_user_id: str, dbs_pin: str
    ):
        # login page
        logger.info("Opening login page")
        driver.get("https://internet-banking.dbs.com.sg/IB/Welcome")
        driver.find_element(By.NAME, "UID").send_keys(dbs_user_id)
        driver.find_element(By.NAME, "PIN").send_keys(dbs_pin)
        logger.info("Clicking 'Login' button")
        driver.find_element(By.CSS_SELECTOR, "[title^='Login']").click()

        # authentication page
        driver.switch_to.parent_frame()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "user_area"))
        )
        driver.switch_to.frame("iframe1")
        logger.info("Clicking 'Authenticate now' button")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "AuthenticatBtnId"))
        ).click()

        # authentication pop-up
        driver.switch_to.parent_frame()
        time.sleep(1)
        logger.info("Clicking 'Enter OTP Manually' link")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Enter OTP Manually"))
        ).click()

        # sms otp flow
        driver.switch_to.parent_frame()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "user_area"))
        )
        driver.switch_to.frame("iframe1")
        logger.info("Clicking 'Get OTP via SMS' button")
        driver.find_element(By.LINK_TEXT, "Send SMS OTP").click()
        driver.find_element(By.CSS_SELECTOR, "[title^='Get OTP via SMS']").click()

        # wait for SMS to be forwarded to email account
        # and then retrieve OTP from email body
        otp = self.get_otp()
        driver.find_element(By.NAME, "SMSLoginPin").send_keys(otp)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submitButton"))
        ).click()

        logger.info("Auth flow complete")

        return driver

    def login(self) -> webdriver.Chrome:
        try:
            return self.execute_auth_flow(
                driver=self.webdriver,
                dbs_user_id=settings.dbs_user_id,
                dbs_pin=settings.dbs_pin,
            )
        except Exception as err:
            logger.error("Error during login: %s", err)
            raise
