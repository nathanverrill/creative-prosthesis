# app/agents/collaborator.py

from app.agents.base_agent import BaseAgent
from app.graph.state import SongWritingState
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any

class CollaboratorAgent(BaseAgent):
    
    def __init__(self):
        # High temperature for maximum creativity
        super().__init__(agent_name="Collaborator", use_tools=False, temperature=0.9) 

    def __call__(self, state: SongWritingState) -> Dict[str, Any]:
        """Implements the core logic for drafting and revising lyrics."""
        
        # Combine all feedback/suggestions into a single, comprehensive input
        all_feedback = state.get('feedback', []) + state.get('critic_suggestions', [])
        feedback_str = "\n- " + "\n- ".join(all_feedback) if all_feedback else "No feedback provided yet."

        system_prompt = self._get_prompt_template(self.system_prompt_key)
        human_prompt_template = self._get_prompt_template(self.human_prompt_key)
        
        human_prompt = human_prompt_template.format(
            revision_number=state['revision_number'] + 1,
            inspiration=state['inspiration'],
            original_facts="\n".join(state['original_facts']),
            draft_lyrics=state['draft_lyrics'] if state['draft_lyrics'] else "None (initial draft)",
            feedback_and_suggestions=feedback_str
        )

        chain = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ]) | self.llm
        
        # Execute the chain (empty input since all vars formatted)
        try:
            new_lyrics = chain.invoke({})
            new_lyrics = new_lyrics.content
        except Exception as e:
            new_lyrics = f"Revision failed: {str(e)}"

        # Clear iteration-specific state keys upon revision start
        return {
            "draft_lyrics": new_lyrics,
            "revision_number": state['revision_number'] + 1,
            "feedback": [],
            "critic_suggestions": [],
            "critic_scores": {},
            "qa_status": False,
        }