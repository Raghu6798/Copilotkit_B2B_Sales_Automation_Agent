import os
from dotenv import load_dotenv
import json
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log

load_dotenv()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    before=before_log(logger, "INFO"),
    after=after_log(logger, "ERROR")
)
def _execute_with_retry(request_func, *args, **kwargs):
    return request_func(*args, **kwargs)

def google_search(query):
    """
    Performs a Google search using the provided query.
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'content-type': 'application/json'
    }
    response = _execute_with_retry(requests.request, "POST", url, headers=headers, data=payload)
    results = response.json().get('organic', [])
    return results

def get_recent_news(company: str) -> str:
    url = "https://google.serper.dev/news"
    
    # Define the payload for the request
    payload = json.dumps({
        "q": company,
        "num": 20,
        "tbs": "qdr:y"
    })
    
    # Set the headers
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    
    # Make the POST request to the API
    response = _execute_with_retry(requests.post, url, headers=headers, data=payload)
    
    # Check if the response is successful
    if response.status_code == 200:
        news = response.json().get("news", [])
        
        # Prepare the string to return
        news_string = ""
        news.reverse()  # Reverse the list to get the most recent news first
        
        for item in news:
            title = item.get('title')
            snippet = item.get('snippet')
            date = item.get('date')
            link = item.get('link')
            
            news_string += f"Title: {title}\nSnippet: {snippet}\nDate: {date}\nURL: {link}\n\n"
        
        return news_string
    else:
        return f"Error fetching news: {response.status_code}"
