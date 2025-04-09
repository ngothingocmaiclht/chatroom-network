import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext

class ChatGUI:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title("Chat Client")
        self.root.geometry("600x600")
        self.create_gui()

    def start(self):
        self.root.mainloop()

    def create_gui(self):
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10, fill=tk.BOTH)        
        self.status_label = tk.Label(status_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.connect_button = tk.Button(status_frame, text="Connect", command=self.client.connect)
        self.connect_button.pack(side=tk.RIGHT, padx=10)
        
        self.chat_display = scrolledtext.ScrolledText(self.root, state='disabled', height=10, wrap=tk.WORD)
        self.chat_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        message_frame = tk.Frame(self.root)
        message_frame.pack(padx=5, pady=5, fill=tk.BOTH)
        
        self.message_input = tk.Entry(message_frame, state='disabled')
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.message_input.bind('<Return>', self.client.send_message)
        
        self.send_button = tk.Button(message_frame, text="Send", command=self.client.send_message, state='disabled')
        self.send_button.pack(side=tk.RIGHT, padx=5)

    def update_status(self, connected):
        self.status_label.config(text="Connected" if connected else "Disconnected")
        self.connect_button.config(
            text="Disconnect" if connected else "Connect",
            command=self.client.disconnect if connected else self.client.connect
        )
        self.message_input.config(state='normal' if connected else 'disabled')
        self.send_button.config(state='normal' if connected else 'disabled')

    def update_chat(self, message):
        self.root.after(0, lambda: self._update_chat(message))

    def _update_chat(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + '\n')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def show_error(self, title, message):
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def show_info(self, title, message):
        self.root.after(0, lambda: messagebox.showinfo(title, message))

    def get_username(self):
        return simpledialog.askstring("Username", "Please give yourself a name:", parent=self.root)