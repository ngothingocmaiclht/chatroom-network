import socket
import threading
import json

class ChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 5001
        self.clients = {}
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        
        print(f"Server is listening on {self.host}:{self.port}")
    
    def start(self):
        try:
            self.accept_connections()
        except KeyboardInterrupt:
            print("\nServer shutting down.")

    def accept_connections(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            
            username = client_socket.recv(1024).decode('utf-8')
            self.clients[client_socket] = username # store user
            
            connect_message = json.dumps({
                'type': 'notification',
                'message': f'{username} has just hopped in'
            }).encode('utf-8')

            self.broadcast(connect_message, client_socket)

            # thread for handling the current client            
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                
                data = json.loads(message.decode('utf-8'))
                
                if data['type'] == 'message':
                    # construct the message
                    broadcast_message = json.dumps({
                        'type': 'message',
                        'username': self.clients[client_socket],
                        'message': data['message']
                    }).encode('utf-8')

                    # broadcast message to all clients
                    self.broadcast(broadcast_message, client_socket)
            
            except:
                self.remove_client(client_socket) # connection loss -> remove client
                break

    def broadcast(self, message, sender_socket=None):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message)
                except:
                    self.remove_client(client)
    
    
    def remove_client(self, client_socket):
        if client_socket in self.clients:
            username = self.clients[client_socket]
            del self.clients[client_socket]
            
            # Broadcast disconnect notification
            disconnect_message = json.dumps({
                'type': 'notification',
                'message': f'{username} has just left'
            }).encode('utf-8')

            # notify other clients
            self.broadcast(disconnect_message)
            
            client_socket.close()    

# Run the server
if __name__ == "__main__":
    server = ChatServer()
    server.start()

import socket
import threading

class ChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', 5000))
        self.clients = {}  

    def start(self):
        self.server_socket.listen()
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.start()
        except Exception as e:
            print("Error starting the server" + e)

    def broadcast(self, message, sender=None):
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            username = self.clients[client_socket]
            disconnect_message = f"SERVER: {username} has left the chat room."
            
            del self.clients[client_socket]
            
            self.broadcast(disconnect_message, client_socket)
            
            try:
                client_socket.close()
            except:
                pass

    def handle_client(self, client_socket, address):
        try:
            username = client_socket.recv(1024).decode('utf-8').split(':', 1)[1].strip()
            
            self.clients[client_socket] = username
            
            connect_message = f"SERVER: {username} has joined the chat room."

            self.broadcast(connect_message)
            
            active_users = f"SERVER: Currently online: {', '.join(self.clients.values())}"
            
            client_socket.send(active_users.encode('utf-8'))

            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    new_message = f"{username}: {data}"
                    
                    self.broadcast(new_message, client_socket)
                except:
                    break
                
        except Exception as e:
            print("Some error happened" + e)
     

    
if __name__ == "__main__":
    server = ChatServer()
    server.start()