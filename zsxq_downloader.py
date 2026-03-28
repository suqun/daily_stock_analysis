import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PHONE = os.getenv("ZSXQ_PHONE", "")
YOUR_PLANET_ID = os.getenv("ZSXQ_PLANET_ID", "")
SAVE_DIR = os.getenv("ZSXQ_DATA_DIR", "./data/zsxq")
COOKIE_FILE = os.path.join(SAVE_DIR, "cookies.json")
DELAY = 3

Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)


def save_cookies(context):
    cookies = context.cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    logger.info("Cookies 已保存")


def load_cookies(context):
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        logger.info("Cookies 已加载")
        return True
    return False


def need_login(page):
    page.goto("https://www.zsxq.com")
    time.sleep(DELAY)
    try:
        page.click("text=登录", timeout=3000)
        return True
    except:
        return False


def login(page):
    print("=" * 50)
    print("请在知识星球 App 收到验证码后，输入这里")
    print("=" * 50)

    page.click("text=登录")
    time.sleep(DELAY)

    page.click("text=手机号登录")
    time.sleep(DELAY)

    page.fill('input[placeholder="请输入手机号"]', PHONE)
    time.sleep(DELAY)

    page.click("text=获取验证码")
    time.sleep(1)

    code = input("验证码：")
    page.fill('input[placeholder="请输入验证码"]', code)
    time.sleep(1)

    page.click("text=登录")
    time.sleep(3)
    print("登录成功！")


def download_members():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        if not need_login(page):
            load_cookies(context)
            if need_login(page):
                login(page)
        else:
            login(page)

        save_cookies(context)

        print(f"进入星球 {YOUR_PLANET_ID}...")
        page.goto(f"https://www.zsxq.com/planets/{YOUR_PLANET_ID}")
        time.sleep(3)

        page.click("text=成员")
        time.sleep(3)

        print("点击导出全部成员...")
        page.click("text=导出全部成员")
        time.sleep(5)

        download = page.wait_for_download()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(SAVE_DIR, f"members_{timestamp}.xlsx")
        download.save_as(save_path)

        latest_path = os.path.join(SAVE_DIR, "members.xlsx")
        if os.path.exists(latest_path):
            os.remove(latest_path)
        download.save_as(latest_path)

        print(f"✅ 下载完成：{save_path}")
        browser.close()
        return save_path


def sync_to_database(excel_path: str):
    """下载完成后同步到数据库"""
    from src.services.vip_service import sync_members_from_excel

    logger.info(f"开始同步会员数据: {excel_path}")
    count = sync_members_from_excel(excel_path)
    logger.info(f"同步完成，新增/更新会员: {count} 人")


def auto_download():
    if not PHONE or not YOUR_PLANET_ID:
        logger.error("请在 .env 中配置 ZSXQ_PHONE 和 ZSXQ_PLANET_ID")
        return None

    try:
        excel_path = download_members()
        if excel_path:
            sync_to_database(excel_path)
        return excel_path
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return None


if __name__ == "__main__":
    auto_download()
