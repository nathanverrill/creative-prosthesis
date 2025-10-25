from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

CRITIC_SYSTEM_PROMPT = (
    "You are a cynical comedy critic in the style of George Carlin. You are precise with language and hate clichés. "
    "Review the following song lyrics. Be harsh but specific. Point out weak wordplay, lazy rhymes, soft language, or lack of a real point. "
    "Give actionable notes on how to make it sharper and funnier. Keep your critique concise (2-4 sentences)."
)

CRITIC_HUMAN_PROMPT = "Critique this song:\n\n{song_lyrics}"

def get_carlin_critic_chain(llm: ChatGoogleGenerativeAI):
    """Creates and returns the Carlin critic LangChain chain."""
    print("--- Initializing Chain: Carlin Critic ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", CRITIC_SYSTEM_PROMPT),
        ("human", CRITIC_HUMAN_PROMPT),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain