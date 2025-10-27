# app/agents/critics.py

from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Dict, Any, List

# --- Pydantic Schema for Structured Output ---
# This strictly defines the format the LLM MUST follow for scoring.
class CriticScoresOutput(BaseModel):
    """Structured output for the Critics Agent scores."""
    creativity: float = Field(
        description="Score from 0.0 to 1.0 assessing the inventiveness, surprising structure, and quality of the lyrical concepts."
    )
    freshness: float = Field(
        description="Score from 0.0 to 1.0 assessing the avoidance of common tropes and overused lyrical clichés. 1.0 is completely original."
    )
    humor: float = Field(
        description="Score from 0.0 to 1.0 assessing the effectiveness, wit, and comedic timing of any humorous elements."
    )
    fact_check_pass: bool = Field(
        description="True if the lyrics appear factually correct or plausible based on known facts and context, False if errors are detected."
    )
    suggestions: List[str] = Field(
        description="A list of 2-3 specific, actionable suggestions for the next revision to improve the current draft."
    )

class CriticsAgent(BaseAgent):
    
    def __init__(self):
        # Medium temperature for balancing judgment and suggested creativity
        # Needs to be low enough (0.5) to reliably follow the JSON schema
        super().__init__(agent_name="Critics", use_tools=False, temperature=0.5) 

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """
        Scores Creativity, Freshness, Humor, and provides structured suggestions.
        The NSFW check is handled by the dedicated NsfwAgent node.
        """
        
        # --- 1. Dynamic Prompt Retrieval ---
        system_prompt = self._get_prompt_template("critics_system")
        human_prompt_template = self._get_prompt_template("critics_human")

        # Format the human prompt fully
        formatted_human = human_prompt_template.format(
            draft_lyrics=state['draft_lyrics'],
            inspiration=state['inspiration']
        )

        critic_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", formatted_human)
        ])

        # --- 2. Enforce Structured Output ---
        # Binds the LLM to the strict Pydantic schema for reliable JSON scoring.
        critic_chain = critic_prompt | self.llm.with_structured_output(
            schema=CriticScoresOutput
        )

        # --- 3. Execution ---
        try:
            # No extra vars needed (all formatted)
            result: CriticScoresOutput = critic_chain.invoke({})
        except Exception as e:
            print(f"Critics Agent failed to parse output: {e}")
            # Fail safe: Return minimal, failing scores if the parser or LLM fails
            return {
                "critic_scores": {"creativity": 0.0, "freshness": 0.0, "humor": 0.0},
                "critic_suggestions": ["CRITICAL: Critic scoring failed. Review LLM output."],
                "qa_status": False,
            }

        # --- 4. State Update ---
        # Note: fact_check_pass from here; if using separate fact_check_node, override with state['qa_status']
        return {
            "critic_scores": {
                "creativity": result.creativity, 
                "freshness": result.freshness,
                "humor": result.humor,
            },
            "critic_suggestions": result.suggestions,
            # Pass the fact check status directly from the critic's judgment
            "qa_status": result.fact_check_pass,
        }

# Note: The 'CriticsAgent' must be initialized in the workflow.py file.