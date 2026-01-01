# Project Diagrams - Presentation Version

## 1. System Architecture Overview

```mermaid
flowchart LR
    User([User]) -->|Upload CSV| Frontend[Next.js<br/>Frontend]
    Frontend -->|REST API| Backend[FastAPI<br/>Backend]
    Backend -->|Orchestrate| Crew[CrewAI<br/>7 Agents]
    Crew -->|Query| LLM[OpenRouter<br/>LLM]
    Crew -->|Generate| Output[Reports<br/>Charts<br/>Model]
    Output -->|Display| Frontend
    Frontend --> User
    
    style Frontend fill:#4CAF50,color:#fff
    style Backend fill:#2196F3,color:#fff
    style Crew fill:#FF9800,color:#fff
    style LLM fill:#9C27B0,color:#fff
    style Output fill:#FFC107
```

**Key Points:**
- User uploads dataset via modern web UI
- FastAPI backend handles requests
- CrewAI orchestrates 7 specialized agents
- OpenRouter provides LLM intelligence
- Generates reports, charts, and trained models

---

## 2. Multi-Agent Workflow

```mermaid
flowchart TD
    Start([Upload Dataset]) --> Agent1[1. Data Profiler<br/>Analyze Structure]
    Agent1 --> Agent2[2. Data Cleaner<br/>Handle Missing Values]
    Agent2 --> Agent3[3. Visualizer<br/>Generate Charts]
    Agent3 --> Agent4[4. Statistician<br/>Run Tests]
    Agent4 --> Agent5[5. ML Recommender<br/>Train Model]
    Agent5 --> Agent6[6. XAI Agent<br/>SHAP & LIME]
    Agent6 --> Agent7[7. Reporter<br/>Generate Report]
    Agent7 --> End([Complete Analysis])
    
    style Agent1 fill:#e3f2fd
    style Agent2 fill:#e8f5e9
    style Agent3 fill:#fff3e0
    style Agent4 fill:#fce4ec
    style Agent5 fill:#f3e5f5
    style Agent6 fill:#e0f2f1
    style Agent7 fill:#fff9c4
```

**Key Points:**
- Sequential execution ensures quality
- Each agent specializes in one task
- Context flows from one agent to next
- Fully automated pipeline

---

## 3. Data Flow & Processing

```mermaid
flowchart LR
    subgraph Input
        CSV[CSV/Excel<br/>Dataset]
    end
    
    subgraph Processing
        Profile[Profile<br/>Quality Check]
        Clean[Clean<br/>Impute Missing]
        Analyze[Analyze<br/>Statistics]
        Train[Train<br/>ML Model]
    end
    
    subgraph Output
        Report[Report<br/>MD + HTML]
        Charts[Charts<br/>PNG Files]
        Model[Model<br/>PKL File]
    end
    
    CSV --> Profile
    Profile --> Clean
    Clean --> Analyze
    Analyze --> Train
    Train --> Report
    Train --> Charts
    Train --> Model
    
    style Input fill:#e3f2fd
    style Processing fill:#fff3e0
    style Output fill:#e8f5e9
```

**Key Points:**
- Raw data → Cleaned data → Analysis
- Generates 3 types of outputs
- All artifacts saved for reuse

---

## 4. Explainability (XAI) Process

```mermaid
flowchart TD
    Model[Trained<br/>Random Forest] --> XAI{XAI Agent}
    
    XAI -->|Global| SHAP[SHAP Analysis<br/>Feature Importance]
    XAI -->|Local| LIME[LIME Explanation<br/>Single Prediction]
    
    SHAP --> Plot1[SHAP<br/>Summary Plot]
    LIME --> Plot2[LIME<br/>Explanation Plot]
    
    Plot1 --> Report[Added to<br/>Final Report]
    Plot2 --> Report
    
    style Model fill:#2196F3,color:#fff
    style XAI fill:#FF9800,color:#fff
    style SHAP fill:#4CAF50,color:#fff
    style LIME fill:#9C27B0,color:#fff
    style Report fill:#FFC107
```

**Key Points:**
- SHAP: Global feature importance
- LIME: Individual prediction explanation
- Makes "black box" models transparent
- Visualizations included in report

---

## 5. Technology Stack

```mermaid
flowchart TB
    subgraph Frontend["Frontend Stack"]
        NextJS[Next.js 16]
        React[React 19]
        Tailwind[TailwindCSS]
    end
    
    subgraph Backend["Backend Stack"]
        FastAPI[FastAPI]
        CrewAI[CrewAI]
        Pandas[Pandas]
    end
    
    subgraph ML["ML & XAI"]
        SKLearn[Scikit-learn]
        SHAP[SHAP]
        LIME[LIME]
    end
    
    subgraph Deploy["Deployment"]
        Vercel[Vercel<br/>Frontend]
        Render[Render<br/>Backend]
    end
    
    Frontend -.-> Backend
    Backend -.-> ML
    Frontend -.-> Deploy
    Backend -.-> Deploy
    
    style Frontend fill:#61dafb,color:#000
    style Backend fill:#009688,color:#fff
    style ML fill:#ff6f00,color:#fff
    style Deploy fill:#5c6bc0,color:#fff
```

**Key Points:**
- Modern tech stack
- Free deployment options
- Industry-standard ML libraries
- Scalable architecture

---

## Quick Reference

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Next.js | User interface |
| Backend | FastAPI | REST API server |
| Orchestration | CrewAI | Multi-agent coordination |
| LLM | OpenRouter | AI-powered analysis |
| ML | Scikit-learn | Model training |
| XAI | SHAP + LIME | Explainability |
| Deployment | Vercel + Render | Cloud hosting |

---

## Presentation Tips

**For Each Diagram:**

1. **System Architecture** - "Our system has 5 main components working together"
2. **Multi-Agent Workflow** - "7 specialized agents work sequentially like an assembly line"
3. **Data Flow** - "Data goes through 4 stages: Profile → Clean → Analyze → Train"
4. **XAI Process** - "We use both SHAP and LIME to explain our model's predictions"
5. **Tech Stack** - "We use modern, industry-standard technologies"

**Keep it Simple:**
- Point to each box and explain in one sentence
- Use the colored sections to guide attention
- Emphasize automation and AI-powered analysis
