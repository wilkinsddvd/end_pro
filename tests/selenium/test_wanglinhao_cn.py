import os

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

TARGET_URL = os.getenv("SELENIUM_TARGET_URL", "https://wanglinhao.cn/")


def _create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    chromedriver_path = "/usr/bin/chromedriver"
    if os.path.exists(chromedriver_path):
        return webdriver.Chrome(service=Service(chromedriver_path), options=options)
    return webdriver.Chrome(options=options)


@pytest.fixture(scope="module")
def driver():
    try:
        browser = _create_driver()
    except WebDriverException as exc:
        pytest.skip(f"无法启动 Chrome WebDriver: {exc}")
    browser.set_page_load_timeout(20)
    yield browser
    browser.quit()


def _open_homepage(driver):
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except WebDriverException as exc:
        message = str(exc)
        if "ERR_NAME_NOT_RESOLVED" in message or "ERR_INTERNET_DISCONNECTED" in message:
            pytest.skip(f"当前环境无法访问 {TARGET_URL}: {exc}")
        raise


def test_homepage_can_be_opened(driver):
    """首页可访问并完成加载。"""
    try:
        _open_homepage(driver)
    except TimeoutException as exc:
        pytest.fail(f"首页加载超时: {exc}")
    assert "wanglinhao.cn" in driver.current_url


def test_homepage_has_visible_body(driver):
    """首页主体内容可见。"""
    _open_homepage(driver)
    body = driver.find_element(By.TAG_NAME, "body")
    assert body.is_displayed()
    assert body.text.strip() != ""
