# SERPAPI_API_KEY=7e9942893807e034662c6bb82429ce09b43e5600b915cc8484703eacbb4bdedf
# GOOGLE_API_KEY=AIzaSyBcTdwd6oSan7Nj4uHdhJ2F-2B_5a5KvZ8

# app/config.py

import os
from dotenv import load_dotenv

# Load .env file (auto-skips if not in dev; use os.getenv in prod if needed)
load_dotenv()

# Gemini LLM API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is required for Gemini LLM. Set in .env file.")

# SERP API Key for web searches
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY is required for SERP searches. Set in .env file.")

max_revisions = int(os.getenv("MAX_REVISIONS", "5"))