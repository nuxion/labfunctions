import timeit

from memory_profiler import profile


@profile
def test():
    # from dataproc.crawlers.page import crawl_page_async2 # 120 mb
    # from dataproc.crawlers.managers.page import AIOPageManager # 120 mb
    # from dataproc.crawlers.models import CrawlerBucketModel, PageModel # 24mb
    # from dataproc.crawlers.parsers.page import Page # 108 mb
    # from dataproc.crawlers.links_extractors import social_links # 26 mb
    # from dataclasses import dataclass
    # from typing import List

    # import dateparser
    # import pytz
    # from dataproc.crawlers.links_extractors import social_from_html # 26 mb

    # from dataproc.crawlers.parsers.article import ArticleData
    # from dataproc.crawlers.parsers.html import WebSite, parser_html
    # from dataproc.crawlers.parsers.url import url_base_name, url_norm
    ##from dataproc.words.ml_models import WordActor
    # from langdetect import detect as lang_detect

    # extract_links
    # import re
    # from dataclasses import dataclass
    # from datetime import datetime
    # from typing import List, Optional
    # from urllib.parse import urlparse

    # import Levenshtein as lv
    ## from dataproc.crawlers.http_client import HTTPError
    # from dataproc.crawlers.parsers.rss import find_rss_links, rss_parser # 20 mb
    # from dataproc.crawlers.parsers.sitexml import (get_sitemaps_from_url,
    #                                            parse_sites_xml)
    # from dataproc.crawlers.parsers.url import (SOCIALS_COM, URL_REGEX,
    #                                        url_base_name, url_norm)

    # import logging
    # from dataclasses import dataclass
    # from typing import List, Optional

    import feedparser
    from dataproc.crawlers import fetch  # 10 MB ... REVISAR
    from dataproc.crawlers.fetcher import HTTPError
    from dataproc.crawlers.http_client import Fetch
    from dataproc.crawlers.parsers import html
    from dateutil.parser import parse as dtparser

    print("hello")


if __name__ == "__main__":
    test()
