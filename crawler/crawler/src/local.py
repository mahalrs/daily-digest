import sys

from collections import deque

from playwright.sync_api import sync_playwright

from core import extract_page_content_and_urls
from utils import create_crawl_input, get_hash, normalize_url
from s3 import save_content


def crawl(browser, crawl_input):
    #
    # TODO:
    #         Start urls has categories from Google News; add them to output
    #         Ignore content from start urls; we only care about links
    #

    start_urls = set(crawl_input.start_urls)
    url_queue = deque(crawl_input.start_urls)
    seen_urls = set()

    count = 0

    while url_queue:
        if count >= 500:
            break
        count += 1

        (tag, url) = url_queue.popleft()
        url_hash = get_hash(url)
        if url_hash in seen_urls:
            continue
        seen_urls.add(url_hash)

        print('\nVisiting', url)

        out = extract_page_content_and_urls(browser, url, crawl_input)
        if out.err:
            print('Could not visit url', url)
            print('Error:', out.err.err)
            print(out.err.trace)
            continue

        print(out.status)
        #
        # TODO:
        #       Handle where status != 200
        #

        if out.real_url != url:
            seen_urls.add(get_hash(normalize_url(out.real_url)))

        for u in out.new_urls:
            url_queue.append((tag, normalize_url(u)))

        print('Title:', out.content.title)
        print('Tag:', tag)
        print('Found', len(out.new_urls), 'new urls')

        # Handle content only if not from initial start urls...
        if url not in start_urls:
            nurl = normalize_url(out.real_url)
            save_content(get_hash(nurl), nurl, out.content)

        #
        # TODO:
        #       Some checks:
        #           check if ip is blocked
        #           content type
        #           any further error handling


def main(argv):
    if not argv:
        print('Error: Crawl Input file must be specified.')

    crawl_input = create_crawl_input(argv[0])

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        crawl(browser, crawl_input)
        browser.close()


if __name__ == '__main__':
    main(sys.argv[1:])
