from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

class LineEdit(BaseModel):
    text: str
    author: str
    scores: Optional[Dict[str, float]] = None

class LyricLine(BaseModel):
    line_text: str
    authors: List[str]
    history: List[LineEdit]
    final_author: str
    version: int = 1
    is_human: bool = False
    voice: Optional[str] = None
    is_adlib: Optional[bool] = False

class LyricDocument(BaseModel):
    title: str
    theme: str
    lines: List[LyricLine]
    suno_prompt: Optional[str] = None
