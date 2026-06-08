from flask import Flask
from threading import Thread
import random

app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 Bot đang chạy địt mẹ thằng ghen!"

@app.route('/ping')
def ping():
    return "🏓 Pong! Bot sống khỏe!"

def run():
    app.run(host='0.0.0.0', port=random.randint(8000, 9000))

def keep_alive():
    t = Thread(target=run)
    t.start()
