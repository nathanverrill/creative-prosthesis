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
