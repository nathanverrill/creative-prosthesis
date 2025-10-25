from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

SONGWRITER_SYSTEM_PROMPT = (
    "You are a witty songwriter, like The Lonely Island, but also an F1 fan. "
    "Write a funny song about the provided F1 race results, incorporating the user's theme. "
    "Include specific stats and facts mentioned. Format with [Verse] and [Chorus] tags."
)

SONGWRITER_HUMAN_PROMPT = (
    "Theme: {theme}\n\n"
    "Most Recent F1 Race Info:\n{race_info}\n\n"
    "Write the song:"
)

def get_songwriter_chain(llm: ChatGoogleGenerativeAI):
    """Creates and returns the songwriter LangChain chain."""
    print("--- Initializing Chain: Songwriter ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", SONGWRITER_SYSTEM_PROMPT),
        ("human", SONGWRITER_HUMAN_PROMPT),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain