# llm_server_daemon.py
import socket
import subprocess
import threading
import sys
import io

HOST = "127.0.0.1"
PORT = 55555


BITNET_CMD = [
    "python", "run_inference.py",
    "-m", "models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf",
    "-p", "Your task is to convert user input into JSON format. Output format: \
    {\"device\": string, \"command\": string, \"value\": number, \"Comment\": your response } \
    Input: turn off music Convert Input into JSON. \nOutput:",   
    "-cnv", "-t", "4", "-c", "256"
]

def handle_client(conn, proc):
    try:
        while True:
            prompt = conn.recv(65536).decode()
            if not prompt:
                break
            proc.stdin.write(prompt + "\n")
            proc.stdin.flush()

            buffer = io.StringIO()
            in_output = False  

            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                if not in_output:
                    if line.startswith("Output:"):
                        in_output = True
                        content = line[len("Output:"):].lstrip()
                        if content:
                            buffer.write(content)
                    continue
                if line.strip() == "" or line.strip().endswith("\n"):
                    break
                buffer.write(line)
            
            response = buffer.getvalue()
            print(f"[BitNet Answer] : {response}")
            conn.sendall(response.encode())
            in_output = False
            buffer.close()
    except Exception as e:
        print(f"[BitNet Daemon] Error: {e}", file=sys.stderr)
    #finally:
        #print("bitnet test")
        #conn.close()

def main():
    # Bitnet init booting
    proc = subprocess.Popen(
        BITNET_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[BitNet Daemon] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn, proc), daemon=True).start()
    except KeyboardInterrupt:
        print("[BitNet Daemon] Ended")
    finally:
        proc.terminate()
        server.close()

if __name__ == "__main__":
    main()
