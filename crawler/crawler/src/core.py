import traceback

from common import CrawlErr, CrawlOutput, CrawlStatus, PageContent
from utils import normalize_url, url_is_from_any_domain, url_has_any_path


def block_aggressively(route):
    excluded_resource_types = ['stylesheet', 'image', 'font']

    if route.request.resource_type in excluded_resource_types:
        route.abort()
    else:
        route.continue_()


def get_links(page, crawl_input):
    atags = page.locator('a')
    urls = set()

    for i in range(atags.count()):
        el = atags.nth(i)
        href = el.evaluate('node => node.href')
        if not isinstance(href, str):
            continue

        # Filter to only urls within our target domains/paths
        url = normalize_url(href)
        if (url_is_from_any_domain(url, crawl_input.target_domains) and
                url_has_any_path(url, crawl_input.target_paths)):
            urls.add(url)

    # TODO:
    #       Check if we need to convert relative urls to absolute

    return urls


def extract_content(page):
    title = page.locator('title').nth(0).inner_text()
    return PageContent(
        title=title,
        html_content=page.content(),
    )


def extract_page_content_and_urls(browser, url, crawl_input):
    try:
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # TODO:
        #       add user-agent to the context
        #

        page.route('**/*', block_aggressively)
        response = page.goto(url, timeout=10000, wait_until='load')
        print('Page loaded...')

        status = CrawlStatus(
            code=response.status,
            text=response.status_text,
        )

        # Wait 2000ms, a reasonable time for js libraries to load and
        # complete client-side rendering or ajax calls
        page.wait_for_timeout(2000)
        print('Page rendering...')

        output = CrawlOutput(status=status,
                             content=extract_content(page),
                             new_urls=get_links(page, crawl_input),
                             url=url,
                             real_url=page.url,
                             err=None)

        context.close()

        return output
    except Exception as except_obj:
        context.close()

        err = CrawlErr(
            err=str(except_obj),
            trace=traceback.format_exc(),
        )

        return CrawlOutput(
            status=None,
            content=None,
            new_urls=None,
            url=url,
            real_url=None,
            err=err,
        )
