import socket
import threading
import json

class ChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 9501  # Matches client
        self.clients = {}
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        
        print(f"Server is listening on {self.host}:{self.port}")
    
    def start(self):
        try:
            self.accept_connections()
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            self.shutdown()
        except Exception as e:
            print(f"Server error: {str(e)}")
            self.shutdown()

    def accept_connections(self):
        while True:
            try:
                client_socket, _ = self.server_socket.accept()
                
                username_data = client_socket.recv(1024).decode('utf-8')
                if not username_data.startswith("Username:"):
                    client_socket.close()
                    continue
                username = username_data.split(":", 1)[1].strip()
                self.clients[client_socket] = username
                
                connect_message = json.dumps({
                    'type': 'notification',
                    'message': f'{username} has joined the chat'
                }).encode('utf-8')
                self.broadcast(connect_message, client_socket)
                
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"Error accepting connection: {str(e)}")

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                broadcast_message = json.dumps({
                    'type': 'message',
                    'username': self.clients[client_socket],
                    'message': message
                }).encode('utf-8')
                self.broadcast(broadcast_message, client_socket)
            
            except Exception:
                self.remove_client(client_socket)
                break

    def broadcast(self, message, sender_socket=None):
        for client in list(self.clients.keys()):
            if client != sender_socket:
                try:
                    client.send(message)
                except:
                    self.remove_client(client)
    
    def remove_client(self, client_socket):
        if client_socket in self.clients:
            username = self.clients[client_socket]
            del self.clients[client_socket]
            
            disconnect_message = json.dumps({
                'type': 'notification',
                'message': f'{username} has left the chat'
            }).encode('utf-8')
            self.broadcast(disconnect_message)
            
            try:
                client_socket.close()
            except:
                pass
    
    def shutdown(self):
        for client in list(self.clients.keys()):
            self.remove_client(client)
        self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()