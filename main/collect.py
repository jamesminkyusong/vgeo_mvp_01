from vgeo.collect.search_and_scrape_gdelt import search_gdelt_queries, scrape_multiple
from vgeo.collect.clean_md import clean_multiple
from vgeo.collect.generate_features import compute_multiple_sentiment_score, extract_countries, check_and_assign_bias, convert_to_html
from vgeo.collect.upload_vector_db import load_to_milvus

import configparser

import os
from datetime import datetime
import asyncio
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob


def load_configs():
    config = configparser.ConfigParser()
    config.read('main/collect_input.ini')

    gdelt_search_str = config['GDELT_SETTING']['GDELT_SEARCH_QUERY'].strip()
    gdelt_countries =  config['GDELT_SETTING']['COUNTRIES'].strip()
    gdelt_languages =  config['GDELT_SETTING']['LANGUAGES'].strip()
    gdelt_sdate = config['GDELT_SETTING']['S_DATE'].strip()
    gdelt_edate = config['GDELT_SETTING']['E_DATE'].strip()
    main_topic = config['GDELT_SETTING']['MAIN_TOPIC'].strip()
    export_path = config['OUTPUT']['EXPORT_PATH'].strip()
    return gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic, export_path

# ensure hour
def build_input_query(search_str, countries, languages, s_date, e_date):
    formatted_query = search_str.replace(" ", "%20")
    final_query = f'{formatted_query}&sourcecountry={countries}&sourcelang={languages}&startdatetime={s_date}000000&enddatetime={e_date}060000&maxrecords=250'
    return final_query


async def search_and_scrape(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic):
    search_query = build_input_query(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate)
    
    # Execute synchronous search query (assuming search_gdelt_queries is synchronous)
    articles_df = search_gdelt_queries(search_query)
    print(len(articles_df))
    # Await the asynchronous scraping
    mds = await scrape_multiple(articles_df['url'])
    articles_df['dirty_mds'] = mds
    articles_df['platform'] = ["gdelt" for _ in range(0, len(articles_df))]
    articles_df['main_topic'] = [main_topic for _ in range(0, len(articles_df))]

    return articles_df

def generate_features(df, cleaned_results):
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("spacytextblob")
    bias_df = pd.read_csv("vgeo/collect/bias_ratings.csv")

    sent_scores = compute_multiple_sentiment_score(nlp, df, cleaned_results)
    extracted_countries = extract_countries(cleaned_results)
    bias_ratings = check_and_assign_bias(bias_df, df)
    html_texts = convert_to_html(cleaned_results)
    df['sentiment_score']=sent_scores
    df['countries_mentioned']=extracted_countries
    df['bias_rating']= bias_ratings
    df['html_content'] = html_texts
    return df

def clean_df(df):
    final_column = ["title", "seendate", "domain", "url", "language", "sourcecountry", "platform", "main_topic", "bias_rating", "sentiment_score", "countries_mentioned", "content", "html_content"]
    df = df[final_column]
    df = df.fillna("")
    len_content_filter = df['content'].apply(lambda x: len(x) >100)
    df = df[len_content_filter]
    return df

# search_scrape_and_save
if __name__ == "__main__":
    #load configs
    gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic, export_path = load_configs()
    
    # search using GDELT
    articles_df = asyncio.run(search_and_scrape(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic))
    
    # clean using gemini
    clean_mds = clean_multiple(articles_df['dirty_mds'].tolist())
    articles_df['content'] = clean_mds
    
    # generate other features such as sentiment score, countries mentioned, bias
    articles_df = generate_features(articles_df, clean_mds)
    
    final_df = clean_df(articles_df)
    vector_db = load_to_milvus(final_df)

    today_string = datetime.today().strftime('%y%m%d')
    filename = f"{today_string}_{main_topic}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_{str(len(articles_df)).zfill(3)}.csv"
    final_df.to_csv(os.path.join(export_path, filename), index= False, encoding= 'utf-8')
    

