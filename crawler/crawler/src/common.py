# from dataclasses import dataclass
from typing import NamedTuple, List

# @dataclass
# class Address:
#     street: str
#     housenumber: int


class CrawlInput(NamedTuple):
    crawl_id: str
    start_urls: List[str]
    target_domains: List[str]
    target_paths: List[str]


class PageContent(NamedTuple):
    title: str
    html_content: str


class CrawlStatus(NamedTuple):
    code: int
    text: str


class CrawlErr(NamedTuple):
    err: str
    trace: str


class CrawlOutput(NamedTuple):
    status: CrawlStatus
    content: PageContent
    new_urls: List[str]
    url: str
    real_url: str
    err: CrawlErr
