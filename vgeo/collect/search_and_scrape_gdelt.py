import os
import pandas as pd
import time
import re
from datetime import datetime, timedelta
from gdeltdoc import Filters, near, repeat, GdeltDoc
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode


def search_gdelt_queries(q):
    today_string = datetime.today().strftime('%Y-%m-%d')
    yesterday_string = (datetime.today() - timedelta(days=60)).strftime('%Y-%m-%d')

    # dummy
    f = Filters(
        start_date = yesterday_string,
        end_date = today_string,
        num_records = 250,
        keyword = ['a' ,'b'],
        repeat = repeat(3, "India")
    )
    f.query_params = [q]

    gd = GdeltDoc()
    
    articles_df = gd.article_search(f)
    articles_df = articles_df.drop_duplicates(subset='url')
    articles_df['title_norm'] = articles_df['title'].apply(lambda x: remove_non_english(x.lower()))
    articles_df = articles_df.drop_duplicates(subset= 'title_norm')
    # articles_df = articles_df[articles_df['language'] == "English"] 
    articles_df = articles_df[~articles_df['url'].str.contains('magazine|thestandard|newscentralasia|chinadaily|larouchepub|yahoo|jdsupra|sandiegosun|eurasiareview|insidenova|gdnonline|clutchfans|guide|fool', case=False, na=False)]
    articles_df = articles_df.reset_index(drop=True)

    return articles_df

def remove_non_english(text: str) -> str:
    """
    Removes all non-English characters (including digits, punctuation, 
    whitespace, etc.) from the given text, leaving only a-z/A-Z.
    """
    return re.sub(r'[^A-Za-z]', '', text)


async def scrape_url(url):
    config = CrawlerRunConfig(
        word_count_threshold=5,
        excluded_tags=['form', 'header', 'footer', 'nav'],
        exclude_social_media_links=True,
        exclude_external_images=True,
        magic=True,
        simulate_user=True,
        override_navigator=True
    )
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            if result != None and len(result.markdown) < 300:
                result = None
            return result
    except:
        return None
    
async def scrape_multiple(url_list):
    results = []
    for url in url_list:
        result = await scrape_url(url)
        if result is not None:
            results.append([result.markdown])
        else:
            results.append(None)
    return results

