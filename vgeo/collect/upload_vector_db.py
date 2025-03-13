import os
import configparser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pymilvus import MilvusClient
from langchain_community.vectorstores import Milvus

config = configparser.ConfigParser()
config.read('vgeo/collect/collect_internal_settings.ini') # need to change path for not running in main

os.environ['GOOGLE_API_KEY']= config['API_KEYS']['GOOGLE_API_KEY'].strip()
os.environ['ZILLIZ_CLOUD_URI']= config['API_KEYS']['ZILLIZ_CLOUD_URI'].strip()
os.environ['ZILLIZ_CLOUD_USERNAME']= config['API_KEYS']['ZILLIZ_CLOUD_USERNAME'].strip()
os.environ['ZILLIZ_CLOUD_PASSWORD']= config['API_KEYS']['ZILLIZ_CLOUD_PASSWORD'].strip()
os.environ['ZILLIZ_CLOUD_API_KEY']= config['API_KEYS']['ZILLIZ_CLOUD_API_KEY'].strip()

def load_md_as_doc(md_text, title, seendate, domain, url):
    """
    Converts Markdown text into LangChain Document objects with metadata.
    Splits text into chunks while tracking character positions.
    """
    seentime = seendate[8:]
    seendate_only = seendate[:8]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

    # Split document while tracking positions
    split_docs = []
    char_start = 0  # Track character position
    count = 1
    for split in text_splitter.split_text(md_text):
        char_end = char_start + len(split)  # Track split end position
        split_docs.append(
            Document(
                metadata={
                    "title": title,
                    "seendate": seendate_only,
                    "seentime": seentime,
                    "domain": domain,
                    "url": url,
                    'split_start': char_start,
                    'split_end': char_end,
                    'chunk_number': count,
                    'chunk_total': len(text_splitter.split_text(md_text))
                },
                page_content=split
            )
        )
        char_start += len(split) - 150
        count += 1
    return split_docs


def load_all_md_as_docs(df):
    """
    Converts a DataFrame containing cleaned Markdown text into LangChain Document objects.
    """
    all_docs = []
    for idx, row in df.iterrows():
        md_text = row['content']  # Assuming cleaned Markdown is in this column
        title = row['title']
        seendate = row['seendate']
        seendate = seendate[:8]
        domain = row['domain']
        url = row["url"]

        res = load_md_as_doc(md_text, title, seendate, domain, url)
        all_docs.extend(res)  # Append all split documents
    return all_docs

def load_to_milvus(df):
    all_docs = load_all_md_as_docs(df)

    client = MilvusClient(
        uri=os.getenv("ZILLIZ_CLOUD_URI"),
        token=os.getenv("ZILLIZ_CLOUD_API_KEY")
    )
    
    client.drop_collection(
        collection_name="LangChainCollection"
    )
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    connection_args = {
        "uri": os.getenv("ZILLIZ_CLOUD_URI"),
        "user": os.getenv("ZILLIZ_CLOUD_USERNAME"),
        "password": os.getenv("ZILLIZ_CLOUD_PASSWORD"),
        "secure": True,
    }
    vector_db = Milvus.from_documents(all_docs, embeddings, collection_name= f"LangChainCollection",connection_args=connection_args)
    return vector_db


