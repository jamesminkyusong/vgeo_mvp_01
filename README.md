# VGEO MVP README

This project implements a backend pipeline to collect, clean, and process news articles from the GDELT database, extract features (such as sentiment, countries mentioned, and bias ratings), and load the resulting data into a vector store. We then utilize RAG to generate a Geopolitical Risk & Opportunity Report and generate scenario sections based on the final report context.

---

## Overview

The pipeline performs the following steps:

**Collection:**  
   - Uses a configurable query to retrieve news articles from GDELT
   - Translate when applicable and cleans scraped html to Markdown using LLM (Gemini)
   - Computes sentiment scores, extracts mentioned countries, assigns bias ratings, and re-converts the content to HTML for Label Studio.
   - Automatically loads into the VectorDB

**Generation:**  
   - Grounded report based on the collected documents and real-time web searched documents during the report generation workflow
   - Report covers Historical Context, Recent Developments and Current Impacts & Ramifications 
   - After building the main report, the pipeline generates three potential future scenarios, only based on real-time web searched results

---

## collect.py
### Set Up
The pipeline uses INI files to take user input and run with those settings

```ini
[GDELT_SETTING]
GDELT_SEARCH_QUERY = (France OR Macron OR Germany OR Merz) AND (nuclear OR "nuclear umbrella" OR "nuclear Defense") AND (Trump OR Russia OR USA OR "United States of America")
COUNTRIES = US,FR,GM
LANGUAGES = eng,fra,deu
S_DATE = 20250311
E_DATE = 20250311
MAIN_TOPIC = France_Germany_Nuclear_Defense

[OUTPUT]
EXPORT_PATH = /Users/jamessong/Downloads/test
```

### Explanation:
- **GDELT_SEARCH_QUERY:** The query string used to search GDELT. Follows simple but specific format. Please refer to `GDELT_configs_explanation`
- **COUNTRIES & LANGUAGES:** Comma-separated values for filtering the search.
- **S_DATE and E_DATE:** Dates in YYYYMMDD format.
- **MAIN_TOPIC:** A short identifier for the main topic.
- **EXPORT_PATH:** Directory to save the output CSV file.

### Running the Pipeline

Set your root directory as the parent of main and vgeo and run the main collection script with:

```bash
python main/collect.py
```

The script will:
- Load the configuration from `main/collect_input.ini`.
- Search and scrape articles from GDELT.
- Clean the article content.
- Generate additional features (sentiment, bias, etc.).
- Upload the processed articles to Milvus.
- Generate scenario sections based on the main report.
- Save the final output as a CSV file named with a timestamp and other metadata.

### Sample Queries

Below are some sample search queries you might use:

1. **Example 1:**
   ```
   (France OR Macron OR Germany OR Merz) AND (nuclear OR "nuclear umbrella") AND (Trump OR Russia OR USA OR "United States of America")
   ```

2. **Example 2:**
   ```
   trump AND (tariff OR trade) AND ("international relations" OR "diplomatic tensions" OR trade) AND (Colombia OR Canada OR China OR EU OR Japan OR Mexico)
   ```

3. **Example 3:**
   ```
   ukraine AND (russia OR moscow) AND (Zelensky OR Zelenskyy OR Putin OR Trump) AND (ceasefire OR "peace talks" OR invasion)
   ```

### Currently Supported Languages & Countries

#### Languages (Max 7 at once)
- English (eng)
- Spanish (spa)
- Chinese (zho)
- German (deu)
- French (fra)
- Korean (kor)
- Ukrainian (ukr)
- Russian (rus)

####Countries (Max 7 at once)
- USA (US)
- Germany (GM)
- France (FR)
- Russia (RS)
- Ukraine (UP)
- Mexico (MX)
- Colombia (CO)
- Canada (CA)
- South Korea (KS)

### After Running Collection
- You should check the folder you specified as EXPORT_PATH in collect_input.ini

---

## generate.py
### Set Up
The pipeline uses INI files to take user input and run with those settings. It is simpler to configure than `collect_input.ini` as we only have to enter the TOPIC and EXPORT_PATH.

```ini
[API_KEYS]
OPENAI_API_KEY=
HF_KEY=
GOOGLE_API_KEY=
DEEPSEEK_KEY=
TAVILY_KEY=
LANGSMITH_KEY=
ZILLIZ_CLOUD_URI=
ZILLIZ_CLOUD_USERNAME=
ZILLIZ_CLOUD_PASSWORD=
ZILLIZ_CLOUD_API_KEY=

[INPUT] 
TOPIC="France and Germany's nuclear defense strategy and its geopolitcal ramifications"

[OUTPUT]
OUT_PATH=/Users/jamessong/Downloads/test/reports
```

### Running the Pipeline

Set your root directory as the parent of main and vgeo and run the main generation script with:

```bash
python main/generate.py
```

The script will:
- Generate and save the report into the specified EXPORT PATH