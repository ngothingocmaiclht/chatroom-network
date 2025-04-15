import socket
import threading
import json
import os

class ChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', 5000))
        
        self.clients = {}  
        
        self.user_db_file = "users.json"
        self.load_users()
        
        self.rooms = {
            "Common": [],
        }

    def load_users(self):
        if not os.path.exists(self.user_db_file):
            with open(self.user_db_file, 'w') as file:
                json.dump({}, file)

        with open(self.user_db_file, 'r') as file:
            try:
                self.users = json.load(file)
            except json.JSONDecodeError:
                self.users = {}

    def save_users(self):
        with open(self.user_db_file, 'w') as file:
            json.dump(self.users, file)

    def start(self):
        self.server_socket.listen()
        print("Server is listening on port 5000")

        try:
            while True:
                client_socket, address = self.server_socket.accept()
                
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.daemon = True
                thread.start()
                
        except Exception:
            print("Error starting the server")

        finally:
            self.server_socket.close()

    def register_user(self, client_socket, username, password):
        if username in self.users:
            self.send_response(client_socket, {
                "type": "register_response",
                "success": False,
                "message": "Username already exists"
            })
            return False
            
        self.users[username] = {
            "password": password
        }
        self.save_users()
        
        self.send_response(client_socket, {
            "type": "register_response",
            "success": True,
            "message": "Registration successful"
        })
        
        return True

    def authenticate_user(self, client_socket, username, password):
        if username not in self.users or self.users[username]["password"] != password:
            self.send_response(client_socket, {
                "type": "login_response",
                "success": False,
                "message": "Invalid username or password"
            })
            return False
            
        # Login successful
        self.clients[client_socket] = {"username": username, "room": None}
        
        self.send_response(client_socket, {
            "type": "login_response",
            "success": True,
            "username": username
        })
        
        return True

    def handle_client(self, client_socket, address):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type")
                    
                    if message_type == "register":
                        username = message_data.get("username")
                        password = message_data.get("password")
                        self.register_user(client_socket, username, password)
                    
                    elif message_type == "login":
                        username = message_data.get("username")
                        password = message_data.get("password")
                        self.authenticate_user(client_socket, username, password)
                    
                    elif message_type == "logout":
                        self.handle_logout(client_socket)
                    
                    elif message_type == "get_rooms":
                        self.get_room_list(client_socket)
                    
                    elif message_type == "create_room":
                        room_name = message_data.get("room_name")
                        self.create_room(client_socket, room_name)
                    
                    elif message_type == "join_room":
                        room_name = message_data.get("room_name")
                        self.join_room(client_socket, room_name)
                    
                    elif message_type == "message":
                        if client_socket in self.clients and self.clients[client_socket]["room"]:
                            room = message_data.get("room")
                            message_content = message_data.get("message")
                            self.broadcast_message(client_socket, room, message_content)
                        
                except json.JSONDecodeError:
                    print(f"Invalid JSON from client: {address}")
                
        except Exception as e:
            print(f"Error handling client {address}: {str(e)}")
        finally:
            self.remove_client(client_socket)

    def send_response(self, client_socket, data):
        try:
            client_socket.send(json.dumps(data).encode('utf-8'))
        except Exception as e:
            print(f"Error sending response: {str(e)}")

    def get_room_list(self, client_socket):
        room_list = list(self.rooms.keys())
        self.send_response(client_socket, {
            "type": "room_list",
            "rooms": room_list
        })

    def create_room(self, client_socket, name):
        if not name or name in self.rooms:
            self.send_response(client_socket, {
                "type": "notification",
                "message": f"Room '{name}' already exists or invalid name"
            })
            return
            
        self.rooms[name] = []
        
        self.join_room(client_socket, name)
        
        for client in self.clients:
            self.get_room_list(client)
            
            
    def join_room(self, client_socket, room_name):
        if room_name not in self.rooms:
            self.send_response(client_socket, {
                "type": "room_joined",
                "success": False,
                "message": "Room does not exist"
            })
            return
            
        if client_socket not in self.clients:
            self.send_response(client_socket, {
                "type": "room_joined",
                "success": False,
                "message": "You must log in first"
            })
            return
            
        # Get client info
        username = self.clients[client_socket]["username"]
        current_room = self.clients[client_socket]["room"]
        
        if current_room:
            if client_socket in self.rooms[current_room]:
                self.rooms[current_room].remove(client_socket)
                
            notification = {
                "type": "notification",
                "message": f"{username} has left the room"
            }
            for client in self.rooms[current_room]:
                self.send_response(client, notification)
        
        self.rooms[room_name].append(client_socket)
        self.clients[client_socket]["room"] = room_name
        
        self.send_response(client_socket, {
            "type": "room_joined",
            "success": True,
            "room": room_name
        })
                
        notification = {
            "type": "notification",
            "message": f"{username} has joined the room"
        }
        for client in self.rooms[room_name]:
            if client != client_socket:
                self.send_response(client, notification)
                
    def broadcast_message(self, sender_socket, room_name, message_content):
        if room_name not in self.rooms:
            return
            
        username = self.clients[sender_socket]["username"]
        
        message_data = {
            "type": "chat_message",
            "username": username,
            "room": room_name,
            "message": message_content
        }
        
        for client_socket in self.rooms[room_name]:
            self.send_response(client_socket, message_data)

    def handle_logout(self, client_socket):
        if client_socket not in self.clients:
            return
            
        username = self.clients[client_socket]["username"]
        current_room = self.clients[client_socket]["room"]
        
        if current_room and current_room in self.rooms:
            if client_socket in self.rooms[current_room]:
                self.rooms[current_room].remove(client_socket)
                
            notification = {
                "type": "notification",
                "message": f"{username} has logged out"
            }
            for client in self.rooms[current_room]:
                self.send_response(client, notification)
        
        del self.clients[client_socket]
        
    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.handle_logout(client_socket)
            
        try:
            client_socket.close()
        except:
            pass

if __name__ == "__main__":
    server = ChatServer()
    server.start()