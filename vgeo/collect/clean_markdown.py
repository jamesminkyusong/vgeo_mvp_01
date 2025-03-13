import os
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
from countries import countries


nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")


def check_and_assign_bias(bias_df, articles_df, idx):
    curr_article_domain = articles_df['domain'].iloc[idx]
    check_exist = bias_df[bias_df['source_url_normalized']==curr_article_domain.strip()]
    if len(check_exist)>0:
        curr_bias = check_exist['bias'].iloc[0]
    else:
        curr_bias = "center"
    return curr_bias

def chunk_document_for_sentiment(md_txt):
    n = len(md_txt)
    chunk_len = n//3
    return md_txt[chunk_len:2*chunk_len]

def spacy_sentiment_score(spacy_model, articles_df, md_chunk, idx):
    headline = articles_df['title'].iloc[idx]
    doc = spacy_model(headline)
    headline_sentiment = doc._.blob.polarity

    doc = spacy_model(md_chunk)
    chunk_polarity = doc._.blob.polarity

    return headline_sentiment * 0.3 + chunk_polarity*0.7

def spacy_ner(spacy_model, full_article):
    doc = spacy_model(full_article)
    ents = []
    ents_labels = []
    for ent in doc.ents:
        if ent.text not in ents and ent.label_ not in ["CARDINAL", "ORDINAL", "WORK_OF_ART", "PERCENT", "MONEY"]:
            ents.append(ent.text)
            ents_labels.append([ent.text, ent.label_])
    print(ents_labels)
    return ents_labels

def md_reader(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return content

if __name__ == "__main__":
    articles_df = pd.read_excel(r'/Users/jamessong/Repositories/VGeo/vgeo_repo/data/mvp_clean_urls_250114.xlsx')
    bias_df = pd.read_csv(r'/Users/jamessong/Repositories/VGeo/vgeo/vgeo/collect/bias_ratings.csv')

    clean_md_path = "/Users/jamessong/Repositories/VGeo/vgeo_repo/output/clean_2"
    fcount = 0
    bias_col = []
    sent_col =[]
    ner_col = []
    for f in sorted(os.listdir(clean_md_path)):
        if not f.endswith(".md"):
            continue
        
        # save bias
        bias_rating = check_and_assign_bias(bias_df, articles_df, fcount)
        bias_col.append(bias_rating)

        md_fp = os.path.join(clean_md_path, f)
        md_txt = md_reader(md_fp)
        md_chunk = chunk_document_for_sentiment(md_txt)
        score = spacy_sentiment_score(nlp, articles_df, md_chunk, fcount)
        sent_col.append(score)

        ents_labels = spacy_ner(nlp, md_txt)
        ner_col.append(ents_labels)
        fcount+=1


