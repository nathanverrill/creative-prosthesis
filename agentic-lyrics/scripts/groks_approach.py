import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate  # Core for prompts

from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent
from langchain import hub

# --- FIX ---
# You must provide your Google API key.
# It's best to set this as an environment variable, but for clarity,
# we can set it here. Replace "YOUR_API_KEY_HERE" with your actual key.
# Make sure to `import os` (which you already did).
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"

# Check if the key is still a placeholder
if os.environ["GOOGLE_API_KEY"] == "YOUR_API_KEY_HERE":
    print("="*50)
    print("WARNING: Please replace 'YOUR_API_KEY_HERE' \n         with your actual Google API Key.")
    print("="*50)
    # We can exit here or let it fail on the LLM call.
    # For this fix, we'll let it continue so you see where it's used.

# Initialize Gemini (use 'gemini-1.5-pro' for better creativity)
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
    # Test the connection (optional, but good for debugging)
    # llm.invoke("Hello")
except Exception as e:
    print(f"Error initializing LLM. Is your API key correct? Error: {e}")
    # If the API key is missing or invalid, it will likely fail here.
    # We'll assign a dummy function to llm to prevent further crashes
    # in a real scenario, you'd exit.
    if 'llm' not in locals():
        print("Exiting due to LLM initialization failure.")
        exit()


# Event Context (hardcoded from real 2025 AusGP: Hadjar's formation lap spin-out, father's quantum legacy)
EVENT_CONTEXT = """
F1 Australia GP 2025: Rookie Isack Hadjar (son of quantum physicist Yassine Hadjar) spins out on the formation lap in wet chaos, DNF before the green flag. Helmet etched with quantum equations as tribute. Ties into quantum themes: uncertainty, superposition, entanglement in high-speed failure.
"""

def create_hat_chain(hat_color: str, hat_prompt: str) -> Any:
    """Create a LCEL chain for a De Bono hat (modern replacement for LLMChain)."""
    template = PromptTemplate(
        input_variables=["theme", "event", "previous_ideas"],
        template=f"""{hat_prompt}

Theme: {{theme}}
Event: {{event}}
Previous Ideas: {{previous_ideas}}

Output: Bullet-point ideas from the {hat_color} hat perspective."""
    )
    chain = template | llm | StrOutputParser()
    return chain

# De Bono Hats Prompts
HATS = {
    "White": "Focus on facts: Key elements of quantum physics (e.g., superposition, entanglement) and the F1 crash.",
    "Red": "Emotions: Gut feelings about the crash's drama, excitement of racing, wonder of quantum weirdness.",
    "Black": "Caution: Risks in racing (wet track spins), pitfalls in lyrics (clichés, forced metaphors).",
    "Yellow": "Benefits: How quantum concepts uplift the story—resilience in uncertainty, poetic speed.",
    "Green": "Creativity: Wild ideas—rap battles with particles, choruses as lap crashes.",
    "Blue": "Process: Summarize and structure ideas into verse/chorus hooks."
}

# Persona Prompts (contributors/critics)
PERSONAS = {
    "Lil Dicky": {
        "role": "Humorous rapper: Witty, self-deprecating verses blending quantum puns with F1 fails.",
        "prompt": "Write 8-12 lines of rap lyrics. Infuse humor: Hadjar as 'entangled' in bad luck, particles 'spinning out'."
    },
    "George Carlin": {
        "role": "Satirical critic: Roast the absurdity of quantum-racing metaphors, suggest punchy edits.",
        "prompt": "Critique the draft: Highlight flaws with Carlin-esque sarcasm, propose 4-6 revised lines on uncertainty."
    }
}

def create_persona_chain(name: str, persona: Dict[str, str]) -> Any:
    """Create a LCEL chain for a persona (modern replacement for LLMChain)."""
    template = PromptTemplate(
        input_variables=["theme", "event", "brainstorm", "previous_draft"],
        template=f"""{persona['prompt']}

Theme: {{theme}}
Event: {{event}}
Brainstorm Summary: {{brainstorm}}
Previous Draft: {{previous_draft}}

{persona['role']}
Output: {name}'s contribution (lyrics or critique)."""
    )
    chain = template | llm | StrOutputParser()
    return chain

# Main Function
THEME = "Quantum Physics"
EVENT = EVENT_CONTEXT  # Or pass as input

