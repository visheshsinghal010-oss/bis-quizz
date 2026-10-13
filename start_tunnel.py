import subprocess
import re
import sys
import os
import time

def start_cloudflare_tunnel():
    bin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")
    cmd = [bin_path, "tunnel", "--url", "http://127.0.0.1:5000"]
    
    print("[*] Starting Cloudflare Tunnel on http://127.0.0.1:5000...")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    url_found = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    start_time = time.time()
    # Read stderr where cloudflared logs its tunnel info
    while time.time() - start_time < 30:
        line = process.stderr.readline()
        if not line:
            time.sleep(0.1)
            continue
        print(line.strip())
        match = url_pattern.search(line)
        if match:
            url_found = match.group(0)
            break

    if url_found:
        print("=" * 60)
        print("PUBLIC TUNNEL URL CREATED SUCCESSFULLY:")
        print(url_found)
        print("=" * 60)
        url_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_url.txt")
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url_found)
        return url_found, process
    else:
        print("[!] Could not detect public URL within 30 seconds.")
        return None, process

if __name__ == "__main__":
    url, proc = start_cloudflare_tunnel()
    if url:
        print(f"Tunnel is running at: {url}")
        # Keep process alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            proc.terminate()
