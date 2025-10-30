from fastapi import APIRouter, Body
from app.models import LyricDocument, LineEdit, LyricLine
from app.llm import call_ollama
from app.scoring import score_line

router = APIRouter()

# In-memory store for now
doc = LyricDocument(title="Untitled", theme="", lines=[])

@router.post("/generate/lyrics")
def generate_lyrics(theme: str, hook: str):
    prompt = f"Write funny, factual, meme-ready lyrics for a club song based on: {theme}. Use this hook: {hook}"
    raw = call_ollama(prompt)
    lines = raw.split("\n")

    doc = LyricDocument(
        title=theme,
        theme=theme,
        lines=[]
    )

    for line in lines:
        scores = score_line(line)
        edit = LineEdit(
            text=line,
            author="lyricist",
            scores=scores
        )
        lyric_line = LyricLine(
            line_text=line,
            final_author="lyricist",
            authors=["lyricist"],
            history=[edit],
            version=1,
            is_human=False,
            scores=scores
        )
        doc.lines.append(lyric_line)

    return doc

@router.post("/edit/line")
def edit_line(index: int, edit: LineEdit):
    line = doc.lines[index]
    line.history.append(edit)
    line.line_text = edit.text
    line.final_author = edit.author
    line.version += 1
    line.is_human = edit.author == "human"
    line.authors.append(edit.author)
    line.scores = edit.scores or score_line(edit.text)
    return line

@router.get("/history")
def get_lyric_history():
    return doc

from app.models import LyricDocument

@router.post("/finalize/song")
def finalize_song(song: LyricDocument):
    if not song.lines:
        return {
            "error": "No lines in submitted song.",
            "authorship_ratio": 0.0,
            "status": "failed"
        }

    ratio = sum(l.is_human for l in song.lines) / len(song.lines)
    final_text = "\n".join([l.line_text for l in song.lines])

    return {
        "status": "finalized",
        "lines": len(song.lines),
        "authorship_ratio": ratio,
        "final_lyrics": final_text
    }

