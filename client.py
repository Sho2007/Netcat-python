import socket

server_ip = '192.168.1.106'
server_port = 12345 

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((server_ip, server_port))

client_socket.sendall("Hello bro".encode('utf-8'))

response = client_socket.recv(1024).decode('utf-8')
print(f"Response from server: {response}")

client_socket.close()
