# from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Milvus
import os

# Initialize Milvus Collection
def get_vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Milvus(
        embeddings,
        connection_args={
            "uri": os.getenv("ZILLIZ_CLOUD_URI"),
            "user": os.getenv("ZILLIZ_CLOUD_USERNAME"),
            "password": os.getenv("ZILLIZ_CLOUD_PASSWORD"),
            "secure": True,
        },
        collection_name="GermanyElection",
    )
    return vector_store

def insert_documents(docs):
    """Embeds and stores cleaned Markdown documents in Milvus."""
    vector_store = get_vector_store()
    vector_store.add_texts(docs)

def retrieve_relevant_documents(query, k=5):
    """Retrieves relevant documents from Milvus based on semantic similarity."""
    vector_store = get_vector_store()
    
    result = vector_store.similarity_search(query, k=k)
    return result