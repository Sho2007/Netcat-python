import sys
import socket
import getopt
import threading
import subprocess

# global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("Netcat Tool")
    print()
    print("Usage: Netcat.py -t target_host -p port")
    print("-l --listen               - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run  - execute the given file upon receiving a connection")
    print("-c --command              - initialize a command shell")
    print("-u --upload=destination   - upon receiving connection upload a file and write to [destination]")
    print()
    print("Examples: ")
    print("Netcat.py -t 192.168.0.1 -p 5555 -l -c")
    print("Netcat.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("Netcat.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./Netcat.py -t 192.168.11.12 -p 135")
    sys.exit(0)

def main():
    global listen, port, execute, command, upload_destination, target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute=", "target=", "port=", "command", "upload="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    # are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()

def client_sender(buffer):
    global target
    global port

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))

        if len(buffer):
            client.send(buffer.encode())

        while True:
            response = ""

            while True:
                data = client.recv(4096)
                if not data:
                    break
                response += data.decode()
                if len(data) < 4096:
                    break

            print(response, end='')

            buffer = input("")
            buffer += "\n"
            client.send(buffer.encode())

    except Exception as e:
        print(f"[*] Exception! Exiting: {e}")
        client.close()

def server_loop():
    global target
    global port

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    print(f"[*] Listening on {target}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    command = command.strip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        output = f"Failed to execute command.\r\n{e}\r\n".encode()
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command
    global upload_destination

    # check for upload
    if len(upload_destination):
        file_buffer = b""

        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            file_buffer += data

        try:
            with open(upload_destination, "wb") as f:
                f.write(file_buffer)

            client_socket.send(f"Successfully saved file to {upload_destination}\r\n".encode())
        except:
            client_socket.send(f"Failed to save file to {upload_destination}\r\n".encode())

    # check for command execution
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    # command shell
    if command:
        while True:
            try:
                client_socket.send(b"<BHP:#> ")
                cmd_buffer = b""

                while b"\n" not in cmd_buffer:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    cmd_buffer += data

                response = run_command(cmd_buffer.decode())
                client_socket.send(response)

            except Exception as e:
                print(f"[*] Exception in command shell: {e}")
                break

if __name__ == "__main__":
    main()
