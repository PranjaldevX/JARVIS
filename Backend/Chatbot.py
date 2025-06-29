from groq import Groq  # type: ignore
from json import load, dump
import datetime
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey") or "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"

# Check API key
if not GroqAPIKey:
    print("Error: Groq API key not found in .env file")
    exit(1)

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System prompt
System = (
    f"Hello, I am Pranjal, You are a very accurate and advanced AI chatbot named Maverick, "
    "which also has real-time up-to-date information from the internet.\n"
    "*** Do not tell time until I ask, do not talk too much, just answer the question.***\n"
    "*** Reply in only English, even if the question is in Hindi, reply in English.***\n"
    "*** Do not provide notes in the output, just answer the question and never mention your training data. ***"
)

SystemChatBot = [{"role": "system", "content": System}]

# Load existing chat log
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# Real-time info function
def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        "Please use this real-time information if needed,\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours :{now.strftime('%M')} minutes :{now.strftime('%S')} seconds.\n"
    )

# Clean AI response
def AnswerModifier(answer):
    return "\n".join(line for line in answer.split('\n') if line.strip())

# Chatbot core function
def ChatBot(query):  
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        messages.append({"role": "user", "content": query})

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content

        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(answer)

    except Exception as e:
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(query)

# CLI Interface
if __name__ == "__main__":
    try:
        while True:
            user_input = input("You: ")
            print("Maverick:", ChatBot(user_input))
    except KeyboardInterrupt:
        print("\nChatbot session ended.")
    except Exception as e:
        print(f"Error: {e}")
