import hashlib

from w3lib.url import canonicalize_url, url_query_cleaner
from urllib.parse import ParseResult, urlparse

from common import CrawlInput


def get_hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def normalize_url(url):
    safe_url = canonicalize_url(url)
    return url_query_cleaner(safe_url)


def url_is_from_any_domain(url, domains):
    host = parse_url(url).netloc.lower()
    if not host:
        return False
    domains = [d.lower() for d in domains]
    return any((host == d) or (host.endswith(f'.{d}')) for d in domains)


def url_has_any_path(url, paths):
    path = parse_url(url).path.lower()
    return any(path.startswith(p) for p in paths)


def url_has_any_extension(url, extensions):
    path = parse_url(url).path.lower()
    return any(path.endswith(ext) for ext in extensions)


def parse_url(url):
    if isinstance(url, ParseResult):
        return url
    return urlparse(url)


def create_crawl_input(fpath):
    start_urls = []
    target_d = []
    target_p = []

    with open(fpath, 'r', encoding='utf-8') as f:
        # extract start urls
        f.readline()
        while True:
            line = f.readline().strip()
            if not line:
                break
            line = line.split(' ')
            start_urls.append((line[0], line[1]))

        # extract target domains
        f.readline()
        while True:
            line = f.readline().strip()
            if not line:
                break
            target_d.append(line)

        # extract target paths
        f.readline()
        while True:
            line = f.readline().strip()
            if not line:
                break
            target_p.append(line)

    return CrawlInput(
        crawl_id='test123',
        start_urls=start_urls,
        target_domains=target_d,
        target_paths=target_p,
    )
