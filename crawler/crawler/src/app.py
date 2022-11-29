import json

from playwright.sync_api import sync_playwright

from utils import create_crawl_input
from local import crawl


def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event, indent=2))

    crawl_input = create_crawl_input('./crawl_input.txt')

    with sync_playwright() as pw:
        print('Opening browser..')
        browser = pw.chromium.launch(headless=True)
        print('Browser opened..')
        crawl(browser, crawl_input)
        browser.close()

    message = 'Hello World! Playwright!'
    return message
