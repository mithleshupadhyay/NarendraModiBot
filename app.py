from flask import Flask, render_template, request, redirect, jsonify
import openai
import os
import time
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the name of the bot
name = 'Narendra Modi'

# Define the role of the bot
role = 'Narendra Modi'

# Define the impersonated role with instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    YOU ARE NOT AN AI MODEL!
"""

# Initialize variables for chat history
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
threads_dir = os.path.join(cwd, 'threads')

# Ensure the threads directory exists
if not os.path.exists(threads_dir):
    os.makedirs(threads_dir)

history_file = os.path.join(threads_dir, 'New chat.txt')

# Create a new chat history file
with open(history_file, 'w') as f:
    f.write('\n')

# Initialize chat history
chat_history = ''

# Create a Flask web application
app = Flask(__name__)

# Function to complete chat input using OpenAI's GPT-3.5 Turbo
def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
    current_time = time.strftime("%H:%M:%S", time.localtime())
    output = openai.ChatCompletion.create(
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

    for item in output['choices']:
        chatgpt_output = item['message']['content']

    return chatgpt_output

# Function to handle user chat input
def chat(user_input):
    global chat_history, name, chatgpt_output, history_file
    current_day = time.strftime("%d/%m", time.localtime())
    current_time = time.strftime("%H:%M:%S", time.localtime())
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    with open(history_file, 'a') as f:
        f.write('\n'+ current_day+ ' '+ current_time+ ' User: ' +user_input +' \n' + current_day+ ' ' + current_time+  ' ' +  chatgpt_output + '\n')
        f.close()
    
    # Rename the file based on the first user input if it is still named "New chat.txt"
    if os.path.basename(history_file) == 'New chat.txt':
        new_filename = f"{user_input[:50].replace(' ', '_')}.txt"
        new_filepath = os.path.join(threads_dir, new_filename)
        os.rename(history_file, new_filepath)
        history_file = new_filepath
    
    return chatgpt_raw_output

# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Function to get the list of chat history files
@app.route("/history")
def get_history():
    files = [f for f in os.listdir(threads_dir) if f.endswith('.txt')]
    return jsonify({"history": files})

# Function to get the content of a specific chat history file
@app.route("/history/<filename>")
def get_history_file(filename):
    messages = []
    file_path = os.path.join(threads_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                parts = line.split(' ', 2)
                if len(parts) == 3:
                    timestamp, sender, text = parts
                    sender = 'user' if sender == 'User:' else 'bot'
                    messages.append({"text": text.strip(), "sender": sender})
    return jsonify({"messages": messages})

# Function to delete a specific chat history file
@app.route("/history/<filename>", methods=['DELETE'])
def delete_history_file(filename):
    file_path = os.path.join(threads_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return '', 204

# Function to create a new chat history file
@app.route("/new_thread", methods=['POST'])
def new_thread():
    global history_file, chat_history
    history_file = os.path.join(threads_dir, 'New chat.txt')
    with open(history_file, 'w') as f:
        f.write('\n')
    chat_history = ''
    return jsonify({"message": "New thread created", "file": 'New Chat.txt'})

# Define app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
# Function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    return jsonify({"response": get_response(userText)})

@app.route('/refresh')
def refresh():
    time.sleep(600) # Wait for 10 minutes
    return redirect('/refresh')

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

