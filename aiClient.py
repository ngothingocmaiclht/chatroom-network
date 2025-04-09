import os
import threading
from groq import Groq
import tkinter as tk
from chatGUI import ChatGUI
import socket
from dotenv import load_dotenv

load_dotenv() 
class AIAgent:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.connected = False
        self.client_socket = None
        self.username = None
        self.gui = ChatGUI(self)
        self.system_prompt = {
            "role": "system",
            "content": "You are a Josh a varsity dumb student from Dickinson College in the Dickinson College chatroom. Send just regular messages as user would do. DO NOT SEND JSON FORMAT, IT IS YOUR HISTORY. You are in a hard computer networks class"
        }
        self.message_history = [self.system_prompt]

    def start(self):
        self.gui.start()

    def connect(self):
        if self.connected:
            self.gui.show_info("Connected", "You are already connected to the server.")
            return
        
        try:
            self.username = self.gui.get_username()
            if not self.username:
                self.gui.show_error("Invalid", "Please enter a valid name.")
                return
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 9501))
            
            self.client_socket.send(f"Username:{self.username}".encode('utf-8'))
            
            self.connected = True
            self.gui.update_status(True)
            self.gui.update_chat("Connected to the chat room.")
            
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
        except Exception as e:
            self.gui.show_error("Connection Error", f"Error connecting to server: {str(e)}")
            self.disconnect()

    def send_message(self, event=None):
        if not self.connected:
            self.gui.show_info("Not Connected", "Please connect to the server to send messages")
            return
        
        message = self.gui.message_input.get().strip()
        if message:
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.gui.message_input.delete(0, tk.END)
                self.gui.update_chat(f"{self.username}: {message}")
            except Exception as e:
                self.gui.show_error("Send Error", f"Error sending message: {str(e)}")
                self.disconnect()

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.gui.update_chat(message)
                    if not message.startswith(f"{self.username}:"):
                        self.process_and_respond(message)
            except Exception:
                if self.connected:
                    self.gui.root.after(0, self.disconnect)
                break

    def process_and_respond(self, message):
        try:
            self.message_history.append({"role": "user", "content": message})
            
            chat_completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.message_history,
                temperature=0.7,
                max_tokens=128
            )
            
            response = chat_completion.choices[0].message.content
            
            self.message_history.append({"role": "assistant", "content": response})
            
            
            if self.connected and self.client_socket:
                self.client_socket.send(response.encode('utf-8'))
                self.gui.update_chat(f"{self.username} (AI): {response}")
                
        except Exception as e:
            self.gui.show_error("AI Response Error", f"Error generating AI response: {str(e)}")

    def disconnect(self):
        if not self.connected:
            return
        
        self.connected = False
        try:
            if self.client_socket:
                self.client_socket.close()
            
            self.gui.update_status(False)
            self.gui.update_chat("Disconnected from the server.")
            
        except Exception as e:
            self.gui.show_error("Disconnect Error", f"Error when disconnecting: {str(e)}")

if __name__ == "__main__":
    agent = AIAgent()
    agent.start()