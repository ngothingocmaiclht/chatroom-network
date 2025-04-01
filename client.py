import socket, threading
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.connected = False
        self.create_gui()

    def start(self):
        self.root.mainloop()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.geometry("400x400")
        
        # simple template for connection status section
        # pull from the internet
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10, fill=tk.BOTH)        
        self.status_label = tk.Label(status_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.connect_button = tk.Button(status_frame, text="Connect", command=self.connect)
        self.connect_button.pack(side=tk.RIGHT, padx=10)
        
        self.chat_display = scrolledtext.ScrolledText(self.root, state='disabled', height=10)
        self.chat_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        message_frame = tk.Frame(self.root)
        message_frame.pack(padx=5, pady=5, fill=tk.BOTH)
        
        self.message_input = tk.Entry(message_frame)
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.send_button = tk.Button(message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)

    def update_UI(self, new_message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, new_message + '\n')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def connect(self):
        # if already connected -> display a message only
        if self.connected:
            messagebox.showinfo("Connected", "You are already connected to the server.")
            return
        
        try:
            user_input = simpledialog.askstring("Username", "Please give youself a name:", parent=self.root)
            self.username = user_input
            if not self.username:
                messagebox.showerror("Invalid", "Please enter a valid name.")
                return
            
            # connect to server
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('127.0.0.1', 5000))
            
            self.client_socket.send(f"Username:{self.username}".encode('utf-8'))
            
            # Update GUI
            self.connected = True
            self.status_label.config(text=f"Connected")
            self.connect_button.config(text="Disconnect?", command=self.disconnect)

            self.message_input.config(state='normal')
            self.send_button.config(state='normal')
            
            # Start thread to receive messages
            message_receive_thread = threading.Thread(target=self.receive_messages)
            message_receive_thread.daemon = True
            message_receive_thread.start()
            
            self.update_UI("Connected to the chat room.")
            
        except Exception as e:
            print("Error connecting to server" + e)

    def send_message(self, event=None):
        if not self.connected:
            messagebox.showinfo("Not Connected Yet", "Please connect to the server to send message")
            return
        
        message = self.message_input.get().strip()
        if message:
            try:
                print(message)
                self.client_socket.send(message.encode('utf-8'))
                self.message_input.delete(0, tk.END)  # Clear input field
            except Exception as e:
                print("Error sending the message" + e)

    def receive_messages(self):
        while self.connected:
            try:
                new_message = self.client_socket.recv(1024).decode('utf-8')
                self.root.after(0, self.update_UI, new_message)
            except:
                print("Issue receiving messages")
                break

    def disconnect(self):

        if not self.connected: # if not connected then just return and do nothing
            return
        
        try:
            self.connected = False
            if self.client_socket: # close the client socket
                self.client_socket.close()
            
            # update UI
            self.status_label.config(text="Disconnected")
            self.connect_button.config(text="Connect", command=self.connect)
            self.message_input.config(state='disabled')
            self.send_button.config(state='disabled')
            
            self.update_UI("Disconnected from the server.")
            
        except Exception as e:
            print("Error when disconnecting:" + e)

if __name__ == "__main__":
    client = ChatClient()
    client.start()