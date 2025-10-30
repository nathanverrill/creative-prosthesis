# Lyrics Lab

Creative Prosthesis

Nathan Verrill / Azro Leclaire

October 2025

## 🎤 Lyrics Lab Backend

A containerized Python backend that powers a collaborative, agent-inspired songwriting assistant.  
You provide a theme and a hook, and get structured, versioned, and traceable lyrics — ready for platforms like [Suno](https://www.suno.ai).

---

## 🚀 Features

- ✍️ Theme-based song lyric generation using local LLMs via [Ollama](https://ollama.com)
- 🧠 Line-level tracking of author, version history, and scoring (e.g. creativity, quality)
- 👥 Multi-role inspired collaboration (lyricist, brainstormers, critic, etc.)
- 📊 Finalization with authorship ratio (for copyright/disclosure purposes)
- 🐳 Fully containerized with Docker
- ⚙️ Configurable LLM backend (e.g., `llama3.1`, `mistral-nemo`, etc.)

---

## 📁 Project Structure

```
lyric-lab-backend/
├── app/
│   ├── api.py            # FastAPI routes
│   ├── llm.py            # LLM integration via Ollama
│   ├── models.py         # Pydantic models (Line, Document, History)
│   ├── scoring.py        # Line scoring (quality, creativity, etc.)
│   └── __init__.py
├── config.yaml           # LLM configuration
├── Dockerfile            # For container builds
├── requirements.txt
└── README.md
```

---

## 🛠️ Configuration

Edit `config.yaml` to set your preferred LLM model:

```yaml
llm_provider: ollama
llm_model: llama3.1 # or mistral-nemo
```

Ollama must be running the model locally (e.g. `ollama run llama3.1`).

---

## 🐳 Run with Docker

Build and run the backend:

```bash
docker build -t lyriclab .
docker run -p 8000:8000 lyriclab
```

---

## 🧪 API Endpoints

### `POST /generate/lyrics`

Generate a new draft from theme + hook

**Query Params:**

- `theme`: `"quantum physics at F1"`
- `hook`: `"this is the hook, damnit"`

**Response:**  
Returns a structured `LyricDocument` with line history and scoring.

---

### `GET /finalize/song`

Calculate authorship ratio and produce final output (based on in-memory song)

**Response:**

```json
{
  "status": "finalized",
  "lines": 14,
  "authorship_ratio": 0.21,
  "final_lyrics": "... lyrics as string ..."
}
```

> ⚠️ Requires a song to have been previously generated.

---

## 🔮 Planned Features

- [ ] A/B testing hook selection before writing
- [ ] Integration with UI for editing & visualization
- [ ] Voice/adlib tags per line (e.g. “Danny Ric voice”)
- [ ] Custom agents using CrewAI

---

## 📎 Attribution Use Case

Use the `authorship_ratio` to prove ≥51% human input when required for:

- IP rights under digital copyright laws
- Editorial accountability
- Creative debates 😎

---

## ✅ Requirements

- Python 3.11+
- Docker
- Ollama with your models (e.g. `llama3`, `mistral`, etc.)

---

## 💬 Questions?

You’re building something awesome. If you need:

- API tweaks
- Ollama prompt tuning
- CrewAI-based song generators

→ just ask!
