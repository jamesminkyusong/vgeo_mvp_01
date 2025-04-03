from vgeo.collect.search_and_scrape_gdelt import search_gdelt_queries, scrape_multiple
from vgeo.collect.clean_md import clean_multiple, clean_and_translate_multiple
from vgeo.collect.generate_features import compute_multiple_sentiment_score, extract_countries, check_and_assign_bias, convert_to_html, compute_and_select
from vgeo.collect.upload_vector_db import load_to_milvus
from vgeo.collect.scenarios_llm import scenario_boolean, only_scenarios_df, initial_scenario_json_generate, generate_clusters_context, scenario_clustering

import configparser

import os
import sys
from datetime import datetime
import asyncio
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

def load_configs():
    config = configparser.ConfigParser()
    config.read('main/generate_settings.ini')

    gdelt_search_str = config['COLLECT_GDELT_SETTING']['GDELT_SEARCH_QUERY'].strip()
    gdelt_countries =  config['COLLECT_GDELT_SETTING']['COUNTRIES'].strip()
    gdelt_languages =  config['COLLECT_GDELT_SETTING']['LANGUAGES'].strip()
    gdelt_sdate = config['COLLECT_GDELT_SETTING']['S_DATE'].strip()
    gdelt_edate = config['COLLECT_GDELT_SETTING']['E_DATE'].strip()
    main_topic = config['COLLECT_GDELT_SETTING']['MAIN_TOPIC'].strip()
    export_path = config['COLLECT_OUTPUT_PATH']['EXPORT_PATH'].strip()
    master_scenario_path = config['COLLECT_INPUT_PATH']['SCENARIO_DB'].strip()

    return gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic, export_path, master_scenario_path

# ensure hour
def build_input_query(search_str, countries, languages, s_date, e_date):
    formatted_query = search_str.replace(" ", "%20")
    final_query = f'{formatted_query}&sourcecountry={countries}&sourcelang={languages}&startdatetime={s_date}000000&enddatetime={e_date}000000&maxrecords=250'
    return final_query


async def search_and_scrape(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic):
    search_query = build_input_query(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate)
    
    # Execute synchronous search query (assuming search_gdelt_queries is synchronous)
    articles_df = search_gdelt_queries(search_query)
    print(f"Initiating collection of {len(articles_df)} articles. This will take a while...")
    
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

def generate_id_column(df, main_topic, gdelt_sdate, gdelt_edate):
    today_time_string = datetime.today().strftime('%y%m%d%H%M')
    id_base = f"{main_topic}_{today_time_string}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_A_"
    id_column = [id_base+str(i+1).zfill(3) for i in range(len(df))]
    df['Article_ID'] = id_column
    return df

def clean_df(df, main_topic, gdelt_sdate, gdelt_edate):
    df = generate_id_column(df, main_topic, gdelt_sdate, gdelt_edate)
    final_column = ["Article_ID", "title", "seendate", "domain", "url", "language", "sourcecountry", "platform", "main_topic", "bias_rating", "sentiment_score", "countries_mentioned", "content", "cleaned_content", "html_content"]
    df = df[final_column]
    df = df.fillna("")
    len_content_filter = df['cleaned_content'].apply(lambda x: len(x) >100)
    df = df[len_content_filter]
    return df

def extract_scenarios(df):
    extracted_scenarios = initial_scenario_json_generate(df)

    suggested_clustering= generate_clusters_context(extracted_scenarios)
    final_clustering = scenario_clustering(extracted_scenarios, suggested_clustering)

    cluster_info = pd.DataFrame(data=suggested_clustering.get("cluster_context"))
    sc_df = pd.DataFrame(data=final_clustering)
    return cluster_info, sc_df

