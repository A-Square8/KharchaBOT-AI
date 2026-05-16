# FinPilot AI — System Architecture Flowchart

This diagram outlines the complete end-to-end architecture of FinPilot AI, covering everything from user input routing to the specialized agents (Collector, Search, Advisor, Investor) and the hybrid retrieval pipeline.

```mermaid
flowchart TD
    %% 1. Entry Points
    User["Telegram User"] --> Msg["Text Message"]
    User --> Photo["Receipt Photo"]
    User --> Doc["PDF Document"]

    %% 2. Global Router & Pre-processing
    Doc -->|"PyMuPDF Text Extract"| Extractor["Data Extraction Engine"]
    Photo -->|"Gemini Multimodal"| Extractor

    Msg --> Router{"Global Intent Router"}
    Extractor --> Router

    %% 3. Agent Routing Paths
    Router -->|"Intent: log/expense"| Collector["Collector Agent (Data Ingestion)"]
    Router -->|"Intent: search/query"| Search["Search Agent (Memory Retrieval)"]
    Router -->|"Intent: advice/budget"| Advisor["Advisor Agent (Stage 3)"]
    Router -->|"Intent: stocks/portfolio"| Investor["Investor Agent (Future Stage)"]

    %% ------------------------------------------------------------------
    %% 4. Collector Agent Pipeline (Stage 1 & 2)
    %% ------------------------------------------------------------------
    Collector --> ParseCat{"Parse & Categorize (Gemini)"}
    
    ParseCat -->|"Single Transaction"| DBWrite["Write to PostgreSQL"]
    ParseCat -->|"Credit Card / Salary Slip"| ParseMulti["Parse Multiple Transactions"]
    ParseMulti --> DBWrite
    
    DBWrite --> AutoEmbed["Auto-Embed to Vector Store"]
    AutoEmbed --> ChromaDB[("ChromaDB (Semantic Memory)")]

    %% ------------------------------------------------------------------
    %% 5. Search Agent Pipeline (Hybrid Retrieval)
    %% ------------------------------------------------------------------
    Search --> IntentClass{"Search Intent Classification"}
    
    IntentClass -->|"structured (categories, dates)"| SQLPath["SQL Query (Exact Match)"]
    IntentClass -->|"semantic (vague queries)"| VectorPath["Vector Search (Fuzzy Match)"]
    
    SQLPath -->|"0 results + has keyword"| VectorPath
    
    SQLPath --> FetchDB["Fetch Full Transactions"]
    VectorPath --> FetchChroma["Query Top K Docs"]
    FetchChroma --> FetchDB
    
    FetchDB --> PythonStats["Python Stats Computation (Totals, Categories)"]
    PythonStats --> Synthesis["Gemini Answer Synthesis"]
    
    Synthesis --> Output["Chat Response"]

    %% ------------------------------------------------------------------
    %% 6. Advisor & Investor Stub Pipelines
    %% ------------------------------------------------------------------
    Advisor --> BudgetEngine["Budget & Limit Analysis"]
    Investor --> MarketAPI["External Market API Integration"]
    
    BudgetEngine --> Output
    MarketAPI --> Output

    %% ------------------------------------------------------------------
    %% 7. Core Database
    %% ------------------------------------------------------------------
    Supabase[("Supabase PostgreSQL")]
    DBWrite -.->|"Saves Transactions"| Supabase
    FetchDB -.->|"Reads Data"| Supabase
```
