from chatbot.utils import validate_date_range
import requests, datetime, os, json
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################


##############################################[ENVIRONMENT VARIABLES]###########################################################

from dotenv import load_dotenv
load_dotenv()
ENGLISH_BOOMLIVE_API_KEY=os.getenv("ENGLISH_BOOMLIVE_API_KEY")
ENGLISH_FILTER_BOOMLIVE_ARTICLES = os.getenv("ENGLISH_FILTER_BOOMLIVE_ARTICLES")
ENGLISH_STORE_BOOMLIVE__ARTICLES=os.getenv("ENGLISH_STORE_BOOMLIVE__ARTICLES")
#----------------------------------------------------------------------------------------#
HINDI_BOOMLIVE_API_KEY = os.getenv("HINDI_BOOMLIVE_API_KEY")
BANGLA_BOOMLIVE_API_KEY=os.getenv("BANGLA_BOOMLIVE_API_KEY")
#---------------------------------------------------------------------------------------#
FILTER_BOOMLIVE_ARTICLES = os.getenv("FILTER_BOOMLIVE_ARTICLES")
STORE_BOOMLIVE__ARTICLES=os.getenv("STORE_BOOMLIVE__ARTICLES")
#----------------------------------------------------------------------------------------#

###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################


##############################################[ARTICLE STORE FUNCTIONS]#################################################################################################

async def store_multilingual_daily_articles(lang: str = None):
    """
    Fetch and store articles for the last 15 days asynchronously.

    Returns:
        list: List of article URLs stored for the specified period.
    """
    # Get today's date
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=15)).strftime('%Y-%m-%d')  # 15 days before today
    to_date = today.strftime('%Y-%m-%d')  # Today's date

    print(f"Storing articles from {from_date} to {to_date}...")
    try:
        # Use the existing function to store articles for the given range
        daily_articles = await store_multilingual_articles_custom_range(from_date, to_date)
        return daily_articles
    except Exception as e:
        print(f"Error in store_daily_articles: {str(e)}")
        return []
    
async def store_multilingual_articles_custom_range(from_date: str = None, to_date: str = None, lang: str = None):
    """
    Fetch and store articles based on a custom date range.

    Args:
        from_date (str): Start date in 'YYYY-MM-DD' format. Defaults to 6 months ago.
        to_date (str): End date in 'YYYY-MM-DD' format. Defaults to today.

    Returns:
        list: List of all article URLs processed.
    """
    s_id = ENGLISH_BOOMLIVE_API_KEY
    api_url_origin = 'https://boomlive.in' 
    if lang=='hi':
        s_id = HINDI_BOOMLIVE_API_KEY
        api_url_origin = 'https://hindi.boomlive.in'
    elif lang=='bn':
        s_id= BANGLA_BOOMLIVE_API_KEY
        api_url_origin = 'http://bangla.boomlive.in'
    # Initialize variables
    article_urls = []
    start_index = 0
    count = 20

    # Calculate default date range if not provided
    current_date = datetime.date.today()
    if not to_date:
        to_date = current_date.strftime('%Y-%m-%d')
    if not from_date:
        custom_months_ago = current_date - datetime.timedelta(days=180)  # Default to 6 months ago
        from_date = custom_months_ago.strftime('%Y-%m-%d')

    # Validate the date range
    if not validate_date_range(from_date, to_date):
        print("Invalid date range. Ensure 'from_date' <= 'to_date' and format is YYYY-MM-DD.")
        return []

    print(f"Fetching data from {from_date} to {to_date}....")
    index_name = "boom-latest-articles"

    while True:
        perpageurl = []
        print("Now start index is ", start_index)

        # Construct API URL with the custom range
        api_url = f'{api_url_origin}/dev/h-api/news?startIndex={start_index}&count={count}&fromDate={from_date}&toDate={to_date}'
        headers = {
            "accept": "*/*",
            "s-id": s_id
        }
        print(f"Current API URL: {api_url}")

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Break if no articles are found
            if not data.get("news"):
                break

            for news_item in data.get("news", []):
                url_path = news_item.get("url")
                if url_path:
                    article_urls.append(url_path)
                    perpageurl.append(url_path)

            # print(perpageurl)
            # # Filter and process URLs
            filtered_urls = await filter_urls_custom_range(json.dumps(perpageurl), lang)
            # print("These are filtered urls",filtered_urls)
            docsperindex = await fetch_docs_custom_range(filtered_urls)
            print(f"Processed {len(filtered_urls)} articles and {len(docsperindex)} chunks to add to Pinecone.")

            await store_docs_in_pinecone(docsperindex, filtered_urls, lang)
            start_index += count
        else:
            print(f"Failed to fetch articles. Status code: {response.status_code}")
            break

    return article_urls

###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################
###############################################################################################################################################
#########################################################################################################################################################

###########################################################[PROCESS ARTICLES]##############################################################################################
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain_pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings


async def filter_urls_custom_range(urls, lang):

    api_url = f"{FILTER_BOOMLIVE_ARTICLES}?urls={urls}&lang{lang}"
    headers = {
        "accept": "*/*",
        "Authorization": "adityaboom_requesting2024#",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(api_url, headers=headers, verify=False)
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("urls", [])
    except requests.RequestException as e:
        print(f"Error filtering URLs: {e}")
    return []


async def fetch_docs_custom_range(urls):
    data = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse only HTML content
            if 'text/html' not in response.headers.get('Content-Type', ''):
                print(f"Skipped non-HTML content at {url}")
                continue

            # Extract text using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3'])])

            document = Document(page_content=text, metadata={"source": url})
            data.append(document)
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            continue

    docs = text_splitter.split_documents(data)
    return docs


async def store_docs_in_pinecone(docs, urls, lang):
    index_name = {
        "hi": "hindi-boom-articles",
        "bn": "bangla-boom-articles"
    }.get(lang, "boom-latest-articles")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    print(f"Storing {len(docs)} document chunks to Pinecone index '{index_name}'...")
    pine_vs = Pinecone.from_documents(documents = docs, embedding = embeddings, index_name=index_name)
    print(f"Added {len(docs)} Articles chunks in the pinecone")
    await add_urls_to_database(json.dumps(urls), lang)
    print(f"Successfully stored documents. Associated URLs: {urls}")
    return pine_vs


async def add_urls_to_database(urls, lang):
    """
    Adds new URLs to the database by sending them to an external API endpoint.

    Args:
        urls (list): List of new URLs to be added to the database.

    Returns:
        str: A message indicating the result of the request.
    """

    api_url = f"{STORE_BOOMLIVE__ARTICLES}?urls={urls}&lang={lang}"
    headers = {
        "accept": "*/*",
        "Authorization": "adityaboom_requesting2024#",
        "Content-Type": "application/json"
    }
    
    try:
        # Send the POST request with the URLs in the payload
        response = requests.get(api_url, headers=headers, verify=False)

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            # You can log or process the response data as required
            # noofurls = len(urls)
            # print(urls, noofurls)
            print(f"Successfully added {len(urls)}URLs to the database." )
            return f"Successfully added URLs to the database."
        else:
            if(len(urls) == 0):
                return f"There are no urls to add"
            return f"There are no urls to add"
    except requests.RequestException as e:
        return f"An error occurred while adding URLs: {e}"
    

#########################################################################################################################################################