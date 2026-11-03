from google import genai
from dotenv import load_dotenv
import os

# Load the API key from the .env file
load_dotenv()

# Connect to Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Create a chat session
chat = client.chats.create(
    model="gemini-3.8-flash"
)

print("Welcome to Hina's Gemini Chatbot!")
print("Type 'exit' to quit.\n")

# Chatbot loop
while True:
    message = input("Me: ")

    if message.lower() == "exit":
        print("Goodbye! Chatbot closed.")
        break

    # Send the message to Gemini
    reply = chat.send_message(message)

    # Show Gemini's reply
    print("AI:", reply.text)