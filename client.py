import socket, threading
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, ttk
import json
import hashlib

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.current_room = None
        self.connected = False
        self.logged_in = False
        self.rooms = []
        self.create_gui()

    def start(self):
        self.root.mainloop()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("ChatRoom")
        self.root.geometry("600x600")
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=7, fill=tk.BOTH, expand=True)
        
        self.login_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.login_frame, text="Authenticate")
        
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Chat")
        
        self.create_login_frame()
        
        self.create_chat_frame()
        
        self.notebook.tab(1, state="disabled")

    def create_login_frame(self):

        # simple GUI template
        login_container = ttk.Frame(self.login_frame)
        login_container.pack(pady=50)
        
        ttk.Label(login_container, text="Username:").grid(row=0, column=0, pady=3, sticky=tk.W)
        self.username_entry = ttk.Entry(login_container, width=20)
        self.username_entry.grid(row=0, column=1, pady=3)
        
        ttk.Label(login_container, text="Password:").grid(row=1, column=0, pady=3, sticky=tk.W)
        self.password_entry = ttk.Entry(login_container, width=20, show="*")
        self.password_entry.grid(row=1, column=1, pady=3)
        
        button_frame = ttk.Frame(login_container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.login_button = ttk.Button(button_frame, text="Login", command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=20)
        
        self.register_button = ttk.Button(button_frame, text="Register", command=self.register)
        self.register_button.pack(side=tk.LEFT, padx=20)
        
        self.status_var = tk.StringVar(value="Not connected")
        status_label = ttk.Label(self.login_frame, textvariable=self.status_var)
        status_label.pack(pady=10)

    def create_chat_frame(self):
        room_frame = ttk.Frame(self.chat_frame)
        room_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(room_frame, text="Chatroom:").pack(side=tk.LEFT, padx=5)
        
        self.room_var = tk.StringVar()
        self.room_dropdown = ttk.Combobox(room_frame, textvariable=self.room_var, state="readonly")
        self.room_dropdown.pack(side=tk.LEFT, padx=5)
        self.room_dropdown.bind("<<ComboboxSelected>>", self.join_room)
        
        self.create_room_button = ttk.Button(room_frame, text="Create Room", command=self.create_room)
        self.create_room_button.pack(side=tk.LEFT, padx=7)
        
        self.logout_button = ttk.Button(room_frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=tk.RIGHT, padx=7)
        
        status_frame = ttk.Frame(self.chat_frame)
        status_frame.pack(pady=7, fill=tk.X)
        
        self.room_status_var = tk.StringVar(value="Have not joined any room")
        ttk.Label(status_frame, textvariable=self.room_status_var).pack(side=tk.LEFT, padx=10)
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', height=18)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        message_frame = ttk.Frame(self.chat_frame)
        message_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.message_input = ttk.Entry(message_frame)
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_input.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10)
        
        self.message_input.config(state='disabled')
        self.send_button.config(state='disabled')

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 5000))
            self.connected = True
            
            message_receive_thread = threading.Thread(target=self.receive_messages)
            message_receive_thread.daemon = True
            message_receive_thread.start()

            return True
        except Exception:
            messagebox.showerror("Connection Error", "Could not connect to server")
            return False

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        if not self.connected and not self.connect():
            return
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        registration_data = {
            "type": "register",
            "username": username,
            "password": hashed_password
        }
        
        try:
            self.client_socket.send(json.dumps(registration_data).encode('utf-8'))
            self.status_var.set("Registration request sent...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send registration: {str(e)}")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        if not self.connected and not self.connect():
            return
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        login_data = {
            "type": "login",
            "username": username,
            "password": hashed_password
        }
        
        try:
            self.client_socket.send(json.dumps(login_data).encode('utf-8'))
            self.status_var.set("Login request sent...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send login: {str(e)}")

    def handle_login_success(self, username):
        self.username = username
        self.logged_in = True
        self.status_var.set(f"Logged in as {username}")
        
        self.notebook.tab(1, state="normal")
        self.notebook.select(1)
        
        request_data = {
            "type": "get_rooms"
        }
        self.client_socket.send(json.dumps(request_data).encode('utf-8'))

    def logout(self):
        if not self.connected:
            return
            
        try:
            logout_data = {
                "type": "logout"
            }
            self.client_socket.send(json.dumps(logout_data).encode('utf-8'))
            
            self.username = None
            self.current_room = None
            self.logged_in = False
            
            # update UI
            self.notebook.tab(1, state="disabled")
            self.notebook.select(0)
            self.chat_display.config(state='normal')
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state='disabled')
            self.room_status_var.set("Not in any room")
            self.status_var.set("Logged out")
            
            self.password_entry.delete(0, tk.END)
            
        except Exception:
            messagebox.showerror("Error", "Failed to log out ")

    def update_rooms_list(self, rooms):
        self.rooms = rooms
        self.room_dropdown['values'] = rooms
        if rooms:
            self.room_dropdown.current(0)

    def create_room(self):
        room_name = simpledialog.askstring("Create Room", "Enter new room name:", parent=self.root)
        if room_name and room_name.strip():
            room_data = {
                "type": "create_room",
                "room_name": room_name.strip()
            }
            try:
                self.client_socket.send(json.dumps(room_data).encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create room: {str(e)}")

    def join_room(self, event=None):
        selected_room = self.room_var.get()
        if selected_room and selected_room != self.current_room:
            room_data = {
                "type": "join_room",
                "room_name": selected_room
            }
            try:
                self.client_socket.send(json.dumps(room_data).encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to join room: {str(e)}")

    def handle_room_joined(self, room_name):
        self.current_room = room_name
        self.room_status_var.set(f"In room: {room_name}")
        
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
        
        self.message_input.config(state='normal')
        self.send_button.config(state='normal')

    def update_UI(self, new_message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, new_message + '\n')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def send_message(self, event=None):
        if not self.connected or not self.logged_in or not self.current_room:
            messagebox.showinfo("Unable to send message", "Log in and join a room")
            return
        
        message = self.message_input.get().strip()
        if message:
            try:
                message_data = {
                    "type": "message",
                    "room": self.current_room,
                    "message": message
                }
                self.client_socket.send(json.dumps(message_data).encode('utf-8'))
                self.message_input.delete(0, tk.END)
            except Exception:
                messagebox.showerror("Error", "Failed to send message")

    def receive_messages(self):
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                response = json.loads(data)
                
                if response["type"] == "register_response":
                    if response["success"]:
                        messagebox.showinfo("Success", "Registration successful! You can now login.")
                    else:
                        messagebox.showerror("Error", response["message"])
                
                elif response["type"] == "login_response":
                    if response["success"]:
                        self.root.after(0, self.handle_login_success, response["username"])
                    else:
                        messagebox.showerror("Error", response["message"])
                
                elif response["type"] == "room_list":
                    self.root.after(0, self.update_rooms_list, response["rooms"])
                
                elif response["type"] == "room_joined":
                    if response["success"]:
                        self.root.after(0, self.handle_room_joined, response["room"])
                    else:
                        messagebox.showerror("Error", response["message"])
                
                elif response["type"] == "chat_message":
                    formatted_msg = f"{response['username']}: {response['message']}"
                    self.root.after(0, self.update_UI, formatted_msg)
                
                elif response["type"] == "notification":
                    self.root.after(0, self.update_UI, f"SERVER: {response['message']}")
                
            except Exception as e:
                if self.connected:
                    print(f"Error: {str(e)}")
                    self.connected = False
                    self.root.after(0, messagebox.showerror, "Lost Connection", "Lost Connection")
                break

if __name__ == "__main__":
    client = ChatClient()
    client.start()