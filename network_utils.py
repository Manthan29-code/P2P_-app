import socket
import struct
import json
import os

BUFFER_SIZE = 4096

def send_msg(sock, metadata, file_path=None):
    """
    Sends a JSON metadata header followed by the actual file data safely over TCP.
    """
    # 1. Prepare and send metadata
    meta_bytes = json.dumps(metadata).encode('utf-8')
    meta_len = len(meta_bytes)
    
    # Pack the length of metadata into 4 bytes integer
    sock.sendall(struct.pack('!I', meta_len))
    sock.sendall(meta_bytes)
    
    # 2. If a file path is provided, stream the file in binary chunks
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)

def receive_msg(sock, output_dir="received_files"):
    """
    Receives a JSON metadata header and streams the incoming file to disk.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 1. Read metadata length (4 bytes)
    raw_meta_len = sock.recv(4)
    if not raw_meta_len:
        return None
    meta_len = struct.unpack('!I', raw_meta_len)[0]
    
    # 2. Read exact metadata bytes
    meta_bytes = b""
    while len(meta_bytes) < meta_len:
        packet = sock.recv(meta_len - len(meta_bytes))
        if not packet:
            return None
        meta_bytes += packet
        
    metadata = json.loads(meta_bytes.decode('utf-8'))
    
    # 3. If file data is expected, read the exact file size out of the socket stream
    file_name = metadata.get("file_name")
    file_size = metadata.get("file_size", 0)
    
    if file_name and file_size > 0:
        save_path = os.path.join(output_dir, file_name)
        bytes_received = 0
        
        with open(save_path, 'wb') as f:
            while bytes_received < file_size:
                to_read = min(BUFFER_SIZE, file_size - bytes_received)
                chunk = sock.recv(to_read)
                if not chunk:
                    raise ConnectionError("Socket connection broken during file transfer.")
                f.write(chunk)
                bytes_received += len(chunk)
        
        print(f"\n[Success] File saved completely to: {save_path}")
    
    return metadata