def main():
    #load configs
    gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic, export_path, ms_path = load_configs()
    today_string = datetime.today().strftime('%y%m%d')
    today_time_string = datetime.today().strftime('%y%m%d%H%M')
    
    # search using GDELT
    articles_df = asyncio.run(search_and_scrape(gdelt_search_str, gdelt_countries, gdelt_languages, gdelt_sdate, gdelt_edate, main_topic))
    print(f"Done collecting {len(articles_df)} articles. Moving on to cleaning. This will take a while...")
    # clean and translate if neccessary using gemini
    eng_articles = articles_df[articles_df['language']=="English"].reset_index(drop=True)
    non_eng_articles = articles_df[articles_df['language']!="English"].reset_index(drop=True)
    
    clean_mds = clean_multiple(eng_articles['dirty_mds'].tolist())
    clean_eng_translated = clean_and_translate_multiple(non_eng_articles['dirty_mds'].tolist())
    
    eng_articles['cleaned_content'] = clean_mds
    non_eng_articles['cleaned_content'] = clean_eng_translated
    
    articles_df = pd.concat([eng_articles, non_eng_articles], ignore_index=True)
    articles_df['content'] = articles_df['dirty_mds'].tolist()

    # generate other features such as sentiment score, countries mentioned, bias
    articles_df = generate_features(articles_df, articles_df['cleaned_content'].tolist())
    
    final_df = clean_df(articles_df, main_topic, gdelt_sdate[2:], gdelt_edate[2:])
    final_df = scenario_boolean(final_df)
    
    # 00 create a folder for this task and an output folder named data
    folder_name = f"{today_time_string}_{main_topic}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_{str(len(final_df)).zfill(3)}"
    parent_folder_path = os.path.join(export_path, folder_name)
    os.makedirs(parent_folder_path, exist_ok=True)
    folder_path = os.path.join(parent_folder_path , "data")
    os.makedirs(folder_path, exist_ok=True)

    # 01_ first file is all articles with features and scenario boolean
    articles_file_name = f"01_{today_string}_{main_topic}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_{str(len(final_df)).zfill(3)}.xlsx"
    final_df.to_excel(os.path.join(folder_path, articles_file_name), index= False)

    print(f"Succesfully cleaned {len(final_df)} articles. Moving on to extracting and standardizing scenarios. This will take a while...")

    scenario_df = only_scenarios_df(final_df)
    cluster_info, scenario_df = extract_scenarios(scenario_df)
    scenario_df, selected_scenarios_df = compute_and_select(scenario_df)


    # 02_ second file is current task ALL scenarios
    with pd.ExcelWriter(os.path.join(folder_path, f"02_{today_string}_{main_topic}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_scenarios_{str(len(scenario_df)).zfill(3)}.xlsx")) as writer1:
        scenario_df.to_excel(writer1, sheet_name='Scenarios', index= False)
        cluster_info.to_excel(writer1, sheet_name='Cluster_Info', index= False)

    print(f"Succesfully extracted {len(scenario_df)} scenarios into {len(cluster_info)} clusters.")

    # 03_ third file is current task SELECTED scenarios (top 3 from each cluster)
    with pd.ExcelWriter(os.path.join(folder_path, f"03_{today_string}_{main_topic}_{gdelt_sdate[2:]}_{gdelt_edate[2:]}_selected_scenarios_{str(len(selected_scenarios_df)).zfill(3)}.xlsx")) as writer2:
        selected_scenarios_df.to_excel(writer2, sheet_name= 'Selected_Scenarios', index= False)
        cluster_info.to_excel(writer2, sheet_name= 'Cluster_Info', index= False)

    print(f"Succesfully selected {len(selected_scenarios_df)} for report generation guidance.")

    # needs to read and update a master_df
    master_scenario_df = pd.read_excel(ms_path)
    master_scenario_df = pd.concat([master_scenario_df, scenario_df], ignore_index=True)
    master_scenario_df.to_excel(ms_path, index= False)
    

    vector_db = load_to_milvus(final_df)
    return selected_scenarios_df, cluster_info, parent_folder_path

if __name__ == "__main__":
    main()