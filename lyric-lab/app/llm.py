import httpx
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f) or {}

OLLAMA_MODEL = config.get("llm_model", "llama3.1")
OLLAMA_ENDPOINT = config.get("ollama_endpoint", "http://host.docker.internal:11434")

def call_ollama(prompt: str) -> str:
    try:
        response = httpx.post(
            f"{OLLAMA_ENDPOINT}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
            timeout=None  # No timeout for stream
        )

        # ✅ Handle streamed JSONL
        lines = response.text.strip().split("\n")
        output = ""
        for line in lines:
            try:
                data = httpx.Response(200, content=line).json()
                output += data.get("response", "")
            except Exception as e:
                print(f"⚠️ Failed to parse line: {line} -> {e}")

        return output.strip()

    except Exception as e:
        print("❌ Ollama call failed:", e)
        return "Ollama failed to generate a response."
