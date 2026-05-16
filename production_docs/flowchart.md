# FinPilot AI — System Architecture Flowchart

This diagram outlines the complete end-to-end architecture of FinPilot AI, covering everything from user input routing to the specialized agents (Collector, Search, Advisor, Investor) and the hybrid retrieval pipeline.

```mermaid
flowchart TD
    %% Styling definitions
    classDef user fill:#2A2A2A,stroke:#666,stroke-width:2px,color:#FFF,rx:10,ry:10
    classDef router fill:#0D47A1,stroke:#64B5F6,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef agent fill:#1B5E20,stroke:#81C784,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef process fill:#4A148C,stroke:#BA68C8,stroke-width:2px,color:#FFF,rx:5,ry:5
    classDef db fill:#E65100,stroke:#FFB74D,stroke-width:2px,color:#FFF,rx:10,ry:10

    %% 1. Entry Points
    User(["👤 Telegram User"]):::user
    Msg["📝 Text Message"]
    Photo["📸 Receipt Photo"]
    Doc["📄 PDF Document"]

    User --> Msg
    User --> Photo
    User --> Doc

    %% 2. Global Router & Pre-processing
    Doc -->|"PyMuPDF Text Extract"| Extractor["Data Extraction Engine"]:::process
    Photo -->|"Gemini Multimodal"| Extractor

    Msg --> Router{"Global Intent Router\n(Gemini & Handlers)"}:::router
    Extractor --> Router

    %% 3. Agent Routing Paths
    Router -->|Intent: log/expense| Collector["📥 Collector Agent\n(Data Ingestion)"]:::agent
    Router -->|Intent: search/query| Search["🔍 Search Agent\n(Memory Retrieval)"]:::agent
    Router -->|Intent: advice/budget| Advisor["💡 Advisor Agent\n(Stage 3)"]:::agent
    Router -->|Intent: stocks/portfolio| Investor["📈 Investor Agent\n(Future Stage)"]:::agent

    %% ------------------------------------------------------------------
    %% 4. Collector Agent Pipeline (Stage 1 & 2)
    %% ------------------------------------------------------------------
    Collector --> ParseCat{"Parse & Categorize\n(Gemini Fallback Engine)"}:::process
    
    ParseCat -->|"Single Transaction"| DBWrite["Write to PostgreSQL"]:::db
    ParseCat -->|"Credit Card / Salary Slip"| ParseMulti["Parse Multiple Transactions\n(Array Extraction)"]:::process
    ParseMulti --> DBWrite
    
    DBWrite --> AutoEmbed["Auto-Embed to Vector Store"]:::process
    AutoEmbed --> ChromaDB[("🗄️ ChromaDB\n(Semantic Memory Vault)")]:::db

    %% ------------------------------------------------------------------
    %% 5. Search Agent Pipeline (Hybrid Retrieval)
    %% ------------------------------------------------------------------
    Search --> IntentClass{"Search Intent Classification\n(Structured vs Semantic)"}:::process
    
    IntentClass -->|structured\n(Has categories, dates, keywords)| SQLPath["📝 SQL Query\n(Exact Match Filters)"]:::process
    IntentClass -->|semantic\n(Vague, conceptual queries)| VectorPath["🧠 Vector Search\n(Fuzzy Match)"]:::process
    
    SQLPath -->|If 0 results + has keyword| VectorPath
    
    SQLPath --> FetchDB["Fetch Full Transactions"]:::db
    VectorPath --> FetchChroma["Query Top K Docs"]:::db
    FetchChroma --> FetchDB
    
    FetchDB --> PythonStats["📊 Python Stats Computation\n(Accurate Totals & Categories)"]:::process
    PythonStats --> Synthesis["🤖 Gemini Answer Synthesis\n(Direct conversational answer)"]:::process
    
    Synthesis --> Output(["Chat Response"]):::user

    %% ------------------------------------------------------------------
    %% 6. Advisor & Investor Stub Pipelines
    %% ------------------------------------------------------------------
    Advisor --> BudgetEngine["Budget & Limit Analysis"]:::process
    Investor --> MarketAPI["External Market API Integration"]:::process
    
    BudgetEngine --> Output
    MarketAPI --> Output

    %% ------------------------------------------------------------------
    %% 7. Core Database
    %% ------------------------------------------------------------------
    Supabase[("🐘 Supabase PostgreSQL")]:::db
    DBWrite -.->|"Saves Transactions"| Supabase
    FetchDB -.->|"Reads Data"| Supabase
```
