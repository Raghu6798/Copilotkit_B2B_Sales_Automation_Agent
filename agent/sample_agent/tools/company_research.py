import os
from dotenv import load_dotenv
from sample_agent.utils import invoke_llm
import json
import requests
from sample_agent.tools.base.linkedin_tools import scrape_linkedin
from loguru import logger

load_dotenv()

CREATE_COMPANY_PROFILE = """
### Role  
You are an Expert Company profile generator with a particular expertise for generating a company profile from their scraped LinkedIn & website pages. 

### Objective  
Your goal is to look through the scraped LinkedIn company profile & website and create a 300-word company profile summarizing its operations, value proposition, target audience, products/services, location, company size, year founded and any other relevant information that might be useful to use when meeting the inbound lead that works for this company .

### Context  
This profile provides context for engaging with a prospect who works at the company.  

### Instructions  
- If no data is available from LinkedIn *and* the website, output only: *"No company info available."*  
- Use the available data from one or both sources; do not assume or invent information.  
- Always include:  
  - Company description  
  - Value proposition  
  - Target audience  
  - Products/services  
  - Location, size, and year founded  
- Keep the tone neutral and factual; avoid hype or subjective language.  
- Limit the profile to 300 words.  
"""

def research_lead_company(linkedin_url):
    logger.info("Researching company LinkedIn profile for URL: {}", linkedin_url)
    # Scrape company LinkedIn profile
    company_page_content = scrape_linkedin(linkedin_url, True)
    print(company_page_content)
    if not company_page_content or "data" not in company_page_content:
        logger.warning("LinkedIn profile not found for URL: {}", linkedin_url)
        return "LinkedIn profile not found"
    
    # Structure collected information about company
    company_profile = company_page_content["data"]
    logger.info("Successfully scraped LinkedIn company profile for URL: {}", linkedin_url)
    return {
        "company_name": company_profile.get('company_name', ''),
        "description": company_profile.get('description', ''),
        "year_founded": company_profile.get('year_founded', ''),
        "industries": company_profile.get('industries', []),
        "specialties": company_profile.get('specialties', ''),
        "employee_count": company_profile.get('employee_count', ''),
        "social_metrics": {
            "follower_count": company_profile.get('follower_count', 0)
        },
        "locations": company_profile.get('locations', [])
    }

def generate_company_profile(company_linkedin_info, scraped_website):
    logger.info("Generating company profile for LinkedIn info and website: {}", {"linkedin_info": company_linkedin_info, "website": scraped_website})
    # Get company profile summary
    inputs = (
        f"# Scraped Website:\n {scraped_website}\n\n"
        f"# Company LinkedIn Information:\n{company_linkedin_info}"
    )
    profile_summary = invoke_llm(
        system_prompt=CREATE_COMPANY_PROFILE, 
        user_message=inputs,
        model="gemini-2.5-flash"
    )
    logger.info("Generated company profile summary.")
    return profile_summary


SUMMARIZE_LINKEDIN_PROFILE = """
# Role  
You are an Expert Lead profile creator with a particular expertise for generating a lead profile from a from a scraped linkedin.  

# Objective  
Generate a 300-word summary of the lead's key information, focusing on their job title, expertise, and current focus, without assumptions or exaggeration. 
Your goal is to look at the provided data about the lead and generate a 300-word lead profile that clearly summarizes the lead's key information, focusing on their job title, expertise, and current focus, without assumptions or exaggeration.  

# Context  
The lead profile you are generating help sales teams understand inbound leads for meetings or calls.

# Instructions  
- Use only the provided data; no assumptions.  
- Highlight the lead's job title, expertise, and relevant context for sales interactions.  
- Keep the profile neutral and factual; avoid words like "impressive" or "seasoned."  
- Limit the profile to 300 words.   
"""
def google_search(query):
    """
    Performs a Google search using the provided query.
    """
    logger.info("Performing Google search for query: {}", query)
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': os.getenv('SERPER_API_KEY'),
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('organic', [])
    logger.info("Google search results for query {}: {}", query, results)
    return results

