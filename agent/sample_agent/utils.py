import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log

# Load environment variables
load_dotenv()

# Check for API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
if not GOOGLE_API_KEY.startswith("AI"):
    logger.warning("GOOGLE_API_KEY should start with 'AI' for Gemini models. Current key may be invalid.")

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

BASE_DIR = os.path.dirname(__file__)
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds
    
def get_report(reports, report_name: str):
    """
    Retrieves the content of a report by its title.
    """
    for report in reports:
        if report.title == report_name:
            return report.content
    return ""

def save_reports_locally(reports):
    # Define the local folder path
    reports_folder = "reports"
    
    # Create folder if it does not exist
    if not os.path.exists(reports_folder):
        os.makedirs(reports_folder)
    
    # Save each report as a file in the folder
    for report in reports:
        file_path = os.path.join(reports_folder, f"{report.title}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(report.content)

def get_llm_by_provider(llm_provider, model):
    try:
        # Else find provider
        if llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=model, temperature=0.1)
        elif llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model=model, temperature=0.1)  # Use the correct model name
        elif llm_provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found. Please check your .env file.")
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=0.1,
                google_api_key=GOOGLE_API_KEY  # Explicitly pass the API key
            )
        elif llm_provider == "sambanova":
            from langchain_sambanova import ChatSambaNovaCloud
            llm = ChatSambaNovaCloud(
                model="Llama-3.3-Swallow-70B-Instruct-v0.4",
                sambanova_api_key=os.getenv("SAMBANOVA_API_KEY")
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        raise

def _invoke_llm_with_retry(llm, messages):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type(Exception),
        before=before_log(logger, "INFO"),
        after=after_log(logger, "ERROR")
    )
    def _inner():
        return llm.invoke(messages)
    return _inner()


def invoke_llm(
    system_prompt,
    user_message,
    model="gemini-2.5-flash",  # Specify the model name according to the provider
    llm_provider="google",  # By default use Google as provider
    response_format=None
):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]  
    
    # Get base llm
    llm = get_llm_by_provider(llm_provider, model)

    if response_format:
        llm = llm.with_structured_output(response_format)
    else: # Esle use parse string output
        llm = llm | StrOutputParser()
    
    # Invoke LLM with retry
    try:
        output = _invoke_llm_with_retry(llm, messages)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return "LLM call failed due to API error."
    return output


