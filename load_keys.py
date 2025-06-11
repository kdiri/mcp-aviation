import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
gemini_api_key = os.getenv("GEMINI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
claude_api_key = os.getenv("CLAUDE_API_KEY")

# Print API keys or a message if not set
if gemini_api_key:
    print(f"Gemini API Key: {gemini_api_key}")
else:
    print("Gemini API Key not set.")

if openai_api_key:
    print(f"OpenAI API Key: {openai_api_key}")
else:
    print("OpenAI API Key not set.")

if claude_api_key:
    print(f"Claude API Key: {claude_api_key}")
else:
    print("Claude API Key not set.")
