import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APIError

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")

if not api_key:
    raise SystemExit("Add GROK_API_KEY to your .env file.")

# Use the OpenAI SDK to connect to xAI.
client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1",
)

model = os.getenv("GROK_MODEL", "grok-4.7")

# Conversation history stays in memory.
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful tutor. "
            "Explain concepts simply and keep answers concise."
        ),
    }
]

print("Grok Streaming Chatbot Started!")
print("Type 'exit' to stop.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        break

    if not user_input:
        continue

    # Build the request with earlier messages.
    next_messages = messages + [
        {"role": "user", "content": user_input}
    ]

    answer_parts = []
    usage = None

    print("Grok: ", end="", flush=True)

    try:
        with client.chat.completions.create(
            model=model,
            messages=next_messages,
            max_tokens=1000,
            stream=True,
            stream_options={"include_usage": True},
        ) as stream:
            for chunk in stream:
                # The usage chunk may have no choices.
                if chunk.usage is not None:
                    usage = chunk.usage

                if chunk.choices:
                    text = chunk.choices[0].delta.content

                    if text:
                        print(text, end="", flush=True)
                        answer_parts.append(text)

    except APIError as error:
        print(f"\nAPI error: {error}\n")
        # Do not save an incomplete exchange to history.
        continue

    print("\n")

    answer = "".join(answer_parts)

    if answer:
        messages = next_messages + [
            {"role": "assistant", "content": answer}
        ]

    if usage is not None:
        print("Input tokens:", usage.prompt_tokens)
        print("Output tokens:", usage.completion_tokens)
        print("Total tokens:", usage.total_tokens)

        # Reasoning tokens are part of completion usage.
        details = usage.completion_tokens_details
        if details is not None:
            print("Reasoning tokens:", details.reasoning_tokens or 0)

        # xAI may report the billed cost in USD ticks.
        cost_ticks = getattr(usage, "cost_in_usd_ticks", None)

        if cost_ticks is not None:
            cost_usd = cost_ticks / 10_000_000_000
            print(f"Request cost: ${cost_usd:.8f}")
        else:
            print("Request cost was not reported.")
    else:
        print("Token usage was not reported.")

    print()