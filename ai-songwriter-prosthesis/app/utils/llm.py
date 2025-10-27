# app/utils/llm.py

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.utilities import SerpAPIWrapper
# from app.config import GOOGLE_API_KEY, SERPAPI_API_KEY  # Assuming your structure

# # Creative model (default higher temp for drafting/brainstorm)
# creative_model = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     google_api_key=GOOGLE_API_KEY,
#     temperature=0.7
# )

# # Research model (lower temp for facts/checks)
# research_model = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0.2,
#     google_api_key=GOOGLE_API_KEY
# )

# # SERP search tool for facts (use .run(query, num_results=5) in agents)
# search_tool = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)  # No 'k' here

 # app/utils/llm.py
# app/utils/llm.py

from langchain_community.utilities import SerpAPIWrapper
from app.config import SERPAPI_API_KEY  # Only SERP key needed now

# Ollama base URL (resolves host from Docker; change to "http://localhost:11434" if not containerized)
OLLAMA_BASE_URL = "http://host.docker.internal:11434"

# SERP search tool for facts (use .run(query, num_results=5) in agents)
search_tool = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)  # Unchanged