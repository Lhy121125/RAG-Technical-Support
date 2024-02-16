from document_loader import *


def load_to_elastic(docs, client):
    # data = data_loader(base_url)
    # docs = splitter(base_url)
    # clean the index before getting new data
    client.delete_by_query(index="docs", body={"query": {"match_all": {}}})
    id = 0
    for d in docs:
        doc = {
            'source': d.metadata["source"],
            'title': d.metadata["title"],
            'subtitle': d.metadata["subtitle"],
            'content': d.page_content
        }  
        resp = client.index(index="docs", id = id, document=doc)
        id += 1
    
def search(client, query):
    resp = client.search(
        index="docs", 
        body={
            "query": {
                "match": {
                    "content": {
                        "query" : query,
                    }
                }
            }
        }
    )  

    return resp