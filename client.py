import socket
import threading
from chatGUI import ChatGUI

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.connected = False
        self.gui = ChatGUI(self)

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
            
            message_receive_thread = threading.Thread(target=self.receive_messages)
            message_receive_thread.daemon = True
            message_receive_thread.start()
            
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
                self.gui.update_chat(f"{self.username}: {message}")
                self.client_socket.send(message.encode('utf-8'))
                self.gui.message_input.delete(0, len(message))
            except Exception as e:
                self.gui.show_error("Send Error", f"Error sending message: {str(e)}")
                self.disconnect()

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    # Parse JSON message from server
                    try:
                        import json
                        data = json.loads(message)
                        if data['type'] == 'message':
                            display_message = f"{data['username']}: {data['message']}"
                        elif data['type'] == 'notification':
                            display_message = f"Server: {data['message']}"
                        else:
                            display_message = message
                    except json.JSONDecodeError:
                        display_message = message  # Fallback for non-JSON messages
                    self.gui.update_chat(display_message)
            except Exception:
                if self.connected:
                    self.gui.root.after(0, self.disconnect)
                break

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
    client = ChatClient()
    client.start()