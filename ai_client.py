import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load settings from the project folder. it takes data from .env file 
load_dotenv(Path(__file__).resolve().parent / ".env")
# it will take our generated  api key from .env 
#os.getenv(): Function from os library. It means "get value from environment".
api_key = os.getenv("GROQ_API_KEY") 
# if dont have api key first generate it and then save it in .env file
#otherwise it will raise run time error of not finding api key
if not api_key:
    raise RuntimeError("Add GROQ_API_KEY to your .env file.")

#base_url="...": Very important. By default OpenAI library goes to api.openai.com. But you are telling it: "Don't go to OpenAI, go to Groq server". Groq made its API compatible with OpenAI format, that's why this trick works.
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

#system prompt
STUDY_INSTRUCTIONS = """
You are an AI Study Assistant for students.

Use simple language and short, clear explanations.
Use an example when it helps explain a concept.

For explanations:
- Define the concept.
- Explain its main idea.
- Give a simple example.

For summaries:
- Summarize the text supplied by the student.
- Preserve its main ideas.
- Ask for the text if none was supplied.

For practice questions:
- Generate the requested number of questions.
- If no number is specified, generate three.
- Put the answer key after the questions.

Use previous messages to understand follow-up questions.
Ask for clarification when necessary.
If uncertain, say so instead of inventing information.
"""
#function to display history.this history will be given every time
def create_history():
    """Start a conversation with the study instructions."""
    return [
        {"role": "system", "content": STUDY_INSTRUCTIONS}
    ]

# below Function that takes one parameter messages - the full conversation history
def get_study_response(messages):
    """Send the conversation to Grok and return its answer."""
    response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1500,
        )
    
    answer = response.choices[0].message.content
    #client.chat.completions.create(): The actual API call. It comes from OpenAI library.
    #messages=messages: Send full history so AI remembers context.
    #Response from server has many parts. response.choices is a list of possible answers. [0] means take first answer..message.content is the actual text the AI wrote.

    if not answer or not answer.strip(): #.strip(): Removes empty spaces. If answer is empty or only spaces, raise error ValueError.
            raise ValueError("The model returned no text answer.")
    
    return answer