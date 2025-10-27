from app.graph.state import SongWritingState
from app.utils.llm import get_llm
from app.utils.prompt_manager import PromptManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import json

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
    verdict: str = Field(
        description="A concise ensemble verdict like 'Yes, this is funny as hell and it's factual' or 'No, creative but inaccurate—revise.'"
    )

def extract_plain_lyrics_critics(draft_lyrics: List[dict]) -> str:
    """Extracts a simple, readable string from the structured lyrics."""
    if not draft_lyrics or not isinstance(draft_lyrics, list):
        return "No current draft."
    try:
        return "\n".join([item.get('line', '') for item in draft_lyrics if isinstance(item, dict)])
    except:
        return str(draft_lyrics)

class CriticsAgent:
    
    def __init__(self):
        self.creative_llm = get_llm("critic_creative_model")
        self.factual_llm = get_llm("critic_factual_model")
        self.synthesizer_llm = get_llm("critic_synthesizer_model")
        self.llm = self.synthesizer_llm
        self.prompt_manager = PromptManager()

    async def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Scores Creativity, Freshness, Humor, and provides structured suggestions with ensemble verdict."""
        
        plain_lyrics = extract_plain_lyrics_critics(state['draft_lyrics'])
        topic = state.get('topic', 'No topic provided')

        formatted_human = f"TOPIC: {topic}\n\nDRAFT LYRICS:\n{plain_lyrics}"

        creative_prompt = ChatPromptTemplate.from_messages([
            ("system", "Lonely Island comedian: Score humor (0-1) and creativity (0-1) for satirical escalation and wit."),
            ("human", formatted_human)
        ])
        factual_prompt = ChatPromptTemplate.from_messages([
            ("system", "Fact-checker: Score freshness (0-1) for originality, check facts (true/false), and suggest fixes."),
            ("human", formatted_human)
        ])

        parallel_eval = RunnableParallel(
            creative=(creative_prompt | self.creative_llm),
            factual=(factual_prompt | self.factual_llm)
        )
        results = await parallel_eval.ainvoke({})

        decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a decision-maker. Review creative eval (humor/creativity) and factual eval (freshness/QA).
            Output JSON with scores, fact_check_pass, suggestions (2-3 items), and verdict like: "Yes, this is funny as hell and it's factual" or "No, revise [issue]". Use the schema."""),
            ("human", f"Creative eval: {results['creative'].content}\nFactual eval: {results['factual'].content}")
        ])

        critic_chain = decision_prompt | self.llm.with_structured_output(schema=CriticScoresOutput)

        try:
            result: CriticScoresOutput = await critic_chain.ainvoke({})
        except Exception as e:
            print(f"Critics Agent failed to parse output: {e}")
            return {
                "critic_scores": {"creativity": 0.0, "freshness": 0.0, "humor": 0.0},
                "critic_suggestions": ["CRITICAL: Critic scoring failed. Review LLM output."],
                "qa_status": False,
            }

        combined_feedback = state.get("brainstorm_feedback", []) + result.suggestions
        
        return {
            "critic_scores": {
                "creativity": result.creativity, 
                "freshness": result.freshness,
                "humor": result.humor,
            },
            "critic_suggestions": result.suggestions,
            "brainstorm_feedback": combined_feedback, 
            "qa_status": result.fact_check_pass,
        }

_critics_agent_instance = CriticsAgent()

async def critics_node(state: SongWritingState):
    """
    A simple wrapper to make the CriticsAgent class compatible
    with the LangGraph .add_node() function.
    """
    print("---CRITICS: RUNNING ENSEMBLE EVALUATION (ASYNC)---")
    return await _critics_agent_instance(state)