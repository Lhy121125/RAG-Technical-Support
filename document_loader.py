from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.document_loaders import UnstructuredURLLoader, SeleniumURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from bs4 import BeautifulSoup as Soup
from urllib.parse import urljoin, urlparse
from collections import deque
from scrap import *
import threading


import requests

# base_url = "https://docs.python.org/3/tutorial/index.html"
# base_url = "https://www.w3schools.com/java/java_syntax.asp"
# base_url = "https://developer.hashicorp.com/vagrant/tutorials/getting-started/getting-started-index"

def is_valid_url(url):
    """Check if a URL is valid and not an anchor or JavaScript call."""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and not url.startswith("javascript:") and not url.startswith("#") and not(url[-4] == '.' and not url.endswith(".com")) and not "forms" in url and not url.endswith('/') and not url.endswith("changelog.html") and not "wiki" in url 

def get_urls(base_url, depth=0):
    visited = set()
    to_visit = deque([(base_url, 0)])
    all_urls = set()

    while to_visit and len(all_urls) < 150:
        current_url, current_depth = to_visit.popleft()
        print(f"Visiting {current_url} at depth {current_depth}")
        if current_url in visited or current_depth > depth:
            continue
        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=2)  # Add a timeout for efficiency

            content_type = response.headers.get('Content-Type', '')
            # Only process if content type is HTML, for example
            if 'text/html' in content_type:
                soup = Soup(response.text, "html.parser")
                # Your processing logic here
            else:
                print(f"Skipping unsupported content type at {current_url}: {content_type}")
                continue  # Skip further processing and go to the next URL


            # soup = Soup(response.text, "html.parser")
            for link in soup.find_all('a', href=True):
                href = link['href']
                abs_url = urljoin(current_url, href)
                if is_valid_url(abs_url) and abs_url not in visited:
                    all_urls.add(abs_url)
                    if current_depth < depth:
                        to_visit.append((abs_url, current_depth + 1))
        except Exception as e:
            print(f"Failed to fetch {current_url}: {e}")

    return list(all_urls)


import threading

def get_num_links(url):
    try:
        response = requests.get(url, timeout=5)  # Adjust timeout as necessary
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)  # Find all <a> tags with an href attribute
        return len(links)  # Return the number of links
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return 0  # Return 0 if there's an error
    
def sort_urls_by_link_count(urls):
    # Fetch and count links for each URL
    url_counts = [(url, get_num_links(url)) for url in urls]
    
    # Sort URLs based on the number of links, descending
    sorted_urls = sorted(url_counts, key=lambda x: x[1], reverse=True)
    
    return sorted_urls


def load_url_with_timeout(url, docs, token_counter):
    try:
        new_docs, new_len = load_url(url)  # load_url needs to return both documents and their total length
        if token_counter["count"] + new_len < 500000:
            docs.extend(new_docs)
            token_counter["count"] += new_len
            return True
        else:
            print(f"Loaded {token_counter['count']} characters, stopping")
            token_counter["count"] = 500000  # Set the count to the limit to stop further loading
            return False
    except Exception as e:
        print(f"Failed to load {url}: {e}")
        return False

def data_loader(base_url):
    urls = get_urls(base_url)[:150]
    # TODO: Double check whether need to sort
    sorted_url = sort_urls_by_link_count(urls)
    print(f"Found {len(sorted_url)} URLs")
    docs = []
    token_counter = {"count": 0}  # Shared state
    for url,_ in sorted_url:
        if token_counter["count"] >= 500000:
            print("Token limit reached, stopping.")
            break  # Break the loop if the token limit is reached before starting a new thread

        print(f"Loading {url}")
        thread = threading.Thread(target=load_url_with_timeout, args=(url, docs, token_counter))
        thread.start()
        thread.join(timeout=2)  # Wait for 2 seconds for the thread to complete

        if thread.is_alive():
            print(f"Loading {url} took too long, skipping...")

    return docs



# def data_loader(base_url):
#     urls = get_urls(base_url)
#     # loader = UnstructuredURLLoader(urls=urls)
#     # docs = loader.load()
#     docs = []
#     for url in urls:
#         try:
#             docs.extend(load_url(url))
#         except Exception as e:
#             print(f"Failed to load {url}: {e}")
#     return docs

def splitter(base_url):
    data = data_loader(base_url)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=100,
        separators=["\n\n", "\n", "(?<=\. )", " ", ""]
    )
    
    docs = text_splitter.split_documents(data)
    # print(len(docs))
    # print(docs[0].page_content)
    return docs


# url = "https://cran.r-project.org/doc/manuals/r-release/R-intro.html#The-R-environment"
# urls = get_urls(url)
# print(len(urls))

