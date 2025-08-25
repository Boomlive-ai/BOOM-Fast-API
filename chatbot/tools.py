import re
import requests
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage

# Initialize the LLM
llm = ChatOpenAI(temperature=0, model_name='gpt-4.1-mini')

def generate_questions_batch(articles, lang='en'):
    """
    Generates concise questions for a batch of articles using an LLM.

    Parameters:
        articles (list): List of article dictionaries.

    Returns:
        list: A randomly ordered list of questions generated from all the articles.
    """
    print("generate_questions_batch invoked", articles)

    # Construct a single prompt for all articles in the batch
    input_prompts = []
    for i, article in enumerate(articles):
        title = article.get("heading", "Untitled Article")
        description = article.get("description", "No description available.")
        story = article.get("story", "No story content available.")
        input_prompts.append(f"""
        Article {i + 1}:
        Title: {title}
        Description: {description}
        Story Excerpt: {story[:500]}... (truncated for brevity)
        Use Language corresponding to this language code:{lang}
        Generate two concise,interesting, specific and relevant questions (under 60 characters) based on the article content which user want to know about latest articles.
        Ensure the questions meet the following criteria:
        1. Focus on actionable or data-driven information from the article.
        2. Do not include the article title "Aticle n", article labels, or headings in the questions or article numbers or question numbers.
        3. Do not use bullet points and article numbers.
        4. Return only the questions (no introductory text or labels).
        5. Keep the questions under 60 characters each.
        6. Should have a emoji related to question as prefix
        7. Return the questions in a shuffled order.
        8. Use Language corresponding to this language code:{lang}

        Provide only the list of questions which have proper context for user to understand question, as shown in the example.
        """)

    # Combine all prompts into one input
    batch_prompt = "\n".join(input_prompts)

    try:
        # Create a HumanMessage object for the LLM
        message = HumanMessage(content=batch_prompt)

        # Invoke the LLM with the message
        response = llm.invoke([message])

        # Extract and clean the questions from the response
        questions = response.content.strip().split("\n")
        cleaned_questions = [q.strip() for q in questions if q.strip()]

        return cleaned_questions
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []

def fetch_questions_on_latest_articles_in_Boomlive(language="en"):
    """
    Fetches the latest articles from the IndiaSpend API and generates up to 20
    concise questions in batches.

    Returns:
        dict: A dictionary containing all questions from the articles in a single list.
    """

    print("fetch_questions_on_latest_articles_in_Boomlive invoked")
    urls = []
    print(f"Language: {language}")

    base_urls = {
        "en": "https://www.boomlive.in",
        "hi": "https://hindi.boomlive.in",
        "bn": "https://bangla.boomlive.in"
    }
       # Define language-specific SIDs
    sids = {
        "en": "1w3OEaLmf4lfyBxDl9ZrLPjVbSfKxQ4wQ6MynGpyv1ptdtQ0FcIXfjURSMRPwk1o",
        "hi": "A2mzzjG2Xnru2M0YC1swJq6s0MUYXVwJ4EpJOub0c2Y8Xm96d26cNrEkAyrizEBD",
        "bn": "xgjDMdW01R2vQpLH7lsKMb0SB5pDCKhFj7YgnNymTKvWLSgOvIWhxJgBh7153Mbf"
    }


      # Select the appropriate base URL and SID
    base_url = base_urls.get(language, base_urls["en"])
    sid = sids.get(language, sids["en"])
    
    api_url = 'https://boomlive.in/dev/h-api/news'
    headers = {
        "accept": "*/*",
        "s-id": sid
    }

     # Add language parameter to API call if not English
    if language != "en":
        api_url = f"{base_url}/dev/h-api/news"
    print(f"Fetching articles from API: {api_url}")

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if response.status_code == 200:
            # Break if no articles are found
            if not data.get("news"):
                return {"questions": []}
            # Filter URLs containing 'fact-check' in the URL path
            for news_item in data.get("news", []):
                url_path = news_item.get("url")
                if url_path and f"{base_url}/fact-check/" in url_path:
                    urls.append(url_path)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch articles: {e}")
        return {"error": f"Failed to fetch articles: {e}"}

    # If no relevant articles are found
    if not urls:
        print("No 'fact-check' articles found.")
        return {"questions": []}

    # Fetch corresponding articles
    articles = data.get("news", [])
    filtered_articles = [article for article in articles if article.get("url") in urls]

    # Limit articles to 10 (as each article generates 2 questions)
    filtered_articles = filtered_articles[:10]

    # Generate questions in a single batch
    questions = generate_questions_batch(filtered_articles, language)

    # Ensure only 20 questions are returned
    return {"questions": questions[:20]}



