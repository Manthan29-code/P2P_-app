import socket
import os
import base64
from network_utils import send_msg, receive_msg

PORT = 65432

def generate_unique_code():
    """
    Generates a unique code based on the receiver's local IP address.
    """
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    # Encode IP to make it look like a clean unique connection token
    code_bytes = local_ip.encode('utf-8')
    return base64.b32encode(code_bytes).decode('utf-8').replace("=", "")

def decode_unique_code(code):
    """
    Decodes the unique token back into a standard usable IP address string.
    """
    # Pad the string back if necessary for base32 decoding
    rem = len(code) % 8
    if rem:
        code += "=" * (8 - rem)
    try:
        return base64.b32decode(code.encode('utf-8')).decode('utf-8')
    except Exception:
        raise ValueError("Invalid unique connection code entered.")

def start_receiver_mode():
    """
    Acts as a server waiting for a connection using a unique token.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', PORT))
    server_sock.listen(1)
    
    unique_code = generate_unique_code()
    print("\n" + "="*50)
    print(f" Your Unique Receiver Code: {unique_code}")
    print("="*50)
    print("Waiting for the sender to connect...")
    
    conn, addr = server_sock.accept()
    print(f"Connected securely to sender at: {addr[0]}")
    server_sock.close() # Close listening socket as we only need this P2P channel
    return conn

def start_sender_mode(unique_code):
    """
    Acts as a client connecting to a receiver via their unique token.
    """
    target_ip = decode_unique_code(unique_code)
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Attempting connection to target IP: {target_ip}...")
    client_sock.connect((target_ip, PORT))
    print("Connected successfully to receiver!")
    return client_sock

def handle_file_sending(sock):
    """
    Interactive prompt logic allowing a user to send a file through the active socket.
    """
    file_path = input("Enter the full path of the file to send: ").strip('"\' ')
    if not os.path.exists(file_path):
        print("Error: File does not exist. Transaction canceled.")
        return False
        
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    metadata = {
        "file_name": file_name,
        "file_size": file_size
    }
    
    print(f"Sending metadata and streaming file '{file_name}' ({file_size} bytes)...")
    send_msg(sock, metadata, file_path)
    print("Sending complete!")
    return True