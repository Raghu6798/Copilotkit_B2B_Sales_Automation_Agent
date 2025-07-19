from colorama import Fore, Style
from sample_agent.tools.base.markdown_scraper_tool import scrape_website_to_markdown
from sample_agent.tools.base.search_tools import get_recent_news
from sample_agent.tools.base.gmail_tools import GmailTools
from sample_agent.tools.google_docs_tools import GoogleDocsManager
from sample_agent.tools.company_research import research_lead_on_linkedin
from sample_agent.tools.company_research import research_lead_company, generate_company_profile
from sample_agent.tools.youtube_tools import get_youtube_stats
from sample_agent.tools.rag_tool import fetch_similar_case_study
from sample_agent.prompts import *
from sample_agent.state import LeadData, CompanyData, Report, GraphInputState, GraphState
from sample_agent.structured_outputs import WebsiteData, EmailResponse
from sample_agent.utils import invoke_llm, get_report, get_current_date, save_reports_locally
from loguru import logger

# Enable or disable sending emails directly using GMAIL
# Should be confident about the quality of the email
SEND_EMAIL_DIRECTLY = False
# Enable or disable saving emails to Google Docs
# By defauly all reports are save locally in `reports` folder
SAVE_TO_GOOGLE_DOCS = False

class OutReachAutomationNodes:
    def __init__(self, loader):
        self.lead_loader = loader
        self.docs_manager = GoogleDocsManager()
        self.drive_folder_name = ""

    def get_new_leads(self, state: GraphInputState):
        logger.info("Entering get_new_leads with state: {}", state)
        print(Fore.YELLOW + "----- Fetching new leads -----\n" + Style.RESET_ALL)
        
        # Fetch new leads using the provided loader
        raw_leads = self.lead_loader.fetch_records()
        
        # Structure the leads
        leads = [
            LeadData(
                id=lead["id"],
                name=f'{lead.get("First Name", "")} {lead.get("Last Name", "")}',
                email=lead.get("Email", ""),
                phone=lead.get("Phone", ""),
                address=lead.get("Address", ""),
                company=lead.get("Company", ""),  
                profile=""
            )
            for lead in raw_leads
        ]
        
        print(Fore.YELLOW + f"----- Fetched {len(leads)} leads -----\n" + Style.RESET_ALL)
        logger.info("Fetched leads: {}", leads)
        return {"leads_data": leads, "number_leads": len(leads)}
    
    @staticmethod
    def check_for_remaining_leads(state: GraphState):
        logger.info("Checking for remaining leads. State: {}", state)
        """Checks for remaining leads and updates lead_data in the state."""
        print(Fore.YELLOW + "----- Checking for remaining leads -----\n" + Style.RESET_ALL)
        
        current_lead = None
        if state["leads_data"]:
            current_lead = state["leads_data"].pop()
        print(Fore.YELLOW + f"----- Current lead selected: {current_lead} -----\n" + Style.RESET_ALL)
        logger.info("Current lead selected: {}", current_lead)
        return {"current_lead": current_lead, "number_leads": len(state["leads_data"])}

    @staticmethod
    def check_if_there_more_leads(state: GraphState):
        logger.info("Checking if there are more leads. State: {}", state)
        # Number of leads remaining
        num_leads = state["number_leads"]
        if num_leads > 0:
            print(Fore.YELLOW + f"----- Found {num_leads} more leads -----\n" + Style.RESET_ALL)
            logger.info("Number of leads remaining: {}", num_leads)
            return "Found leads"
        else:
            print(Fore.GREEN + "----- Finished, No more leads -----\n" + Style.RESET_ALL)
            logger.info("Number of leads remaining: {}", num_leads)
            return "No more leads"

    def fetch_linkedin_profile_data(self, state: GraphState):
        logger.info("Fetching LinkedIn profile data for state: {}", state)
        print(Fore.YELLOW + "----- Searching Lead data on LinkedIn -----\n" + Style.RESET_ALL)
        lead_data = state["current_lead"]
        company_data = state.get("company_data", CompanyData())
        
        # Scrape lead linkedin profile and get company info from the same call
        (
            lead_profile, 
            company_name, 
            company_website,
            company_linkedin_url
        ) = research_lead_on_linkedin(lead_data.name, lead_data.company)
        lead_data.profile = lead_profile

        # If LinkedIn failed to get company info, try to search for company information
        if not company_name and lead_data.company:
            print(Fore.YELLOW + "----- LinkedIn failed, searching for company information -----\n" + Style.RESET_ALL)
            # Use the company name from the lead data as fallback
            company_name = lead_data.company.strip()
            
            # Search for company website
            try:
                from sample_agent.tools.company_research import google_search
                search_results = google_search(f"{company_name} official website")
                if search_results:
                    # Extract the first result that looks like a company website
                    for result in search_results:
                        link = result.get('link', '')
                        if any(domain in link.lower() for domain in ['.com', '.org', '.net', '.io']) and not any(exclude in link.lower() for exclude in ['linkedin.com', 'facebook.com', 'twitter.com']):
                            company_website = link
                            break
            except Exception as e:
                print(f"Error searching for company website: {e}")
                company_website = ""

        # Use company info from research_lead_on_linkedin directly
        company_data.name = company_name
        company_data.website = company_website
        company_data.profile = f"LinkedIn URL: {company_linkedin_url}" if company_linkedin_url else ""
            
        # Update folder name for saving reports in Drive
        self.drive_folder_name = f"{lead_data.name}_{company_data.name}"
        
        print(Fore.YELLOW + f"----- Updated lead_data: {lead_data} and company_data: {company_data} -----\n" + Style.RESET_ALL)
        logger.info("Updated lead_data: {} and company_data: {}", lead_data, company_data)
        return {
            "current_lead": lead_data,
            "company_data": company_data,
            "reports": []
        }
    
    def review_company_website(self, state: GraphState):
        logger.info("Reviewing company website for state: {}", state)
        print(Fore.YELLOW + "----- Scraping company website -----\n" + Style.RESET_ALL)
        lead_data = state.get("current_lead")
        company_data = state.get("company_data")
        
        company_website = company_data.website
        
        # If no website but we have company name, try to find it
        if not company_website and company_data.name:
            print(Fore.YELLOW + "----- No website found, searching for company website -----\n" + Style.RESET_ALL)
            try:
                from sample_agent.tools.company_research import google_search
                search_results = google_search(f"{company_data.name} official website")
                if search_results:
                    # Extract the first result that looks like a company website
                    for result in search_results:
                        link = result.get('link', '')
                        if any(domain in link.lower() for domain in ['.com', '.org', '.net', '.io']) and not any(exclude in link.lower() for exclude in ['linkedin.com', 'facebook.com', 'twitter.com']):
                            company_website = link
                            company_data.website = link
                            break
            except Exception as e:
                print(f"Error searching for company website: {e}")
        
        if company_website:
            # Scrape company website
            content = scrape_website_to_markdown(company_website)
            website_info = invoke_llm(
                system_prompt=WEBSITE_ANALYSIS_PROMPT.format(main_url=company_website), 
                user_message=content,
                model="gemini-2.5-flash",
                response_format=WebsiteData
            )

            # Extract all relevant links
            company_data.social_media_links.blog = website_info.blog_url
            company_data.social_media_links.facebook = website_info.facebook
            company_data.social_media_links.twitter = website_info.twitter
            company_data.social_media_links.youtube = website_info.youtube
            
            # Update company profile with website summary
            company_data.profile = generate_company_profile(company_data.profile, website_info.summary)
                 
        inputs = f"""
        # **Lead Profile:**

        {lead_data.profile}

        # **Company Information:**

        {company_data.profile}
        """
        
        # Generate general lead search report
        general_lead_search_report = invoke_llm(
            system_prompt=LEAD_SEARCH_REPORT_PROMPT, 
            user_message=inputs,
            model="gemini-2.5-flash"
        )
        
        lead_search_report = Report(
            title="General Lead Research Report",
            content=general_lead_search_report,
            is_markdown=True
        )
        
        print(Fore.YELLOW + f"----- Website review complete. Updated company_data: {company_data} -----\n" + Style.RESET_ALL)
        logger.info("Website review complete. Updated company_data: {}", company_data)
        return {
            "company_data": company_data,
            "reports": [lead_search_report]
        }
    
    @staticmethod
    def collect_company_information(state: GraphState):
        return {"reports": []}
    
    def analyze_blog_content(self, state: GraphState):
        logger.info("Analyzing blog content for state: {}", state)
        print(Fore.YELLOW + "----- Analyzing company main blog -----\n" + Style.RESET_ALL)  
        blog_analysis_report = ""
        
        # Check if company has a blog
        company_data = state["company_data"]
        blog_url = company_data.social_media_links.blog
        if blog_url:
            blog_content = scrape_website_to_markdown(blog_url)
            prompt = BLOG_ANALYSIS_PROMPT.format(company_name=company_data.name)
            blog_analysis_report = invoke_llm(
                system_prompt=prompt, 
                user_message=blog_content,
                model="gemini-2.5-flash"
            )
            blog_analysis_report = Report(
                title="Blog Analysis Report",
                content=blog_analysis_report,
                is_markdown=True
            )
        print(Fore.YELLOW + f"----- Blog analysis report: {blog_analysis_report} -----\n" + Style.RESET_ALL)
        logger.info("Blog analysis report: {}", blog_analysis_report)
        return {"reports": [blog_analysis_report]}
    
    def analyze_social_media_content(self, state: GraphState):
        logger.info("Analyzing social media content for state: {}", state)
        print(Fore.YELLOW + "----- Analyzing company social media accounts -----\n" + Style.RESET_ALL)
        
        # Load states
        company_data = state["company_data"]
        
        # Get social media urls
        facebook_url = company_data.social_media_links.facebook
        twitter_url = company_data.social_media_links.twitter
        youtube_url = company_data.social_media_links.youtube
        
        youtube_analysis_report = None  # <-- Add this line
        
        # Check If company has Youtube channel
        if youtube_url:
            youtube_data = get_youtube_stats(youtube_url)
            prompt = YOUTUBE_ANALYSIS_PROMPT.format(company_name=company_data.name)
            youtube_insight = invoke_llm(
                system_prompt=prompt, 
                user_message=youtube_data,
                model="gemini-2.5-flash"
            )
            youtube_analysis_report = Report(
                title="Youtube Analysis Report",
                content=youtube_insight,
                is_markdown=True
            )
            
        # Check If company has Facebook account
        if facebook_url:
            # TODO Add Facebook analysis part
            pass
        
        # Check If company has Twitter account
        if twitter_url:
            # TODO Add Twitter analysis part
            pass
        
        print(Fore.YELLOW + f"----- YouTube analysis report: {youtube_analysis_report} -----\n" + Style.RESET_ALL)
        logger.info("YouTube analysis report: {}", youtube_analysis_report)
        return {
            "company_data": company_data,
            "reports": [youtube_analysis_report] if youtube_analysis_report else []
        }
    
    def analyze_recent_news(self, state: GraphState):
        logger.info("Analyzing recent news for state: {}", state)
        print(Fore.YELLOW + "----- Analyzing recent news about company -----\n" + Style.RESET_ALL)
        
        # Load states
        company_data = state["company_data"]
        
        # Use company name for news search, fallback to lead's company if company_data.name is empty
        company_name = company_data.name if company_data.name else state.get("current_lead", {}).get("company", "")
        
        # Fetch recent news using serper API
        recent_news = get_recent_news(company=company_name) if company_name else ""
        number_months = 6
        current_date = get_current_date()
        news_analysis_prompt = NEWS_ANALYSIS_PROMPT.format(
            company_name=company_name, 
            number_months=number_months, 
            date=current_date
        )
        
        # Only call LLM if recent_news is not empty and not an error
        if not recent_news or recent_news.strip() == "" or recent_news.startswith("Error fetching news"):
            if company_name:
                news_insight = f"No recent news found for {company_name} in the last 6 months."
            else:
                news_insight = "No company name available for news search."
        else:
            news_insight = invoke_llm(
                system_prompt=news_analysis_prompt, 
                user_message=recent_news,
                model="gemini-2.5-flash"
            )

        news_analysis_report = Report(
            title="News Analysis Report",
            content=news_insight,
            is_markdown=True
        )
        print(Fore.YELLOW + f"----- News analysis report: {news_analysis_report} -----\n" + Style.RESET_ALL)
        logger.info("News analysis report: {}", news_analysis_report)
        return {"reports": [news_analysis_report]}
    
    def generate_digital_presence_report(self, state: GraphState):
        logger.info("Generating digital presence report for state: {}", state)
        print(Fore.YELLOW + "----- Generate Digital presence analysis report -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        blog_analysis_report = get_report(reports, "Blog Analysis Report")
        facebook_analysis_report = get_report(reports, "Facebook Analysis Report")
        twitter_analysis_report = get_report(reports, "Twitter Analysis Report")
        youtube_analysis_report = get_report(reports, "Youtube Analysis Report")
        news_analysis_report = get_report(reports, "News Analysis Report")
        
        inputs = f"""
        # **Digital Presence Data:**
        ## **Blog Information:**

        {blog_analysis_report}
        
        ## **Facebook Information:**

        {facebook_analysis_report}
        
        ## **Twitter Information:**

        {twitter_analysis_report}

        ## **Youtube Information:**

        {youtube_analysis_report}

        # **Recent News:**

        {news_analysis_report}
        """
        
        prompt = DIGITAL_PRESENCE_REPORT_PROMPT.format(
            company_name=state["company_data"].name, date=get_current_date()
        )
        digital_presence_report = invoke_llm(
            system_prompt=prompt, 
            user_message=inputs,
            model="gemini-2.5-flash"
        ) 
        
        digital_presence_report = Report(
            title="Digital Presence Report",
            content=digital_presence_report,
            is_markdown=True
        )
        print(Fore.YELLOW + f"----- Digital presence report: {digital_presence_report} -----\n" + Style.RESET_ALL)
        logger.info("Digital presence report: {}", digital_presence_report)
        return {"reports": [digital_presence_report]}
    
    def generate_full_lead_research_report(self, state: GraphState):
        logger.info("Generating full lead research report for state: {}", state)
        print(Fore.YELLOW + "----- Generate global lead analysis report -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")
        digital_presence_report = get_report(reports, "Digital Presence Report")
        
        inputs = f"""
        # **Lead & company Information:**

        {general_lead_search_report}
        
        ---

        # **Digital Presence Information:**

        {digital_presence_report}
        """
        
        prompt = GLOBAL_LEAD_RESEARCH_REPORT_PROMPT.format(
            company_name=state["company_data"].name, date=get_current_date()
        )
        full_report = invoke_llm(
            system_prompt=prompt, 
            user_message=inputs,
            model="gemini-2.0-flash"
        )
        
        global_research_report = Report(
            title="Global Lead Analysis Report",
            content=full_report,
            is_markdown=True
        )
        print(Fore.YELLOW + f"----- Global research report: {global_research_report} -----\n" + Style.RESET_ALL)
        logger.info("Global research report: {}", global_research_report)
        return {"reports": [global_research_report]}
    
    @staticmethod
    def score_lead(state: GraphState):
        logger.info("Scoring lead. State: {}", state)
        """
        Score the lead based on the company profile and open positions.

        @param state: The current state of the application.
        @return: Updated state with the lead score.
        """
        print(Fore.YELLOW + "----- Scoring lead -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        global_research_report = get_report(reports, "Global Lead Analysis Report")
        
        # Scoring lead
        lead_score = invoke_llm(
            system_prompt=SCORE_LEAD_PROMPT,
            user_message=global_research_report,
            model="gemini-2.0-flash"
        )
        print(Fore.YELLOW + f"----- Lead score: {lead_score} -----\n" + Style.RESET_ALL)
        logger.info("Lead score: {}", lead_score)
        return {"lead_score": lead_score.strip()}

    @staticmethod
    def is_lead_qualified(state: GraphState):
        """
        Check if the lead is qualified based on the lead score.

        @param state: The current state of the application.
        @return: Updated state with the qualification status.
        """
        print(Fore.YELLOW + "----- Checking if lead is qualified -----\n" + Style.RESET_ALL)
        return {"reports": []}

    @staticmethod
    def check_if_qualified(state: GraphState):
        """
        Check if the lead is qualified based on the lead score.

        @param state: The current state of the application.
        @return: Updated state with the qualification status.
        """
        # Checking if the lead score is 7 or higher
        print(f"Score: {state['lead_score']}")
        is_qualified = float(state["lead_score"]) >= 7
        if is_qualified:
            print(Fore.GREEN + "Lead is qualified\n" + Style.RESET_ALL)
            return "qualified"
        else:
            print(Fore.RED + "Lead is not qualified\n" + Style.RESET_ALL)
            return "not qualified"
    
    @staticmethod
    def create_outreach_materials(state: GraphState):
        return {"reports": []}
    
    def generate_custom_outreach_report(self, state: GraphState):
        logger.info("Generating custom outreach report for state: {}", state)
        print(Fore.YELLOW + "----- Crafting Custom outreach report based on gathered information -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")
        global_research_report = get_report(reports, "Global Lead Analysis Report")
        
        # TODO Create better description to fetch accurate similar case study using RAG
        # get relevant case study
        case_study_report = fetch_similar_case_study(general_lead_search_report)
        
        inputs = f"""
        **Research Report:**

        {global_research_report}

        ---

        **Case Study:**

        {case_study_report}
        """
        
        # Generate report
        custom_outreach_report = invoke_llm(
            system_prompt=GENERATE_OUTREACH_REPORT_PROMPT,
            user_message=inputs,
            model="gemini-2.0-flash"
        )
        
        # TODO Find better way to include correct links into the final report
        # Proof read generated report
        inputs = f"""
        {custom_outreach_report}

        ---

        **Correct Links:**

        ** Our website link**: https://elevateAI.com
        ** Case study link**: https://elevateAI.com/case-studies/A
        """
        
        # Call our editor/proof-reader agent
        revised_outreach_report = invoke_llm(
            system_prompt=PROOF_READER_PROMPT,
            user_message=inputs,
            model="gemini-2.5-flash"
        )
        
        # Store report into google docs and get shareable link
        new_doc = self.docs_manager.add_document(
            content=revised_outreach_report,
            doc_title="Outreach Report",
            folder_name=self.drive_folder_name,
            make_shareable=True,
            folder_shareable=True, # Set to false if only personal or true if with a team
            markdown=True
        )  
        
        print(Fore.YELLOW + f"----- Custom outreach report link: {new_doc['shareable_url']}, Reports folder link: {new_doc['folder_url']} -----\n" + Style.RESET_ALL)
        logger.info("Custom outreach report link: {}, Reports folder link: {}", new_doc["shareable_url"], new_doc["folder_url"])
        return {
            "custom_outreach_report_link": new_doc["shareable_url"],
            "reports_folder_link": new_doc["folder_url"]
        }

    def generate_personalized_email(self, state: GraphState):
        logger.info("Generating personalized email for state: {}", state)
        """
        Generate a personalized email for the lead.

        @param state: The current state of the application.
        @return: Updated state with the generated email.
        """
        print(Fore.YELLOW + "----- Generating personalized email -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        general_lead_search_report = get_report(reports, "General Lead Research Report")
        
        lead_data = f"""
        # **Lead & company Information:**

        {general_lead_search_report}

        # Outreach report Link:

        {state["custom_outreach_report_link"]}
        """
        output = invoke_llm(
            system_prompt=PERSONALIZE_EMAIL_PROMPT,
            user_message=lead_data,
            model="gemini-2.5-flash",
            response_format=EmailResponse
        )
        
        # Get relevant fields
        subject = output.subject
        personalized_email = output.email
        
        # Get lead email
        email = state["current_lead"].email
        
        # Create draft email
        gmail = GmailTools()
        gmail.create_draft_email(
            recipient=email,
            subject=subject,
            email_content=personalized_email
        )
        
        # Send email directly
        if SEND_EMAIL_DIRECTLY:
            gmail.send_email(
                recipient=email,
                subject=subject,
                email_content=personalized_email
            )
        
        # Save email with reports for reference
        personalized_email_doc = Report(
            title="Personalized Email",
            content=personalized_email,
            is_markdown=False
        )
        print(Fore.YELLOW + f"----- Personalized email generated for: {email} -----\n" + Style.RESET_ALL)
        logger.info("Personalized email generated for: {}", email)
        return {"reports": [personalized_email_doc]}

    def generate_interview_script(self, state: GraphState):
        logger.info("Generating interview script for state: {}", state)
        print(Fore.YELLOW + "----- Generating interview script -----\n" + Style.RESET_ALL)
        
        # Load reports
        reports = state["reports"]
        global_research_report = get_report(reports, "Global Lead Analysis Report")
        
        # Generating SPIN questions
        spin_questions = invoke_llm(
            system_prompt=GENERATE_SPIN_QUESTIONS_PROMPT,
            user_message=global_research_report,
            model="gemini-2.5-flash"
        )
        
        inputs = f"""
        # **Lead & company Information:**

        {global_research_report}

        # **SPIN questions:**

        {spin_questions}
        """
        
        # Generating interview script
        interview_script = invoke_llm(
            system_prompt=WRITE_INTERVIEW_SCRIPT_PROMPT,
            user_message=inputs,
            model="gemini-2.5-flash"
        )
        
        interview_script_doc = Report(
            title="Interview Script",
            content=interview_script,
            is_markdown=True
        )
        print(Fore.YELLOW + f"----- Interview script generated: {interview_script_doc} -----\n" + Style.RESET_ALL)
        logger.info("Interview script generated: {}", interview_script_doc)
        return {"reports": [interview_script_doc]}
    
    @staticmethod
    def await_reports_creation(state: GraphState):
        return {"reports": []}
    
    def save_reports_to_google_docs(self, state: GraphState):
        logger.info("Saving reports to Google Docs. State: {}", state)
        print(Fore.YELLOW + "----- Save Reports to Google Docs -----\n" + Style.RESET_ALL)
        
        # Load all reports
        reports = state["reports"]
        
        # Ensure reports are saved locally
        save_reports_locally(reports)
        
        # Save all reports to Google docs
        if SAVE_TO_GOOGLE_DOCS:
            for report in reports:
                self.docs_manager.add_document(
                    content=report.content,
                    doc_title=report.title,
                    folder_name=self.drive_folder_name,
                    markdown=report.is_markdown
                )
        print(Fore.YELLOW + "----- Reports saved locally and/or to Google Docs. -----\n" + Style.RESET_ALL)
        logger.info("Reports saved locally and/or to Google Docs.")
        return state

    def update_CRM(self, state: GraphState):
        logger.info("Updating CRM for lead: {} with state: {}", state["current_lead"].id, state)
        print(Fore.YELLOW + "----- Updating CRM records -----\n" + Style.RESET_ALL)
        
        # save new record data, ensure correct fields are used
        new_data = {
        "Status": "ATTEMPTED_TO_CONTACT",
        "Score": state.get("lead_score", ""), 
        "Outreach Report": state.get("custom_outreach_report_link", ""),
        "Last Contacted": get_current_date()
    }
        self.lead_loader.update_record(state["current_lead"].id, new_data)
        
        # reset reports list
        state["reports"] = []
        print(Fore.YELLOW + f"----- CRM updated for lead: {state['current_lead'].id} -----\n" + Style.RESET_ALL)
        logger.info("CRM updated for lead: {}", state["current_lead"].id)
        return {}