if __name__ == "__main__":
    
    # Check if the LLM was initialized successfully
    if os.environ["GOOGLE_API_KEY"] == "YOUR_API_KEY_HERE":
        print("\nScript cannot run without a valid GOOGLE_API_KEY. Exiting.")
        exit()

    print("--- Starting Lyric Generation Process ---")

    # Step 1: Brainstorm - Run hats sequentially manually
    previous_ideas = ""
    brainstorm_parts = []
    hat_order = ["White", "Red", "Black", "Yellow", "Green", "Blue"]
    
    # Create chains inside main to avoid global issues
    hat_chains = {color: create_hat_chain(color, prompt) for color, prompt in HATS.items()}
    
    print("\n[Step 1: Running De Bono Hats...]")
    for hat in hat_order:
        print(f"  Thinking with {hat} Hat...")
        # Prepare inputs as dict
        inputs = {
            "theme": THEME,
            "event": EVENT,
            "previous_ideas": previous_ideas
        }
        result = hat_chains[hat].invoke(inputs)
        brainstorm_parts.append(f"{hat} Hat: {result}")
        previous_ideas += f"\n{result}"  # Accumulate for next hat
    
    brainstorm_output = brainstorm_parts[-1]  # Blue hat summary
    print("\n=== Brainstorm Summary (Blue Hat) ===\n", brainstorm_output)

    # Step 2: Initial Draft (LCEL style)
    print("\n[Step 2: Creating Initial Draft...]")
    initial_prompt = PromptTemplate(
        input_variables=["theme", "event", "brainstorm"],
        template="""Using the brainstorm, write an initial 16-line lyric draft (verse-chorus-verse) on {theme} via {event}."""
    )
    initial_chain = initial_prompt | llm | StrOutputParser()
    initial_draft = initial_chain.invoke({"theme": THEME, "event": EVENT, "brainstorm": brainstorm_output})
    print("\n=== Initial Draft ===\n", initial_draft)

    # Step 3: Persona chains (now inside main)
    print("\n[Step 3: Preparing Persona Tools...]")
    persona_chains = {name: create_persona_chain(name, data) for name, data in PERSONAS.items()}

    # Simple ReAct Agent for Refinement: Uses personas as tools to iterate on draft
    @tool
    def lil_dicky_contribute(draft: str) -> str:
        """Lil Dicky adds humorous verses to the draft."""
        print("\n>> Agent called Lil Dicky Tool...")
        chain = persona_chains["Lil Dicky"]
        inputs = {
            "theme": THEME,
            "event": EVENT,
            "brainstorm": brainstorm_output,
            "previous_draft": draft
        }
        return chain.invoke(inputs)

    @tool
    def george_carlin_critique(draft: str) -> str:
        """George Carlin critiques and refines the draft satirically."""
        print("\n>> Agent called George Carlin Tool...")
        chain = persona_chains["George Carlin"]
        inputs = {
            "theme": THEME,
            "event": EVENT,
            "brainstorm": brainstorm_output,
            "previous_draft": draft
        }
        return chain.invoke(inputs)

    tools = [lil_dicky_contribute, george_carlin_critique]
    
    # Pull the standard ReAct prompt
    try:
        refine_prompt = hub.pull("hwchase17/react")
    except Exception as e:
        print(f"Could not pull prompt from LangChain Hub. Using a fallback. Error: {e}")
        # A simple fallback prompt if hub fails
        refine_prompt = PromptTemplate.from_template(
            """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
        )

    refine_agent = create_react_agent(llm, tools, refine_prompt)
    refine_executor = AgentExecutor(
        agent=refine_agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True  # Good practice
    )

    # Step 4: Refine with Agent
    print("\n[Step 4: Running Refinement Agent...]")
    query = "Start with the initial draft. Get Lil Dicky to contribute verses, then have Carlin critique and refine into final lyrics."
    
    # The agent needs the initial draft as context.
    # We pass it as part of the main input string.
    agent_input = {
        "input": query + f"\n\nHere is the Initial Draft to work from:\n{initial_draft}"
    }
    
    final_result = refine_executor.invoke(agent_input)
    final_draft = final_result.get("output", "Agent did not produce a final 'output' string.")
    
    print("\n=== Final Draft Lyrics ===\n", final_draft)

