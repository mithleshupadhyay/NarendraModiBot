from flask import Flask, render_template, request, redirect, jsonify
import openai
import os
import time
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=".env", override=True)

# Get the API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: OPENAI_API_KEY is not set in .env file!")
openai.api_key = api_key
print(f"✅ OpenAI API Key Loaded: {api_key[:5]}... (hidden for security)")

# Define bot name and role
name = 'Narendra Modi'
role = 'Narendra Modi'

# Define impersonation role instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    YOU ARE NOT AN AI MODEL!
"""

# Initialize chat history variables
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
threads_dir = os.path.join(cwd, 'threads')

# Ensure the threads directory exists
os.makedirs(threads_dir, exist_ok=True)

history_file = os.path.join(threads_dir, 'New_chat.txt')
with open(history_file, 'w') as f:
    f.write('\n')

chat_history = ''

# Create Flask app
app = Flask(__name__)

def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
    current_time = time.strftime("%H:%M:%S", time.localtime())
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            temperature=1,
            presence_penalty=0,
            frequency_penalty=0,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": f"{impersonated_role}. Conversation history: {chat_history}"},
                {"role": "user", "content": f"{user_input}. {explicit_input}"},
                {"role": "system", "content": f"The current time is {current_time}."}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except openai.error.OpenAIError as e:
        print(f"⚠️ OpenAI API Error: {e}")
        return "⚠️ Error: Could not process request. Please try again later."

def chat(user_input):
    global chat_history, name, chatgpt_output, history_file
    current_day = time.strftime("%d/%m", time.localtime())
    current_time = time.strftime("%H:%M:%S", time.localtime())
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    
    with open(history_file, 'a') as f:
        f.write(f'\n{current_day} {current_time} User: {user_input}\n{current_day} {current_time} {chatgpt_output}\n')
    
    if os.path.basename(history_file) == 'New_chat.txt':
        new_filename = f"{user_input[:50].replace(' ', '_')}.txt"
        new_filepath = os.path.join(threads_dir, new_filename)
        os.rename(history_file, new_filepath)
        history_file = new_filepath
    
    return chatgpt_raw_output

def get_response(userText):
    return chat(userText)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return jsonify({"response": get_response(userText)})

if __name__ == "__main__":
    app.run(debug=True)

