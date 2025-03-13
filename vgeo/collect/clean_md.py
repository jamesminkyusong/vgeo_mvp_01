from pydantic import BaseModel, Field
from typing import Optional
import os
import pandas as pd
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import configparser

config = configparser.ConfigParser()
config.read('vgeo/collect/collect_internal_settings.ini')
os.environ['GOOGLE_API_KEY']= config['API_KEYS']['GOOGLE_API_KEY'].strip()

class ArticleSchema(BaseModel):
    main_content: Optional[str] = Field(
        description="Extract only the main body of the article, removing any advertisements, author bios, media links, or unrelated sections."
    )

def clean_multiple(results):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b")
    st_llm = llm.with_structured_output(ArticleSchema)
    clean_md_prompt = """
    You are an advanced document processor. The input is a Markdown news article that contains unnecessary content, advertisements, and web elements.

    Your goal is to extract **only** the **main body** of the article while preserving key formatting.

    **Instructions:**
    - Keep only the **core article content** (remove headers, footers, sidebars, ads, related news, hyperlinks, comments, and irrelevant navigation).
    - Maintain the structure with **paragraphs, bullet points, and bold/italic formatting** if present.
    - DO NOT edit or summarize any of the content from the article. Ensure full and complete extraction of the main body of the article.
    - If the input content is not a well scraped article return "No Content"
    """
    # Process each document
    cleaned_results = []
    for doc in results:
        if doc is None:
            cleaned_results.append("")
            continue
        try:
            prompt = f"{clean_md_prompt}\n\n{doc[0]}"
            result = st_llm.invoke(prompt)
            cleaned_results.append(result.main_content)
        except Exception as e:
            cleaned_results.append("")
    for n, c in enumerate(cleaned_results):
        try:
            if c != "" and len(c) <300:
                cleaned_results[n] = ""
            else:
                pass
        except:
            cleaned_results[n]= ""
    return cleaned_results
