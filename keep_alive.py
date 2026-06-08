from flask import Flask
from threading import Thread
import random

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Bot Status</title></head>
    <body style="background:#1a1a1a;color:#00ff00;font-family:monospace;text-align:center;padding-top:50px;">
        <h1>🔥 BOT SPAM ĐANG CHẠY</h1>
        <p>ĐỊT MẸ THẰNG NÀO GHEN</p>
        <p>Status: <span style="color:#ff0000;">●</span> ONLINE</p>
        <p id="time"></p>
        <script>setInterval(()=>{document.getElementById('time').innerText=new Date().toLocaleString('vi-VN')},1000)</script>
    </body>
    </html>
    """

@app.route('/ping')
def ping():
    return "🏓 Pong!"

def run():
    # Render yêu cầu port từ biến môi trường PORT
    import os
    port = int(os.environ.get("PORT", random.randint(8000, 9000)))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