def fetch_articles_based_on_articletype(articleType):
    urls=[]
    api_url = 'https://boomlive.in/dev/h-api/news'
    headers = {
        "accept": "*/*",
        "s-id": "1w3OEaLmf4lfyBxDl9ZrLPjVbSfKxQ4wQ6MynGpyv1ptdtQ0FcIXfjURSMRPwk1o"
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if response.status_code == 200:
            # Break if no articles are found
            if not data.get("news"):
                return {"questions": []}
            # Filter URLs containing 'fact-check' in the URL path
            for news_item in data.get("news", []):
                url_path = news_item.get("url")
                if url_path and f"https://www.boomlive.in/{articleType}" in url_path:
                    urls.append(url_path)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch articles: {e}")
        return {"error": f"Failed to fetch articles: {e}"}
    
        # If no relevant articles are found
    if not urls:
        print(f"No {articleType} articles found.")
        return [{"urls": []}]
        
    return {"urls": urls}



def fetch_articles_based_on_articletype_and_language(articleType, language="en"):
    """
    Fetch articles based on article type and language.
    
    Args:
        articleType (str): Type of articles to fetch (e.g., "fact-check")
        language (str): Language code ("en" for English, "hi" for Hindi, "bn" for Bengali)
    
    Returns:
        dict: Dictionary containing URLs of articles or error message
    """
    urls = []
    
    # Define base URL based on language
    base_urls = {
        "en": "https://www.boomlive.in",
        "hi": "https://hindi.boomlive.in",
        "bn": "https://bangla.boomlive.in"
    }
    
    # Define language-specific SIDs
    sids = {
        "en": "1w3OEaLmf4lfyBxDl9ZrLPjVbSfKxQ4wQ6MynGpyv1ptdtQ0FcIXfjURSMRPwk1o",
        "hi": "A2mzzjG2Xnru2M0YC1swJq6s0MUYXVwJ4EpJOub0c2Y8Xm96d26cNrEkAyrizEBD",
        "bn": "xgjDMdW01R2vQpLH7lsKMb0SB5pDCKhFj7YgnNymTKvWLSgOvIWhxJgBh7153Mbf"
    }
    
    # Select the appropriate base URL and SID
    base_url = base_urls.get(language, base_urls["en"])
    sid = sids.get(language, sids["en"])
    
    # API URL remains the same, but we'll handle language-specific content later
    api_url = 'https://boomlive.in/dev/h-api/news'
    headers = {
        "accept": "*/*",
        "s-id": sid
    }
    
    # Add language parameter to API call if not English
    if language != "en":
        api_url = f"{api_url}?lang={language}"
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if response.status_code == 200:
            # Break if no articles are found
            if not data.get("news"):
                return {"urls": []}
                
            # Filter URLs containing articleType in the URL path
            for news_item in data.get("news", []):
                url_path = news_item.get("url")
                if url_path and f"{base_url}/{articleType}" in url_path:
                    urls.append(url_path)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch articles: {e}")
        return {"error": f"Failed to fetch articles: {e}"}
    
    # If no relevant articles are found
    if not urls:
        print(f"No {articleType} articles found for {language} language.")
        return {"urls": []}
        
    return {"urls": urls}



from datetime import datetime, timedelta
import requests

def fetch_recent_articles(article_type: str, language: str = "en", days: int = 45) -> dict:
    """
    Fetch articles from the past `days` based on article type and language.

    Args:
        article_type (str): Type of articles to fetch (e.g., "fact-check")
        language (str): Language code ("en", "hi", "bn")
        days (int): Number of past days to fetch articles for

    Returns:
        dict: Dictionary containing list of article URLs or error message
    """
    # Setup
    urls = []
    start_index = 0
    count = 20
    today = datetime.today().date()
    from_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
    to_date = today.strftime('%Y-%m-%d')

    # Language-specific domains and SIDs
    base_urls = {
        "en": "https://www.boomlive.in",
        "hi": "https://hindi.boomlive.in",
        "bn": "https://bangla.boomlive.in"
    }
    sids = {
        "en": "1w3OEaLmf4lfyBxDl9ZrLPjVbSfKxQ4wQ6MynGpyv1ptdtQ0FcIXfjURSMRPwk1o",
        "hi": "A2mzzjG2Xnru2M0YC1swJq6s0MUYXVwJ4EpJOub0c2Y8Xm96d26cNrEkAyrizEBD",
        "bn": "xgjDMdW01R2vQpLH7lsKMb0SB5pDCKhFj7YgnNymTKvWLSgOvIWhxJgBh7153Mbf"
    }

    base_url = base_urls.get(language, base_urls["en"])
    sid = sids.get(language, sids["en"])
    api_url = f"{base_url}/dev/h-api/news"

    headers = {
        "accept": "*/*",
        "s-id": sid
    }

    # Fetch in batches
    while True:
        paged_url = f"{api_url}?startIndex={start_index}&count={count}&fromDate={from_date}&toDate={to_date}"
        try:
            response = requests.get(paged_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not data.get("news"):
                break

            for news_item in data.get("news", []):
                url_path = news_item.get("url")
                if url_path and f"{base_url}/{article_type}" in url_path:
                    urls.append(url_path)

            start_index += count
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch articles: {e}"}

    return {"urls": urls}
