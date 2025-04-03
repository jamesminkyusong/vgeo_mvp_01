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
   - After building the main report, the pipeline generates three potential future scenarios, based on relevant extracted scenarios

![Brief Workflow Visualization](https://github.com/jamesminkyusong/vgeo_mvp_01/blob/main/assets/ss.png)

---
## Set Up
### collect.py

The pipeline use the same configuration file inbetween **collect** and **generate** to take user input and run with those settings. 
Initiating data collection requires adjusting below section of the configuration file `main/generate_settings.ini`

```ini
[COLLECT_GDELT_SETTING]
GDELT_SEARCH_QUERY=trump AND (tariff OR trade) AND ("international relations" OR "diplomatic tensions" OR trade) AND (Colombia OR Canada OR China OR EU OR Japan OR Mexico OR Korea)

# no space between commas
COUNTRIES= US,MX,CO,CA,KS,GM 
LANGUAGES= eng,spa,kor,deu

# YYYYMMDD
S_DATE = 20250328
E_DATE = 20250401

# Main topic of the search query for Taxonomy
MAIN_TOPIC = US_Trump_Trade_Tariff

# Master file to update collected scenarios between calls
[COLLECT_INPUT_PATH]
SCENARIO_DB = /Users/jamessong/Downloads/test/test_1/sc_df.xlsx

# Main Folder to save all future outputs
[COLLECT_OUTPUT_PATH]
EXPORT_PATH=/Users/jamessong/Downloads/test
```
**[refer to this documentation for an in depth understanding](https://github.com/jamesminkyusong/vgeo_mvp_01/blob/main/GDELT_configs_explanation.md)**
### Explanation:
- **GDELT_SEARCH_QUERY:** The query string used to search GDELT. Follows simple but specific format. Please refer to `GDELT_configs_explanation`
- **COUNTRIES & LANGUAGES:** Comma-separated values for filtering the search.
- **S_DATE and E_DATE:** Dates in YYYYMMDD format.
- **MAIN_TOPIC:** A short identifier for the main topic.
- **SCENARIO_DB:** PATH to EXCEL FILE which we use to save/update scenarios.
- **EXPORT_PATH:** PATH to FOLDER to save all outputs.


### generate.py
It is simpler to configure than collection as we only have to enter the TOPIC. If you need to break up the process between collect and generate, you can pass the paths manually as well.

```ini
[GENERATE_INPUT]
TOPIC="Trump's US trade and tariff policies in 2025 and potential geopolitical ramifications"

[GENERATE_CUSTOM_CONFIG]
CUSTOM_SELECTED_SCENARIO_PATH= 
EXPORT_PATH=
```

### Explanation:
- **TOPIC:** The query string used to initiate the report generation. Usually a short sentence or two to give the LLM a main topic to write about.
- Leave below blank UNLESS you are running collect.py and generate.py individually (breaking up the integrated collect_and_generate.py).
   - **CUSTOM_SELECTED_SCENARIO_PATH:** PATH to EXCEL FILE
   - **EXPORT_PATH:** PATH to FOLDER to save final report

## Running the Pipeline
Set your root directory as the parent of `main` and `vgeo`. Then, run the main generation script with:

```bash
python main/collect_and_generate.py
```

Above command will:
- Automatically load your configurations
- Collect articles and extract scenarios, resulting in 3 excel files:
   1. clean articles and generate features 
   2. extract, standardize and cluster scenarios 
   3. select few relevant scenarios based of TF-IDF

- Upon completion of collection, it will generate and save the final report into the specified EXPORT PATH
