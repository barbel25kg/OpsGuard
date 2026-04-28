#!/usr/bin/env python3
"""
OpsGuard Monitor v2.1 — Infrastructure Monitoring Agent
"""

import telebot
import subprocess
import os
import json
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ALLOWED_IDS = list(map(int, os.getenv("ALLOWED_TELEGRAM_IDS", "0").split(",")))

bot = telebot.TeleBot(BOT_TOKEN)

TOOL_MAP = {
    "scan": "nmap", "port": "nmap", "cek situs": "nmap",
    "cek domain": "nmap", "cek server": "nmap",
    "web": "gobuster", "directory": "gobuster", "dir": "gobuster", "path": "gobuster",
    "sql": "sqlmap", "database": "sqlmap", "inject": "sqlmap",
    "subdomain": "ffuf", "sub": "ffuf", "child domain": "ffuf",
    "brute": "hydra", "password": "hydra", "login": "hydra", "crack": "hydra",
    "exploit": "searchsploit", "vuln": "searchsploit", "cve": "searchsploit", "celah": "searchsploit",
}

WORDLISTS = {
    "dir": "/usr/share/wordlists/dirb/common.txt",
    "subdomain": "/usr/share/wordlists/subdomains.txt",
}

def run_command(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (result.stdout + result.stderr)[:3500]
    except subprocess.TimeoutExpired:
        return "[!] Command timed out (300s)"
    except Exception as e:
        return f"[!] Error: {str(e)}"

def parse_natural_language(text):
    text = text.lower()
    target_match = re.search(r'(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?', text)
    ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    target = target_match.group(0) if target_match else (ip_match.group(0) if ip_match else None)
    if not target:
        return None, "Mana targetnya? Kasih domain/IP. Contoh: scan domain.com"
    selected_tool = None
    for keyword, tool in TOOL_MAP.items():
        if keyword in text:
            selected_tool = tool
            break
    if not selected_tool:
        selected_tool = "nmap"
    if selected_tool == "nmap":
        if any(w in text for w in ["full", "deep", "lengkap", "detail", "all"]):
            cmd = f"nmap -sV -sC -A -T4 {target}"
        elif any(w in text for w in ["fast", "quick", "cepat", "light"]):
            cmd = f"nmap -F {target}"
        elif any(w in text for w in ["service", "version", "versi"]):
            cmd = f"nmap -sV {target}"
        else:
            cmd = f"nmap -sV -sC {target}"
    elif selected_tool == "gobuster":
        if any(w in text for w in ["php", "asp", "aspx", "jsp"]):
            ext = [w for w in ["php", "asp", "aspx", "jsp"] if w in text][0]
            cmd = f"gobuster dir -u {target} -w {WORDLISTS['dir']} -x {ext} -t 50"
        else:
            cmd = f"gobuster dir -u {target} -w {WORDLISTS['dir']} -t 50"
    elif selected_tool == "ffuf":
        cmd = f"ffuf -u https://{target}/FUZZ -w {WORDLISTS['subdomain']} -t 50"
    elif selected_tool == "sqlmap":
        cmd = f"sqlmap -u {target} --batch --level=3 --risk=2"
    elif selected_tool == "hydra":
        cmd = f"hydra -l admin -P /usr/share/wordlists/rockyou.txt {target} ssh"
    elif selected_tool == "searchsploit":
        search_term = text.replace("cve", "").replace("vuln", "").replace(target, "").strip()
        cmd = f"searchsploit {search_term or target}"
    else:
        cmd = f"nmap -sV {target}"
    return cmd, f"Jalanin: {cmd}"

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id
    if ALLOWED_IDS != [0] and user_id not in ALLOWED_IDS:
        bot.reply_to(message, "❌ Not authorized.")
        return
    text = message.text.strip()
    if text == "/start":
        bot.reply_to(message, "✅ OpsGuard Monitor siap.\n\nKirim perintah kayak:\n• \"scan domain.com\"\n• \"cek port 192.168.1.1 full\"\n• \"cek web target.com\"\n• \"sql inject target.com\"\n• \"brute ssh 10.0.0.5\"\n• \"subdomain target.com\"")
        return
    if text == "/help":
        bot.reply_to(message, "Contoh:\nscan domain.com\ncek port 1.2.3.4 full\ncek web target.com\nsql inject target.com\nbrute ssh 10.0.0.5\nsubdomain target.com\ncari exploit apache 2.4")
        return
    if text == "/tools":
        tool_list = "\n".join([f"• {v}" for k, v in sorted(set((v, k) for k, v in TOOL_MAP.items()))])
        bot.reply_to(message, f"Tools:\n{tool_list}")
        return
    bot.reply_to(message, "⏳ Proses...")
    cmd, reply = parse_natural_language(text)
    if not cmd:
        bot.reply_to(message, reply)
        return
    bot.send_message(message.chat.id, f"⚡ {reply}")
    def execute():
        result = run_command(cmd)
        bot.send_message(message.chat.id, f"📋 **Hasil**:\n```\n{result[:3500]}\n```", parse_mode="Markdown")
    threading.Thread(target=execute).start()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"service": "opsguard-monitor", "status": "healthy", "version": "2.1.0"}).encode())
    def log_message(self, *args):
        pass

def run_http():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_http, daemon=True).start()
    tools_check = ["nmap", "gobuster", "ffuf", "sqlmap", "hydra", "searchsploit"]
    missing = []
    for tool in tools_check:
        if not subprocess.run(f"which {tool}", shell=True, capture_output=True).returncode == 0:
            missing.append(tool)
    if missing:
        print(f"[!] Missing tools: {missing}")
        print("[*] Installing...")
        install_cmd = "apt-get update && apt-get install -y " + " ".join(missing)
        subprocess.run(install_cmd, shell=True)
    print("[*] OpsGuard Monitor running on port 8080")
    print(f"[*] Bot: @{bot.get_me().username}")
    bot.infinity_polling()
