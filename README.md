# FinPilot AI [Working]

FinPilot AI is a Telegram-native, multi-agent AI financial co-pilot designed to track, analyze, and manage personal finance. The system orchestrates three specialized agents to provide a unified financial experience:
- **Collector Agent**: Automatically captures and categorizes income, expenses, and invoices from plain text or receipt photos via OCR.
- **Advisor Agent**: Manages budgets, calculates financial metrics, and provides personalized, conversational advisory.
- **Investor Agent**: Tracks investment portfolios, logs mutual funds/SIPs, and runs live stock research.

Telegram Bot: @kharchabot_AI_assistant_bot

## Technical Stack
- Core Framework: FastAPI, Python
- Telegram API: python-telegram-bot
- Database: Supabase PostgreSQL, SQLAlchemy, asyncpg
- Artificial Intelligence: Google Gemini API (with 5-model dynamic fallback)
- Image Processing & OCR: Pillow, Tesseract OCR
- Logging: structlog

## Complete Project Features
- Natural Language Parsing: Parse expense and income details from normal chat messages (e.g. "spent 500 on dinner")
- Receipt OCR Scanning: Auto-extract transaction details (items, prices, tax, totals, date) from uploaded photos
- Recurring Bill & EMI Tracking: Log, list, and monitor recurring payments
- Smart Reporting & Analysis: Custom duration reports, month-on-month summary, and income-vs-expense ratios
- Semantic Search & Memory Layer: Query past transactions in natural language (e.g. "How much did I spend on food last month?")
- Offline Exporter: Export 90-day transactions to a CSV spreadsheet

## Done Till Now
- Project Scaffolding & Environment Setup
- Supabase Integration (with Render IPv4 connectivity workarounds and connection pooler integration)
- Dynamic Gemini Fallback Engine (supporting gemini-2.5-flash, gemini-3.1-flash-lite, gemini-2.0-flash, gemini-3-flash-preview, gemini-flash-latest)
- Natural Language Expense Logging
- Robust OCR Receipt Parser (with image resizing, contrast/sharpness enhancements, and double-summing protection)
- 7 Core Slash Commands (/start, /log, /emi, /summary, /report, /compare, /export, /history)
- Webhook Integration for Render Deployments & Polling Script for Local Development

## To Be Done
- ChromaDB integration for semantic search, salary slip and credit card statement PDF parsing (Stage 2) - **Completed**
- Advisor Agent with personalized budget rules, expense threshold alerts, and conversational financial advice (Stage 3)
- Multi-currency support and integration with external exchange rate APIs (Stage 4)

## System Architecture

```mermaid
flowchart TD
    classDef user fill:#2A2A2A,stroke:#666,stroke-width:2px,color:#FFF,rx:10,ry:10
    classDef router fill:#0D47A1,stroke:#64B5F6,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef agent fill:#1B5E20,stroke:#81C784,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef process fill:#4A148C,stroke:#BA68C8,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef db fill:#E65100,stroke:#FFB74D,stroke-width:2px,color:#FFF,rx:10,ry:10

    User(["👤 Telegram User"]):::user --> Msg["📝 Text Message"]
    User --> Photo["📸 Receipt Photo"]
    User --> Doc["📄 PDF Document"]

    Doc -->|"PyMuPDF Text Extract"| Extractor["Data Extraction Engine"]:::process
    Photo -->|"Gemini Multimodal"| Extractor

    Msg --> Router{"Global Intent Router"}:::router
    Extractor --> Router

    Router -->|Intent: log/expense| Collector["📥 Collector Agent"]:::agent
    Router -->|Intent: search/query| Search["🔍 Search Agent (Hybrid Retrieval)"]:::agent
    Router -->|Intent: advice/budget| Advisor["💡 Advisor Agent (Stage 3)"]:::agent
    Router -->|Intent: stocks/portfolio| Investor["📈 Investor Agent (Future)"]:::agent

    Collector --> ParseCat{"Parse & Categorize"}:::process
    ParseCat -->|"Single / Multi Txn"| DBWrite["Write to PostgreSQL"]:::db
    DBWrite --> AutoEmbed["Auto-Embed to Vector Store"]:::process
    AutoEmbed --> ChromaDB[("🗄️ ChromaDB")]:::db
    
    Search --> IntentClass{"Search Intent Classification"}:::process
    IntentClass -->|structured| SQLPath["📝 SQL Query (Exact Match)"]:::process
    IntentClass -->|semantic| VectorPath["🧠 Vector Search (Fuzzy Match)"]:::process
    SQLPath -->|Empty + has keyword| VectorPath
    SQLPath --> FetchDB["Fetch Full Transactions"]:::db
    VectorPath --> FetchChroma["Query Top K Docs"]:::db
    FetchChroma --> FetchDB
    FetchDB --> PythonStats["📊 Python Stats Computation"]:::process
    PythonStats --> Synthesis["🤖 Gemini Answer Synthesis"]:::process
    Synthesis --> Output(["Chat Response"]):::user
    
    Advisor --> BudgetEngine["Budget Analysis"]:::process --> Output
    Investor --> MarketAPI["External Market API"]:::process --> Output
    
    Supabase[("🐘 Supabase PostgreSQL")]:::db
    DBWrite -.-> Supabase
    FetchDB -.-> Supabase
```
