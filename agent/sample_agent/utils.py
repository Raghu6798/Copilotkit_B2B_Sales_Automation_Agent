import os
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

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
    # Else find provider
    if llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model, temperature=0.1)
    elif llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model, temperature=0.1)  # Use the correct model name
    elif llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=model, temperature=0.1)  # Correct model name
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    return llm

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
    
    # Invoke LLM
    output = llm.invoke(messages)
    
    return output


if __name__=="__main__":
    get_google_credentials()

