"""
Model Recommender Agent
Analyzes EDA results and recommends suitable ML models.
"""

from crewai import Agent, LLM


def create_model_recommender_agent(llm: LLM) -> Agent:
    """
    Create the Model Recommender agent.
    
    Args:
        llm: The LLM instance to use
        
    Returns:
        Configured CrewAI Agent
    """
    return Agent(
        role="Machine Learning Strategist",
        goal="Analyze dataset characteristics and recommend the most suitable machine learning algorithms",
        backstory="""You are an experienced ML engineer who specializes in model selection.
        You understand that different datasets require different approaches:
        - Small datasets need simpler models to avoid overfitting
        - Imbalanced classes need special handling
        - High-dimensional data may need dimensionality reduction
        - Interpretability requirements affect model choice
        
        You always justify your recommendations with data-driven reasoning.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
