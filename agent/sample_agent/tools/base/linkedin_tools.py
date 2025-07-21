import os
from dotenv import load_dotenv
import requests
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log
from sample_agent.utils import invoke_llm

load_dotenv()

# RapidAPI configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_PROFILE_URL = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-profile-public-data"
BASE_COMPANY_URL = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-company-by-linkedinurl"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
}


def extract_linkedin_url_base(search_results):
    """
    Extracts the LinkedIn URL from the search results.
    """
    for result in search_results:
        if 'linkedin.com/in' in result['link']:
            return result['link']
    return ""


def extract_linkedin_url(search_results):
    EXTRACT_LINKEDIN_URL_PROMPT = """
    **Role:**  
    You are an expert in extracting LinkedIn URLs from Google search results, specializing in finding the correct personal LinkedIn URL.

    **Objective:**  
    From the provided search results, find the LinkedIn URL of a specific person working at a specific company.

    **Instructions:**  
    1. Output **only** the correct LinkedIn URL if found, nothing else.  
    2. If no valid URL exists, output **only** an empty string.  
    3. Only consider URLs with `"/in"`. Ignore those with `"/posts"` or `"/company"`.  
    """
    result = invoke_llm(
        system_prompt=EXTRACT_LINKEDIN_URL_PROMPT, 
        user_message=str(search_results),
        model="gemini-2.0-flash"
    )
    return result


def _is_retryable_httpx_error(exc):
    # Retry on HTTP 5xx errors
    return isinstance(exc, httpx.HTTPStatusError) and 500 <= exc.response.status_code < 600

def _is_retryable_requests_error(exc):
    # Retry on HTTP 5xx errors
    return isinstance(exc, requests.HTTPError) and 500 <= exc.response.status_code < 600

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=(retry_if_exception_type(httpx.HTTPStatusError) | retry_if_exception_type(requests.HTTPError)),
    before=before_log(logger, "INFO"),
    after=after_log(logger, "ERROR")
)
def _retryable_httpx_get(*args, **kwargs):
    response = httpx.get(*args, **kwargs)
    response.raise_for_status()
    return response

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type(requests.HTTPError),
    before=before_log(logger, "INFO"),
    after=after_log(logger, "ERROR")
)
def _retryable_requests_get(*args, **kwargs):
    response = requests.get(*args, **kwargs)
    response.raise_for_status()
    return response


def scrape_linkedin(linkedin_url: str, is_company: bool = False):
    """
    Scrapes LinkedIn profile or company data using the RapidAPI LinkedIn API.

    Args:
        linkedin_url (str): The LinkedIn URL to scrape.
        is_company (bool): If True, scrapes a company profile. If False, scrapes a personal profile.

    Returns:
        dict or None: The scraped LinkedIn profile/company data, or None if scraping failed.
    """
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY not found in environment. Please check your .env file.")
        return None

    linkedin_url = linkedin_url.strip()
    logger.info(f"Scraping LinkedIn URL: {linkedin_url} (is_company={is_company})")

    if is_company:
        url = BASE_COMPANY_URL
        params = {"linkedin_url": linkedin_url}
        try:
            response = _retryable_requests_get(url, headers=HEADERS, params=params, timeout=30)
            data = response.json()
            logger.info(f"Company scrape successful for {linkedin_url}")
            return data
        except requests.HTTPError as exc:
            logger.error(f"HTTP error occurred (company): {exc.response.status_code} - {exc.response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while scraping LinkedIn company: {e}")
        return None
    else:
        params = {
            "linkedin_url": linkedin_url,
            "include_skills": "false",
            "include_certifications": "false",
            "include_publications": "false",
            "include_honors": "false",
            "include_volunteers": "false",
            "include_projects": "false",
            "include_patents": "false",
            "include_courses": "false",
            "include_organizations": "false",
            "include_profile_status": "false",
            "include_company_public_url": "false"
        }
        try:
            response = _retryable_httpx_get(BASE_PROFILE_URL, headers=HEADERS, params=params, timeout=30.0)
            data = response.json()
            logger.info(f"Profile scrape successful for {linkedin_url}")
            return data
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP error occurred (profile): {exc.response.status_code} - {exc.response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while scraping LinkedIn profile: {e}")
        return None

if __name__ == "__main__":
    # Example LinkedIn profile URL (replace with any valid profile for testing)
    linkedin_url = "https://in.linkedin.com/in/prajjwalyd"
    print(f"Testing LinkedIn scrape for: {linkedin_url}")
    result = scrape_linkedin(linkedin_url, is_company=False)
    print("Result:")
    print(result)
    