def get_recent_news(company: str) -> str:
    logger.info("Fetching recent news for company: {}", company)
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
    response = requests.post(url, headers=headers, data=payload)
    
    # Check if the response is successful
    if response.status_code == 200:
        news = response.json().get("news", [])
        logger.info("Fetched news items: {}", news)
        
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
        logger.error("Error fetching news: {}", response.status_code)
        return f"Error fetching news: {response.status_code}"

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
def research_lead_on_linkedin(lead_name, lead_company):
    """
    Searches for the lead's LinkedIn profile based on the lead name and company name.
    
    @param lead_name: The name of the lead to search for.
    @return: A dictionary containing the lead profile data or an error message if not found.
    """
    # Remove company_name extraction
    # company_name = extract_company_name(lead_email)
    # Only use the lead's name in the search query
    query = f"LinkedIn {lead_name} {lead_company}"
    search_results = google_search(query)
    print(search_results)
    lead_linkedin_url = extract_linkedin_url(search_results)
    if not lead_linkedin_url:
        return "Lead LinkedIn URL not found.", "", "", ""

    # Scrape lead LinkedIn profile
    linkedin_data = scrape_linkedin(lead_linkedin_url)
    if "data" not in linkedin_data:
        return "LinkedIn profile not found", "", "", ""
    
    # Summarize collected information about lead
    profile_data = linkedin_data["data"]
    lead_profile_content = {
        "about": profile_data.get('about', ''),
        "full_name": profile_data.get('full_name', ''),
        "location": profile_data.get('location', ''),
        "city": profile_data.get('city', ''),
        "country": profile_data.get('country', ''),
        "skills": profile_data.get('skills', []),
        "current_company": {
            "name": profile_data.get('company', ''),
            "industry": profile_data.get('company_industry', ''),
            "join_month": profile_data.get('current_company_join_month', ''),
            "join_year": profile_data.get('current_company_join_year', '')
        },
        "educations": [
            {
                "school": edu.get('school', ''),
                "field_of_study": edu.get('field_of_study', ''),
                "degree": edu.get('degree', ''),
                "date_range": edu.get('date_range', ''),
                "activities_and_societies": edu.get('activities_and_societies', '')
            } for edu in profile_data.get('educations', [])
        ],
        "experiences": [
            {
                "company": exp.get('company', ''),
                "title": exp.get('title', ''),
                "date_range": exp.get('date_range', ''),
                "is_current": exp.get('is_current', False),
                "location": exp.get('location', ''),
                "description": exp.get('description', '')
            } for exp in profile_data.get('experiences', [])
        ],
        "certifications": [
            {
                "name": cert.get('name', ''),
                "issuer": cert.get('issuer', ''),
                "date": cert.get('date', '')
            } for cert in profile_data.get('certifications', [])
        ],
        "organizations": [
            {
                "name": org.get('name', ''),
                "role": org.get('role', ''),
                "date_range": org.get('date_range', '')
            } for org in profile_data.get('organizations', [])
        ],
        "volunteer_experience": [
            {
                "organization": vol.get('organization', ''),
                "role": vol.get('role', ''),
                "date_range": vol.get('date_range', ''),
                "description": vol.get('description', '')
            } for vol in profile_data.get('volunteers', [])
        ],
        "awards": [
            {
                "name": award.get('name', ''),
                "issuer": award.get('issuer', ''),
                "date": award.get('date', ''),
                "description": award.get('description', '')
            } for award in profile_data.get('honors_and_awards', [])
        ]
    }
    
    # Extract the exact company name and LinkedIn & website url for later research
    company_name = profile_data.get('company', '')
    company_website = profile_data.get('company_website', '')
    company_linkedin_url = profile_data.get('company_linkedin_url', '')
    
    # Get Lead Linkedin profile summary
    inputs = (
        f"# Lead Name: {lead_name}\n\n"
        f"# LinkedIn Scraped Information:\n{lead_profile_content}"
    )
    profile_summary = invoke_llm(
        system_prompt=SUMMARIZE_LINKEDIN_PROFILE, 
        user_message=inputs,
        model="gemini-2.0-flash"
    )
    
    return (
        profile_summary, 
        company_name, 
        company_website,
        company_linkedin_url
    )