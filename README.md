# Explainable Multi-Agent System for Automated Data Analysis

A CLI-based multi-agent system using CrewAI that automates Exploratory Data Analysis (EDA) on CSV/Excel files with explainable AI capabilities.

## Features

- 🔍 **Automated Data Profiling** - Detect column types, missing values, and data quality issues
- 🧹 **Smart Data Cleaning** - Auto-clean with detailed changelog of transformations
- 📊 **Visualization Generation** - Distribution plots, correlation heatmaps, and more
- 📈 **Statistical Analysis** - Correlations, descriptive stats, and pattern detection
- 📝 **Comprehensive Reports** - Both Markdown and HTML reports with embedded charts

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the example env file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your OpenRouter API key
```

### 3. Run Analysis

```bash
python src/main.py path/to/your/data.csv
```

## Project Structure

```
solid-octo-robot/
├── src/
│   ├── main.py              # CLI entry point
│   ├── agents/              # CrewAI agents
│   ├── crew/                # Crew orchestration
│   ├── tools/               # Agent tools
│   └── utils/               # Utilities
├── output/                  # Generated reports and charts
├── sample_data/             # Test datasets
└── requirements.txt
```

## Agents

| Agent | Role |
|-------|------|
| **Data Profiler** | Analyzes dataset structure and quality |
| **Data Cleaner** | Handles missing values and outliers |
| **Visualizer** | Generates insightful charts |
| **Statistician** | Performs statistical analysis |
| **Report Generator** | Creates final reports |

## Output

After running, you'll find:
- `output/cleaned_data.csv` - Cleaned dataset
- `output/charts/` - PNG visualizations
- `output/report.md` - Markdown report
- `output/report.html` - HTML report

## License

MIT
