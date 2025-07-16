# llm_server_daemon.py
import socket
import subprocess
import threading
import sys
import time

HOST = "127.0.0.1"
PORT = 55555

'''
def clear_stdout_buffer(proc):
    # stdout 계속 문제 생겨서 버퍼 비우기 함수를 아예 따로 생성함
    proc.stdout.flush()
    start = time.time()
    while True:
        # 0.1sec - 너무 오래 주면 readline 블록됨.
        if time.time() - start > 0.2:
            break
        line = proc.stdout.readline()
        if not line:
            break
        lstripped = line.strip()
        if lstripped == "" or lstripped.startswith(">") or lstripped.startswith("```"):
            print(f"[BITNET RAW CLEAR] {repr(line)}")
            continue
        if lstripped.startswith("{"):
            break

        try:
            proc.stdout.flush()
            line = proc.stdout.readline()
            if not line:
                break
            print(f"[BITNET RAW CLEAR CHECK] {repr(line)}")
        except Exception:
            break

'''      



bitnet_lock = threading.Lock()
session_started = False  # 최초 질문 구분

BITNET_CMD = [
    "python", "run_inference.py",
    "-m", "models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf",
    "-p", "Your task is to convert user input into JSON format. Output format: \
    {\"device\": string, \"command\": string, \"value\": number, \"Comment\": your response } \
    Input: turn off music Convert Input into JSON. \nOutput:",   
    "-cnv", "-t", "4", "-c", "256"
]

              # 파싱이 문제임. 다시 해보기[해결함]
              # 파싱이 아니라 타이밍이 문제임.
              

def read_json_response(proc):
    json_lines = []
    in_json = False

    while True:
        line = proc.stdout.readline()
        
        if not line:
            break
        line = line.strip()
        #print(f"[BITNET RAW] {repr(line)}")

        if line.startswith("{"):
            in_json = True
            json_lines.append(line)
            continue
        
        if in_json:
            json_lines.append(line)
            if line.endswith("}"):
                break

    return "\n".join(json_lines)
    
def wait_for_input(proc):
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        if "Input:" in line: 
            break


def flush_remaining(proc):
    """
   
    """
    start_time = time.time
    while True:
        proc.stdout.flush()
        line = proc.stdout.readline()
        if not line:
            break
        if "Input:" in line:
            print(f"[BITNET BUFFER CLEAR] {repr(line)}")
            break  # Input: 만나면 멈춤
        print(f"[BITNET BUFFER SKIP] {repr(line)}")

    
    


def handle_client(conn, proc):
    global session_started
    
    try:
        while True:
            
            prompt = conn.recv(65536).decode()
            if not prompt:
                break
                
            with bitnet_lock:
                proc.stdin.write(prompt + "\n")
                proc.stdin.flush()
                
                response = read_json_response(proc)
                print(f"[BitNet Answer] : ", response)
                conn.sendall(response.encode())
                
                #wait_for_input(proc)
                
                #flush_remaining(proc)
                
                '''
                output_lines = []
                json_started = False
                brace_count = 0
                
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    
                    
                    line = line.strip()
                    print(f"[BITNET RAW] {repr(line)}")
                    
                    if not session_started:
                        if line.startswith("Output:"):
                            session_started = True
                        continue
                        
                    # 프롬프트 제거
                    if line.startswith(">"):
                        content = line[1:].strip()
                        if content.startswith("{"):
                            json_started = True
                            output_lines.append(content)
                        continue
                    
                    if line.startswith("```"):
                        continue
                    
                    if line.startswith("{"):
                        json_started = True
                    
                  
                    if json_started:
                        output_lines.append(line)
                        #brace_count += line.count("{")
                        #brace_count -= line.count("}")
                        
                        if line.endswith("}"):
                            break  # end
                  
                response = "\n".join(output_lines)
                print(f"[BitNet Answer]: {response}")
                conn.sendall(response.encode())
                '''

    except Exception as e:
        print(f"[BitNet Daemon] Error: {e}", file=sys.stderr)
    finally:
        conn.close()

def main():
    # Bitnet init booting
    while True:
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
      server.listen(1)
      print(f"[BitNet Daemon] Listening on {HOST}:{PORT}")
      
      
      try:
          while True:
              conn, _ = server.accept()
              handle_client(conn, proc)
              #threading.Thread(target=handle_client, args=(conn, proc), daemon=True).start()
      except KeyboardInterrupt:
          print("[BitNet Daemon] Ended")
      finally:
          proc.terminate()
          server.close()

if __name__ == "__main__":
    main()
