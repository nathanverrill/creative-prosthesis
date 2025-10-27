# ==============================================================================
# --- app/agents/critics.py ---
# ==============================================================================
from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
import json

# --- Pydantic Schema for Structured Output ---
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
# --- Helper Function (Copied for local use) ---
def extract_plain_lyrics_critics(draft_lyrics_json_str: str) -> str:
    """Extracts a simple, readable string from the structured lyrics JSON."""
    if not draft_lyrics_json_str:
        return "No current draft."
    try:
        lyrics_list = json.loads(draft_lyrics_json_str)
        return "\n".join([item.get('line', '') for item in lyrics_list if isinstance(item, dict)])
    except:
        return draft_lyrics_json_str
# --- End Helper Function ---


class CriticsAgent(BaseAgent):
    
    def __init__(self):
        super().__init__(agent_name="Critics", task_type="research", use_tools=False, temperature=0.3)
        # Override for grounded scoring/QA
        self.llm = ChatOllama(
            model="mistral-nemo:12b",
            base_url="http://host.docker.internal:11434",
            temperature=0.3
        )

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Scores Creativity, Freshness, Humor, and provides structured suggestions with ensemble verdict."""
        
        # 1. Prepare input: Convert JSON to plain text for the critic prompt
        plain_lyrics = extract_plain_lyrics_critics(state['draft_lyrics'])
        
        system_prompt = self._get_prompt_template("critics_system")
        human_prompt_template = self._get_prompt_template("critics_human")

        formatted_human = human_prompt_template.format(
            draft_lyrics=plain_lyrics,
            inspiration=state['inspiration']
        )

        # Ensemble: Parallel creative (humor/creativity) and factual (freshness/QA) evals
        creative_llm = ChatOllama(model="llama3.1:8b", base_url="http://host.docker.internal:11434", temperature=0.7)
        factual_llm = ChatOllama(model="mistral-nemo:12b", base_url="http://host.docker.internal:11434", temperature=0.3)

        creative_prompt = ChatPromptTemplate.from_messages([
            ("system", "Lonely Island comedian: Score humor (0-1) and creativity (0-1) for satirical escalation and wit."),
            ("human", formatted_human)
        ])
        factual_prompt = ChatPromptTemplate.from_messages([
            ("system", "Fact-checker: Score freshness (0-1) for originality, check facts (true/false), and suggest fixes."),
            ("human", formatted_human)
        ])

        # Parallel chains
        parallel_eval = RunnableParallel(
            creative=(creative_prompt | creative_llm),
            factual=(factual_prompt | factual_llm)
        )
        results = parallel_eval.invoke({})

        # Synthesize verdict with factual_llm
        decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a decision-maker. Review creative eval (humor/creativity) and factual eval (freshness/QA).
            Output JSON with scores, fact_check_pass, suggestions (2-3 items), and verdict like: "Yes, this is funny as hell and it's factual" or "No, revise [issue]". Use the schema."""),
            ("human", f"Creative eval: {results['creative'].content}\nFactual eval: {results['factual'].content}")
        ])

        critic_chain = decision_prompt | self.llm.with_structured_output(schema=CriticScoresOutput)

        # 3. Execution
        try:
            result: CriticScoresOutput = critic_chain.invoke({})
        except Exception as e:
            print(f"Critics Agent failed to parse output: {e}")
            return {
                "critic_scores": {"creativity": 0.0, "freshness": 0.0, "humor": 0.0},
                "critic_suggestions": ["CRITICAL: Critic scoring failed. Review LLM output."],
                "qa_status": False,
            }

        # 4. State Update
        # Combine new suggestions with existing feedback for the next cycle.
        combined_feedback = state.get("feedback", []) + result.suggestions
        
        return {
            "critic_scores": {
                "creativity": result.creativity, 
                "freshness": result.freshness,
                "humor": result.humor,
            },
            "critic_suggestions": result.suggestions,
            "feedback": combined_feedback, 
            "qa_status": result.fact_check_pass,
        }