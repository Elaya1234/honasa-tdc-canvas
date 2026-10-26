import os
import sys
import time
import shutil
import subprocess
import re
import threading

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"C:\Users\elaya.n\Documents\HONASA TDC"
CLOUDFLARED = os.path.join(ROOT_DIR, "tools", "cloudflared.exe")
PYTHON_EXE = os.path.join(ROOT_DIR, r"IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe")
HTML_FILE = os.path.join(ROOT_DIR, "PDP_Competitive_Research_Canvas.html")
INDEX_FILE = os.path.join(ROOT_DIR, "index.html")

# Ensure index.html exists as a direct copy of PDP_Competitive_Research_Canvas.html
if os.path.exists(HTML_FILE):
    shutil.copyfile(HTML_FILE, INDEX_FILE)
    print("✓ Configured index.html as default landing page")

PORT = 8099

print(f"Starting local HTTP server on port {PORT}...")
server_process = subprocess.Popen(
    [PYTHON_EXE, "-m", "http.server", str(PORT), "--directory", ROOT_DIR],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(1)

print("Starting secure Cloudflare Tunnel...")
tunnel_process = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

public_url = None

def monitor_output():
    global public_url
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    for line in tunnel_process.stdout:
        match = url_pattern.search(line)
        if match and not public_url:
            public_url = match.group(0)
            print("\n" + "=" * 70)
            print("🚀 YOUR LIVE WEBSITE LINK IS READY TO SHARE:")
            print(f"👉  {public_url}  👈")
            print("=" * 70)
            print("\nAnyone with this link can view the full canvas, all 4,192 images,")
            print("and all 258 videos from any phone, laptop, or browser globally!")
            print("Press Ctrl+C anytime to stop sharing.\n")
            
            with open(os.path.join(ROOT_DIR, "LIVE_WEBSITE_LINK.txt"), "w", encoding="utf-8") as f:
                f.write(f"HONASA TDC Competitive Research Canvas - Live Website Link:\n\n{public_url}\n")
            break

t = threading.Thread(target=monitor_output, daemon=True)
t.start()

for _ in range(50):
    if public_url:
        break
    time.sleep(0.5)

if not public_url:
    print("Could not retrieve URL automatically. Checking logs...")
else:
    try:
        tunnel_process.wait()
    except KeyboardInterrupt:
        print("\nStopping server and tunnel...")
    finally:
        server_process.terminate()
        tunnel_process.terminate()
