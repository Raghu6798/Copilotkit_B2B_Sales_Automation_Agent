"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""
import os 
from dotenv import load_dotenv
from typing_extensions import Literal,List,Annotated
from operator import add
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from copilotkit import CopilotKitState



from sample_agent.state import SocialMediaLinks,Report,LeadData, CompanyData, Report, GraphInputState
from sample_agent.nodes import OutReachAutomationNodes
from sample_agent.tools.leads_loader.airtable import AirtableLeadLoader
from sample_agent.tools.lead_research import research_lead_on_linkedin

load_dotenv()

class AgentState(CopilotKitState):
    leads_ids: List[str]
    leads_data: List[dict]
    current_lead: LeadData
    lead_score: str = ""
    company_data: CompanyData
    reports: Annotated[list[Report], add]
    reports_folder_link: str
    custom_outreach_report_link: str
    personalized_email: str
    interview_script: str
    number_leads: int

    
workflow = StateGraph(AgentState)

# Initialize the nodes with the provided lead loader
lead_loader = AirtableLeadLoader(
        access_token=os.getenv("AIRTABLE_ACCESS_TOKEN"),
        base_id=os.getenv("AIRTABLE_BASE_ID"),
        table_name=os.getenv("AIRTABLE_TABLE_NAME"),
)
    
nodes = OutReachAutomationNodes(lead_loader)

# **Step 1: Adding nodes to the graph**
# Fetch new leads from the CRM
workflow.add_node("get_new_leads", nodes.get_new_leads)
workflow.add_node("check_for_remaining_leads", nodes.check_for_remaining_leads)

# Research phase: gather data and insights about the lead
workflow.add_node("fetch_linkedin_profile_data", nodes.fetch_linkedin_profile_data)
workflow.add_node("review_company_website", nodes.review_company_website)
workflow.add_node("collect_company_information", nodes.collect_company_information)
workflow.add_node("analyze_blog_content", nodes.analyze_blog_content)
workflow.add_node("analyze_social_media_content", nodes.analyze_social_media_content)
workflow.add_node("analyze_recent_news", nodes.analyze_recent_news)
workflow.add_node("generate_full_lead_research_report", nodes.generate_full_lead_research_report)
workflow.add_node("generate_digital_presence_report", nodes.generate_digital_presence_report)
workflow.add_node("score_lead", nodes.score_lead)

# Outreach preparation phase
workflow.add_node("create_outreach_materials", nodes.create_outreach_materials)
workflow.add_node("generate_custom_outreach_report", nodes.generate_custom_outreach_report)
workflow.add_node("generate_personalized_email", nodes.generate_personalized_email)
workflow.add_node("generate_interview_script", nodes.generate_interview_script)

# Reporting and finalization
workflow.add_node("save_reports_to_google_docs", nodes.save_reports_to_google_docs)
workflow.add_node("await_reports_creation", nodes.await_reports_creation)
workflow.add_node("update_CRM", nodes.update_CRM)

# **Step 2: Setting up edges between nodes**

# Entry point of the graph
workflow.set_entry_point("get_new_leads")

# Transition from fetching leads to checking if there are leads to process
workflow.add_edge("get_new_leads", "check_for_remaining_leads")

# Conditional logic for lead availability
workflow.add_conditional_edges(
    "check_for_remaining_leads",
    nodes.check_if_there_more_leads,
    {
        "Found leads": "fetch_linkedin_profile_data",  # Proceed if leads are found
        "No more leads": END  # Terminate if no leads remain
    }
)

# Research phase transitions
workflow.add_edge("fetch_linkedin_profile_data", "review_company_website")
workflow.add_edge("review_company_website", "collect_company_information")

# Collect company information and branch into various analyses
workflow.add_edge("collect_company_information", "analyze_blog_content")
workflow.add_edge("collect_company_information", "analyze_social_media_content")
workflow.add_edge("collect_company_information", "analyze_recent_news")

# Analysis results converge into generating reports
workflow.add_edge("analyze_blog_content", "generate_digital_presence_report")
workflow.add_edge("analyze_social_media_content", "generate_digital_presence_report")
workflow.add_edge("analyze_recent_news", "generate_digital_presence_report")
workflow.add_edge("generate_digital_presence_report", "generate_full_lead_research_report")

# Scoring phase with conditional qualification check
workflow.add_edge("generate_full_lead_research_report", "score_lead")
workflow.add_conditional_edges(
    "score_lead",
    nodes.check_if_qualified,
    {
        "qualified": "generate_custom_outreach_report",  # Proceed if lead is qualified
        "not qualified": "save_reports_to_google_docs"  # Save reports and exit if lead is unqualified 
    }
)

# Outreach material creation
workflow.add_edge("generate_custom_outreach_report", "create_outreach_materials")
workflow.add_edge("create_outreach_materials", "generate_personalized_email")
workflow.add_edge("create_outreach_materials", "generate_interview_script")

# Await completion and finalize reports
workflow.add_edge("generate_personalized_email", "await_reports_creation")
workflow.add_edge("generate_interview_script", "await_reports_creation")
workflow.add_edge("await_reports_creation", "save_reports_to_google_docs")

# Save reports and update the CRM
workflow.add_edge("save_reports_to_google_docs", "update_CRM")

# Loop back to check for remaining leads
workflow.add_edge("update_CRM", "check_for_remaining_leads")


graph = workflow.compile()
