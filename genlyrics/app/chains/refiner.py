# app/chains/refiner.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

REFINER_SYSTEM_PROMPT = (
    "You are a skilled song editor and rewriter, taking feedback from a harsh critic. "
    "Your goal is to revise the original song lyrics based *specifically* on the provided critique. "
    "Maintain the original theme and F1 context. Improve wordplay, strengthen rhymes, and address any points the critic made. "
    "Output only the revised song lyrics, formatted with [Verse] and [Chorus] tags."
)

REFINER_HUMAN_PROMPT = (
    "Original Song Lyrics:\n"
    "---------------------\n"
    "{original_lyrics}\n"
    "---------------------\n\n"
    "Critique Received:\n"
    "---------------------\n"
    "{critique}\n"
    "---------------------\n\n"
    "Revise the song based *only* on the critique:"
)

def get_refiner_chain(llm: ChatGoogleGenerativeAI):
    """Creates and returns the refiner LangChain chain."""
    print("--- Initializing Chain: Refiner ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", REFINER_SYSTEM_PROMPT),
        ("human", REFINER_HUMAN_PROMPT),
    ])
    # The input to this chain needs 'original_lyrics' and 'critique'
    chain = prompt | llm | StrOutputParser()
    return chain