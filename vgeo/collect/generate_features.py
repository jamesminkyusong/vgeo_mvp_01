import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
import re
import random
import markdown
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile",
    "China", "Colombia", "Comoros", "Congo",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea",
    "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland",
    "France", "Gabon", "Gambia", "Georgia", "Germany",
    "Ghana", "Greece", "Grenada", "Guatemala", "Guinea",
    "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran",
    "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
    "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon",
    "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives",
    "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua",
    "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway",
    "Oman", "Pakistan", "Palau", "Palestine State", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain",
    "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
    "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste",
    "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "Uruguay", "Uzbekistan", "Vanuatu",
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

abv_countries = [["United Arab Emirates", "UAE"],["United Kingdom", "U.K."], ["U.S.","USA", "United States of America"]]


def remove_non_english(text: str) -> str:
    """
    Removes all non-English characters (including digits, punctuation, 
    whitespace, etc.) from the given text, leaving only a-z/A-Z.
    """
    return re.sub(r'[^A-Za-z]', '', text)

def chunk_document_for_sentiment(md_txt):
    n = len(md_txt)
    chunk_len = n//3
    return md_txt[chunk_len:2*chunk_len]

def compute_sentiment_score(spacy_model, title, md_txt):
    txt = remove_non_english(md_txt)
    txt = chunk_document_for_sentiment(txt)
    
    doc = spacy_model(title)
    headline_sentiment = doc._.blob.polarity

    doc = spacy_model(txt)
    chunk_polarity = doc._.blob.polarity
    score = headline_sentiment * 0.3 + chunk_polarity*0.7
    if score == 0:
        score = random.uniform(-0.2, 0.2)
    return score

def compute_multiple_sentiment_score(spacy_model, df, cleaned_results):
    sent_scores = []
    headlines = df['title'].tolist()
    for n, h in enumerate(headlines):
        md_txt = cleaned_results[n]
        try:
            score = compute_sentiment_score(spacy_model, h, md_txt)
        except:
            score = random.uniform(-0.2, 0.2)
        sent_scores.append(score)
    return sent_scores

def extract_countries(cleaned_results):
    all_countries = []
    for c in cleaned_results:
        curr_countries = []
        for acs in abv_countries:
            for ac in acs:
                if ac in c:
                    curr_countries.append(acs[0])
                    break
                else:
                    pass
        for country in countries:
            if country in c:
                curr_countries.append(country)
        all_countries.append(("|").join(set(curr_countries)))
    return all_countries

def check_and_assign_bias(bias_df, articles_df):
    biases = []
    for n, d in enumerate(articles_df['domain'].tolist()):
        check_exist = bias_df[bias_df['source_url_normalized']==d.strip()]
        if len(check_exist)>0:
            curr_bias = check_exist['bias'].iloc[0]
        else:
            curr_bias = "center"
        biases.append(curr_bias)
    return biases

def convert_to_html(cleaned_results):
    htmls= []
    for c in cleaned_results:
        html_text = markdown.markdown(c)
        htmls.append(html_text)
    return htmls

# features for scenarios

def process_actors(cell):
    if isinstance(cell, list):
        return ', '.join(cell)
    elif isinstance(cell, str):
        return cell
    else:
        return str(cell)

def process_description(description):
    return re.sub(r'[^\x00-\x7F]+', '', description)


def tf_idf_scoring(column):
    # Initialize a TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')

    # Fit and transform the "actors_text" column to compute TF-IDF matrix
    tfidf_actors = vectorizer.fit_transform(column)

    # Create a DataFrame with the TF-IDF scores for each keyword
    tfidf_df = pd.DataFrame(tfidf_actors.toarray(), columns=vectorizer.get_feature_names_out())
    return tfidf_df.sum(axis=1)

def compute_tf_idf(df):
    tf_idf_actors = tf_idf_scoring(df['actors'].apply(process_actors))
    tf_idf_desc = tf_idf_scoring(df['description'].apply(process_actors))
    df['tf_idf'] = (tf_idf_actors*0.66)+(tf_idf_desc*0.33)
    return df

def select_top_secnarios(df):
    top_sc = []
    for c in set(df['cluster_ID']):
        curr_df = df[df['cluster_ID']==c]
        top_scenarios = curr_df.sort_values(by='tf_idf', ascending=False)
        top_sc.append(top_scenarios[:3])
    
    for n, cdf in enumerate(top_sc):
        if n==0:
            fdf = cdf
        else:
            fdf = pd.concat([fdf, cdf], ignore_index=True)
    return fdf

def compute_and_select(df):
    tf_idf_df = compute_tf_idf(df)
    selected_df = select_top_secnarios(tf_idf_df)
    selected_df['BEST'] = ''

    final_scenario_df_column = ["Article_ID", "scenario_summary_title","description","actors","trigger_events","cluster_ID","tf_idf","BEST"]
    tf_idf_df = tf_idf_df[final_scenario_df_column[:-1]]
    selected_df =  selected_df[final_scenario_df_column]
    return tf_idf_df, selected_df