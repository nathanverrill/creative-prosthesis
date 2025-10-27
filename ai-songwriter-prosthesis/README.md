# Agentic Lyrics

Nathan Verrill / Azro Leclaire

October 2025

The **Agentic AI Lyric Editor** is a dynamic web application designed to help songwriters and creatives co-write with AI. Users can generate initial song lyrics based on a theme, then iteratively edit and refine them in a structured, side-by-side view.

The purpose is to **quantify** human contribution in a fast easy-to-use interface. The system measures the percentage of words  
revised or replaced by the human collaborator, providing a transparent, data-driven view of  
creative authorship.

This feature helps demonstrate that a human’s creative input meaningfully transforms the  
generated text — often exceeding common interpretive thresholds in copyright law (such as  
the “50% human contribution” heuristic). By making creativity measurable, the editor aims  
to reinforce the principle that **human revision is authorship**, even when AI is part of the process.

## Core Features

- **AI-Powered Generation:** Enter any theme (e.g., "Quantum Physics" or "F1 Racing") to generate a full song structure, complete with verses and choruses. (Note: Requires a backend endpoint).
- **Side-by-Side Editor:** A clear, two-column layout showing the original generated lyric (read-only) next to a fully editable input field.
- **"Human Edited" Progress Tracker:** A "gamified" progress bar and percentage display that calculates the word-level difference from the original. A visible 50% goal marker encourages users to make the song their own.
- **Smart Syncing:** A checkbox on each line (enabled by default) automatically syncs edits to all identical lines. This makes editing repeating choruses effortless.
- **Search & Replace:** A built-in tool to quickly find and replace words or phrases across all editable lyrics simultaneously.
- **Export Tools:** Easily copy the final, edited lyrics to your clipboard or save them directly as a `.txt` file.

## How to Use

1.  Enter a song theme into the input box and press "Generate Lyrics."
2.  Wait for the backend to provide the initial draft. (A simulation is included in the file for standalone testing).
3.  Edit the lyrics in the right-hand column. You can uncheck the "Sync" box on any line if you want to edit it individually.
4.  Use the "Search & Replace" tool for large-scale changes.
5.  Watch the "Human Edited" percentage bar climb toward the 50% goal.
6.  Once finished, use the "Copy to Clipboard" or "Save Edited Lyrics (.txt)" buttons to export your work.

## Technology Stack

- **Frontend:** Plain HTML, CSS, and Vanilla JavaScript (ES6+).
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) for a modern, responsive UI.
- **Backend (Intended):** The application is built to query a `/generate` endpoint, making it adaptable to any backend lyric generation API.

## Backend: F1 Songwriting Agent (FastAPI)

This is the FastAPI backend service that powers the F1 Lyric Editor. It implements a multi-agent "chain-of-thought" process using LangChain and Google's Gemini model to generate, critique, and refine song lyrics based on a theme and a specific "mood."

### Key Features

- **Configurable Agent Sequence:** The entire generation process is controlled by a `config.yaml` file. You can define the exact sequence of agents (e.g., search, write, critique, refine) to run.
- **Dynamic Mood Injection:** Uniquely modifies the LLM's system prompt at runtime based on the user's "mood" selection (e.g., "cranky," "stoned," "asshole"), changing the tone of the generated output.
- **LangChain + Google Gemini:** Built with `langchain-core` and `langchain_google_genai`, using the `gemini-2.5-flash` model for fast and capable generation.
- **Modular Design:** Logic is separated into modular components (`tools/`, `chains/`) for easy extension.
- **Async First:** Utilizes `asyncio`, `async/await`, and LangChain's `ainvoke` for non-blocking performance.

### How It Works: The Agent Flow

The core logic resides in the `/generate` endpoint, which orchestrates the agent sequence defined in `config.yaml`. A typical flow is:

1.  A `POST` request is received at `/generate` with a `theme` and `mood`.
2.  The server loads the `agent_sequence` from `config.yaml` (e.g., `['get_f1_results', 'run_songwriter', 'run_carlin_critic', 'run_refiner']`).
3.  It executes each step in order, passing the output of one step as the input to the next.
    - **Step 1: `get_f1_results_async` (Tool)**
      - Fetches external data (e.g., F1 race results).
    - **Step 2: `run_songwriter` (LLM Chain)**
      - Takes the `theme` and `race_info`.
      - Generates the first draft of the song lyrics.
    - **Step 3: `run_carlin_critic` (LLM Chain)**
      - Takes the `lyrics`.
      - A persona-driven (George Carlin-style) LLM critiques the lyrics.
    - **Step 4: `run_refiner` (LLM Chain)**
      - Takes the `original_lyrics` and the `critique`.
      - Rewrites the song based on the feedback.
