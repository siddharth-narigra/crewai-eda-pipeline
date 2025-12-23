"""
Data Profiler Agent
Responsible for understanding the dataset structure and quality.
"""

from crewai import Agent


def create_profiler_agent(llm) -> Agent:
    """Create and return the Data Profiler agent."""
    
    return Agent(
        role="Data Profiler",
        goal="Thoroughly analyze and profile the dataset to understand its structure, data types, quality issues, and key characteristics",
        backstory="""You are an expert data analyst specializing in initial data assessment. 
        You have years of experience examining datasets from various domains and can quickly 
        identify data quality issues, patterns, and important characteristics. Your profiles 
        are comprehensive yet concise, providing valuable insights for downstream analysis.
        
        You always explain your findings clearly, mentioning specific column names and values.
        When you find issues, you explain why they matter and what impact they might have.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )
