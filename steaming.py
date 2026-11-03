from google import genai
from google.genai import types, errors
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("GEMINI_API_KEY is missing from .env.")

client = genai.Client(api_key=api_key)

chat = client.chats.create(
    model="gemini-3.8-flash",
    config=types.GenerateContentConfig(
        max_output_tokens=1000,
        system_instruction=(
            "You are a helpful tutor. "
            "Give concise explanations with simple examples."
        ),
    ),
)

print("Streaming Gemini Chatbot Started!")
print("Type 'exit' to stop.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        break

    if not user_input:
        continue

    usage = None
    print("Gemini: ", end="", flush=True)

    try:
        for chunk in chat.send_message_stream(user_input):
            if chunk.text:
                print(chunk.text, end="", flush=True)

            # Keep the latest usage report.
            # Do not add usage reports from every chunk together.
            if chunk.usage_metadata is not None:
                usage = chunk.usage_metadata

    except errors.APIError as error:
        print(f"\nAPI error: {error}\n")
        continue

    print("\n")

    if usage is not None:
        print("Input tokens:", usage.prompt_token_count or 0)
        print("Response tokens:", usage.candidates_token_count or 0)
        print("Thinking tokens:", usage.thoughts_token_count or 0)
        print("Total tokens:", usage.total_token_count or 0)
    else:
        print("Token usage was not reported.")

    print()
    
    
    