4.  During each LLM step, the selected `mood` (e.g., "cranky") is injected into the system prompt, influencing the tone of the response.
5.  The final `SongResponse` object is returned, containing the results from every step of the chain.

## 🤝 Shared Principles of Ownership

This code is released as open-source software to empower creators and invite collaboration.  
While the Apache License allows unrestricted integration, **we hope you will** join us in upholding a  
simple principle: that **individuals retain ownership of the works they create** with these tools.

If you build applications or services using this code, we ask — in the spirit of open  
authorship — that you respect and protect your users’ rights to their own generated works.  
In doing so, you help advance a broader cultural and legal recognition of human authorship  
in AI-assisted creativity.

This project also exists to **inspire thoughtful discourse** around digital property rights,  
creative agency, and the evolving definition of authorship in the age of machine collaboration.  
By engaging with us, you contribute not only code or art, but to the  
conversation shaping the future of creative ownership.

## 🧠 License

- **Code:** Apache License 2.0
- **Documentation:** Creative Commons Attribution 4.0 International (CC BY 4.0)

If you’re interested in collaborating, attribution, or research citation, please credit:

> Leclaire, A. (2025). _Creative Prosthesis: AI-Driven Composition and Code-Based Music Generation._  
> Azro Leclaire LLC (Missouri, USA).

# About

### AI Songwriting Prosthesis: Overview

**What it Does**  
This application is an AI-powered collaborative songwriting tool that generates over-the-top satirical rap lyrics in the style of The Lonely Island. Users provide an "inspiration" (e.g., "quantum entanglement") and optional human lines; the system researches facts, drafts/revises lyrics blending absurdity, pop culture refs, and crude wit (8-12 syllables/line, AABB rhymes), incorporates feedback, fact-checks for accuracy, and iterates until the output meets quality thresholds for creativity, freshness, humor, and QA—or hits a max of 5 revisions—yielding a structured JSON song (sections like [verse 1], [chorus]).

**How it Does It**  
It orchestrates a multi-agent workflow:

- **Research**: Gathers 3-5 facts via SERP API for inspiration.
- **Draft/Revise**: Preserves human lines verbatim while escalating machine-generated content with satirical twists.
- **Brainstorm**: Runs three parallel agents (YesAnd for positive amps, NoBut for constructive roasts/fixes, NonSequitur for chaotic sparks) to append diverse feedback.
- **Fact-Check**: Compares draft to facts, flagging issues (PASS/FAIL).
- **Critique**: Ensembles creative (humor/creativity) and factual (freshness/QA) evals via parallel model calls, scoring 0-1, suggesting tweaks, and issuing verdicts (e.g., "Yes, this is funny as hell and it's factual").
- **Loop**: Router conditionally revises if scores < thresholds (default: 0.5 creativity/freshness, 0.4 humor) + QA pass. Outputs preserve structure for easy rendering/parsing.

**Architecture**  
Built on LangGraph's `StateGraph` for orchestration, with a `SongWritingState` TypedDict (e.g., `feedback: Annotated[List[str], add]` for concurrent appends). Nodes are callable agents/functions; edges mix sequential (research → draft → fact-check), parallel (brainstorm branches converge via aggregator), and conditional (post-critique router to END/revise).

- **Models**: Ollama local (Llama3.1:8B for creative agents like Collaborator/YesAnd; Mistral-Nemo:12B for factual like Researcher/Critics) via `ChatOllama`, with task-specific temps (0.1-1.0).
- **Prompts**: Centralized `PromptManager` dict with few-shots; structured I/O via Pydantic/JsonOutputParser.
- **Tools/Utils**: SERP via `SerpAPIWrapper`; helpers like `extract_plain_lyrics` for JSON-to-text. Dockerized for M1 Mac, with Phoenix tracing. Total: ~1-2s/cycle on 32GB unified memory.

### How to Change a Prompt in the AI Songwriting App

1. **Locate the File**: Open `app/prompts/song_prompts.py`. Prompts are defined in the `PROMPTS` dict by key (e.g., `"critics_human"`).

2. **Edit the Prompt**:

   - Find the key (e.g., `"critics_human": r"""Your prompt text here."""`).
   - Modify the string. Use `r"""` for raw strings to handle escapes (e.g., `{{ }}` for literal `{}` in JSON).
   - Save the file.

