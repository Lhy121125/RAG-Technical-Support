from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from langchain.docstore.document import Document

def load_url(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    total_len = 0
    subtitles_and_content = []

    title = soup.find("h1")


    content = []  # Initialize a list to collect content
    next_node = title.find_next_sibling() if title else None
    while next_node and next_node.name != 'h2':
        if isinstance(next_node, (NavigableString, Tag)):
            text = next_node.get_text(strip=True)  # Use get_text to handle both Strings and Tags
            if text:  # Avoid adding empty strings
                content.append(text)
        next_node = next_node.find_next_sibling()
    
    # Join the collected content and append it to subtitles_and_content
    content_text = "\n".join(content)
    total_len += len(text)
    subtitles_and_content.append(Document(page_content=content_text,
                                          metadata={
                                              "title": title.text.strip(),
                                              "subtitle": title.text.strip(),
                                              "source": url
                                          }))

        
    subtitles = soup.find_all("h2")
    if subtitles:
        for subtitle in subtitles:
            content = []
            next_node = subtitle.find_next_sibling()
            while next_node and next_node.name != 'h2':
                if isinstance(next_node, (NavigableString, Tag)):
                    text = next_node.text.strip()
                    if text:  # Avoid adding empty strings
                        content.append(text)
                next_node = next_node.find_next_sibling()
            content_text = "\n".join(content)
            total_len += len(content_text)
            subtitles_and_content.append(Document(page_content = content_text,
                metadata ={
                    "title": title.text,
                    "subtitle": subtitle.text,
                    "source": url
                })
        )
    else:
        # If no h2 tags are found, gather all text as a single content block
        content = [text for text in soup.stripped_strings if text]  # Collect all non-empty text
        content_text = "\n".join(content)
        total_len += len(text)
        subtitles_and_content.append(Document(page_content = content_text,
                metadata ={
                    "title": title.text,
                    "subtitle": title.text,
                    "source": url
                })
        )
    
    return subtitles_and_content, total_len

def load_urls(urls):
    documents = []
    for url in urls:
        documents.extend(load_url(url))
    return documents

url = "https://cran.r-project.org/doc/manuals/r-release/R-intro.html"

# print(load_urls([url]))

# Display the subtitles and their contents
# for item in subtitles_and_content:
#     print("\nSubtitle:", item["subtitle"])
#     print("Content:")
#     for content in item["content"]:
#         print(content)

# subtitles_and_content = load_url(url)   
# print(subtitles_and_content)