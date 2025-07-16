import psutil
import matplotlib.pyplot as plt
import time
import subprocess
import os
import threading

BITNET_CMD = [
    "python", "run_inference.py",
    "-m", "models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf",
    "-p", "Your task is to convert user input into JSON format. Output format: \
    {\"device\": string, \"command\": string, \"value\": number, \"Comment\": your response } \
    Input: turn off music Convert Input into JSON. \nOutput:",
    "-cnv", "-t", "4", "-c", "256"
]

save_dir = "./cpu_graph_snapshots2"
os.makedirs(save_dir, exist_ok=True)

x_data, y_data = [], []
MAX_POINTS = 120  

bitnet_process = subprocess.Popen(
    BITNET_CMD,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def monitor_bitnet_output():
    for line in bitnet_process.stdout:
        print(f"[BitNet] {line.strip()}")
        with open(f"{save_dir}/bitnet_output.log", "a") as log_file:
            log_file.write(f"[{time.strftime('%H:%M:%S')}] {line}")

threading.Thread(target=monitor_bitnet_output, daemon=True).start()

try:
    while True:
        cpu = psutil.cpu_percent(interval=5)
        current_time = time.strftime("%H:%M:%S")

        x_data.append(current_time)
        y_data.append(cpu)

        if len(x_data) > MAX_POINTS:
            x_data.pop(0)
            y_data.pop(0)

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.set_ylim(0, 100)
        ax.set_ylabel('CPU Usage (%)')

        ax.plot(range(len(x_data)), y_data, color='lime', marker='o', markersize=3, linewidth=1)
        #ax.set_xticks(range(0, len(x_data), max(1, len(x_data)//10)))
        #ax.set_xticklabels([x_data[i] for i in range(0, len(x_data), max(1, len(x_data)//10))],
         #                   rotation=45, ha='right', fontsize=8)
        label_step = max(1, len(x_data)//100)  
        ax.set_xticks(range(0, len(x_data), label_step))
        ax.set_xticklabels([x_data[i] for i in range(0, len(x_data), label_step)],
                   rotation=45, ha='right', fontsize=6)

        filename = f"{save_dir}/cpu_usage_{time.strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(filename, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)

        print(f"[CPU] save complete: {filename}")

except KeyboardInterrupt:
    print("End : BitNet ending ...")
    bitnet_process.terminate()
    try:
        bitnet_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        bitnet_process.kill()
    print("BitNet complete")
