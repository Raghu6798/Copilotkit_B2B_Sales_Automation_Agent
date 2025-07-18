# B2B Sales Automation Agent

A full-stack AI-powered B2B sales research and outreach automation agent, combining a Next.js frontend with a LangGraph + CopilotKit backend.

---

## Features

- Real-time, generative UI for B2B sales workflows
- Structured lead research, scoring, and outreach report generation
- Live agent state dashboard (leads, reports, scores, etc.)
- Chat interface with suggestions and streaming responses
- Easily extensible with new tools, prompts, and workflows

---

## Quick Start

### 1. Clone the repository

```sh
git clone https://github.com/Raghu6798/Copilotkit_B2B_Sales_Automation_Agent.git
cd Copilotkit_B2B_Sales_Automation_Agent
```

---

### 2. Setup the Backend (LangGraph Agent)

#### a. Create and activate a Python virtual environment

```sh
cd agent
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### b. Install dependencies

```sh
uv pip install -r requirements.txt
```

#### c. Configure environment variables

Create a `.env` file in the project root directory with the following configuration:

```env
# CopilotKit Configuration
NEXT_PUBLIC_COPILOTKIT_AGENT_NAME=sample_agent
LANGGRAPH_DEPLOYMENT_URL=http://localhost:8123
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit
NEXT_PUBLIC_COPILOT_API_KEY=your-copilot-api-key

# LangSmith Configuration (for tracing and monitoring)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT="pr-virtual-flick-55"

# AI Model API Keys
GOOGLE_API_KEY=your-google-gemini-api-key

# Search and Data Sources
SERPER_API_KEY=your-serper-api-key
RAPIDAPI_KEY=your-rapidapi-key-for-linkedin-scraper

# Database and CRM Integration
AIRTABLE_ACCESS_TOKEN=your-airtable-access-token
AIRTABLE_BASE_ID=your-airtable-base-id
AIRTABLE_TABLE_NAME=your-airtable-table-name

HUBSPOT_API_KEY=your-hubspot-private-app-token
YOUTUBE_API_KEY=your-youtube-api-key

# Google Sheets Integration
SHEET_ID=your-google-sheet-id
```

#### d. Start the backend server

```sh
cd sample_agent
langgraph dev --port 8123
```

The backend will be available at `http://localhost:8123/copilotkit`.

---

### 3. Setup the Frontend (Next.js UI)

#### a. Install Node.js dependencies

```sh
cd ../../app
npm install
# or
yarn install
# or
pnpm install
```

#### b. Start the Next.js development server

```sh
npm run dev
# or
yarn dev
# or
pnpm dev
```

Visit [http://localhost:3000/copilotkit](http://localhost:3000/copilotkit) to use the agent UI.

---

## Project Structure

```
company_research_agui/
  agent/           # Python backend (LangGraph, CopilotKit, FastAPI)
    sample_agent/  # Main agent logic, tools, and demo server
  app/             # Next.js frontend (dashboard, chat UI)
  .env            # Environment configuration file
```

---

## Environment Variables Reference

### Required API Keys

| Service | Environment Variable | Description |
|---------|---------------------|-------------|
| **Google Gemini** | `GOOGLE_API_KEY` | API key for Google's Gemini AI model |
| **Serper** | `SERPER_API_KEY` | API key for Serper search functionality |
| **RapidAPI** | `RAPIDAPI_KEY` | API key for LinkedIn scraper via RapidAPI |
| **Airtable** | `AIRTABLE_ACCESS_TOKEN` | Access token for Airtable integration |
| **HubSpot** | `HUBSPOT_API_KEY` | Private app token for HubSpot CRM |
| **YouTube** | `YOUTUBE_API_KEY` | API key for YouTube data access |
| **LangSmith** | `LANGSMITH_API_KEY` | API key for LangSmith tracing (optional) |
| **CopilotKit** | `NEXT_PUBLIC_COPILOT_API_KEY` | API key for CopilotKit services |

### Configuration Details

- **LangGraph Deployment:** The agent runs on port 8123 (`LANGGRAPH_DEPLOYMENT_URL=http://localhost:8123`)
- **CopilotKit Runtime:** Uses internal API routing (`NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit`)
- **LangSmith Tracing:** Enabled by default for monitoring and debugging
- **Google Sheets:** Requires `SHEET_ID` extracted from the Google Sheets URL

---

## Customization

- **Prompts, tools, and workflow:** Edit files in `agent/sample_agent/` (e.g., `nodes.py`, `prompts.py`, `tools/`).
- **UI and dashboard:** Edit React components in `app/copilotkit/`.
- **Environment configuration:** Update the `.env` file with your specific API keys and settings.

---

## Deployment

- **Frontend:** Deploy the Next.js app to Vercel, Netlify, or your own server.
- **Backend:** Deploy the FastAPI app to any Python hosting (e.g., Render, AWS, Azure, GCP, etc.).
- Update the `LANGGRAPH_DEPLOYMENT_URL` in your `.env` file to point to your deployed backend.

---

## Getting API Keys

1. **Google Gemini:** Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Serper:** Sign up at [Serper.dev](https://serper.dev) for search API access
3. **RapidAPI:** Create an account at [RapidAPI](https://rapidapi.com) and subscribe to LinkedIn scraper services
4. **Airtable:** Generate a personal access token from your [Airtable account](https://airtable.com/account)
5. **HubSpot:** Create a private app in your HubSpot developer account
6. **YouTube:** Get an API key from [Google Cloud Console](https://console.cloud.google.com)
7. **LangSmith:** Sign up at [LangSmith](https://smith.langchain.com) for AI application monitoring

---

## License

MIT (or your chosen license)

---

## Acknowledgements

- [Next.js](https://nextjs.org/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [CopilotKit](https://github.com/CopilotKit/CopilotKit)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Gemini](https://ai.google.dev/)
- [LangSmith](https://smith.langchain.com/)
