from document_loader import *
import openai
# from langchain.vectorstores import Chroma
import shutil
import os
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from langchain_community.vectorstores import FAISS

# OPENAI_API_KEY = "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"


def vectorizor(docs, embedding):
    # splits = splitter(base_url)
    # persist_directory = 'docs/chroma/'

    # if os.path.exists(persist_directory):
    #     shutil.rmtree(persist_directory)
    #     print(f"Deleted {persist_directory}")
    # else:
    #     print(f"{persist_directory} does not exist")
    vectordb = FAISS.from_documents(
        documents = docs,
        embedding = embedding,
        # persist_directory = persist_directory
    )
    return vectordb

# def vec_search(base_url, embedding):
#     persist_directory = 'docs/chroma/'
    
#     vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
#     return vectordb

# embedding = OpenAIEmbeddings()
# vector_db = vec_search("https://docs.python.org/3/tutorial/index.html", embedding)
# search_result = vector_db.similarity_search("for loop", k=4)
# print(type(search_result[0].page_content))
# print(search_result[0].page_content)
