import asyncio

from dataproc.conf import Config
from dataproc.crawlers.page import CrawlPageTask, crawl_page_async2, crawl_page_sync
from dataproc.crawlers.page_transform import transform_page
from dataproc.utils import Timeit
from dataproc.words.parsers import load_stop

# from dataproc.words.parsers import doc_parser, load_stop

stopw = set(load_stop(lang="any"))

u = "https://www.perfil.com/noticias/coronavirus/nuevos-casos-coronavirus-7-de-enero-de-2022.phtml"

cpt = CrawlPageTask(url=u)
cpt.strategy = "direct"


@Timeit
def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


async def main():
    r = await crawl_page_async2(cpt)


print("=" * 20)
print("Sync call")
print("=" * 20)
p = crawl_page_sync(cpt)
print()
print("=" * 20)
print("ASync call")
print("=" * 20)
run()


transform_page(p, stopw)