3. **Reload in Docker**:

   - Restart the container: `docker restart <container_id>` (or rebuild: `docker build --no-cache .`).
   - In code, add `import importlib; importlib.reload(app.prompts.song_prompts)` if testing interactively.

4. **Test**:
   - Run a workflow invoke with sample input: `song_writer_app.invoke({"inspiration": "test", ...})`.
   - Check logs for the updated prompt in action (e.g., via Phoenix traces).
   - Isolate:
     ```python
     from app.utils.prompt_manager import prompt_manager
     print(prompt_manager.get_prompt("your_key"))
     ```

Changes take effect immediately post-reload. For structured outputs, update Pydantic schemas in agents if needed.

### How to Add a New Brainstorm Agent

1. **Define the Agent Class** (in `app/agents/brainstorm.py`):

   - Add: `class NewAgentName(BaseAgent):`
   - In `__init__`: `super().__init__(agent_name="NewAgentName", task_type="creative" or "research", use_tools=False, temperature=0.X)`
   - Override `self.llm` if specializing (e.g., `ChatOllama(model="llama3.1:8b", ..., temperature=0.X)`).
   - In `__call__(self, state: SongWritingState) -> Dict[str, Any]`:
     - Extract `plain_lyrics = extract_plain_lyrics(state['draft_lyrics'])`
     - Build chain: `system_prompt = self._get_prompt_template(self.system_prompt_key)`; format human prompt; `chain = ChatPromptTemplate.from_messages([...]) | self.llm`
     - Try: `response = chain.invoke({})`; `return {"feedback": [f"LABEL: {response.content}"]}`
     - Except: Return error feedback.

2. **Add Prompts** (in `app/prompts/song_prompts.py`):

   - Add keys: `"newagentname_system": "Your system prompt."`, `"newagentname_human": "Your human template with vars like {draft_lyrics}."`

3. **Integrate into Workflow** (in `app/graph/workflow.py`):

   - After other instantiations: `agent_new = NewAgentName()`
   - `workflow.add_node("new_node", agent_new)`
   - Parallel edges: `workflow.add_edge("collaborator", "new_node")`
   - Convergence: `workflow.add_edge("new_node", "aggregate_feedback")`

4. **Reload & Test**:
   - Restart Docker container.
   - Invoke workflow; check logs for new feedback in aggregate (e.g., 4 items now).
   - Isolate: `agent_new({"draft_lyrics": "test"})` in a script.

This adds parallel execution; state merges via `Annotated[List[str], add]`. For custom logic, extend aggregator.

### How to Add a New Workflow Step (e.g., "Add Profanity")

1. **Define the Step** (new file `app/agents/profanity.py` or in existing):

   - Class: `class ProfanityAgent(BaseAgent):`
   - `__init__`: `super().__init__(agent_name="Profanity", task_type="creative", temperature=0.8)`; override `self.llm = ChatOllama(model="llama3.1:8b", ..., temperature=0.9)`.
   - `__call__(self, state: SongWritingState) -> Dict[str, Any]`:
     - `plain_lyrics = extract_plain_lyrics(state['draft_lyrics'])` (import helper).
     - Chain: Format prompts (e.g., "Inject crude, satirical profanity: {draft_lyrics}"); `chain = ... | self.llm`; `response = chain.invoke({})`.
     - Parse response to JSON lines; return `{"draft_lyrics": json.dumps(new_lyrics)}`.

2. **Add Prompts** (in `app/prompts/song_prompts.py`):

   - `"profanity_system": "Amp crude wit: Add escalating profanity, Lonely Island-style (e.g., 'yo mama' twists). Preserve structure."`
   - `"profanity_human": "Draft: {draft_lyrics}\nProfanify:"`

3. **Integrate into Workflow** (in `app/graph/workflow.py`):

   - Instantiate: `agent_profanity = ProfanityAgent()`
   - `workflow.add_node("profanity", agent_profanity)`
   - Edge: e.g., `workflow.add_edge("collaborator", "profanity")`; `workflow.add_edge("profanity", "yes_and")` (adjust for position, e.g., after draft, before brainstorm).

4. **Update State** (if needed, in `app/graph/state.py`): Add keys like `profanity_level: int` with `Annotated` for merging.

5. **Reload & Test**:
   - Restart Docker.
   - Invoke: Check logs for new node; verify output has profanity in `draft_lyrics`.

This inserts sequentially; for parallel, add multiple edges/convergence. Extend aggregator if feedback involved.
