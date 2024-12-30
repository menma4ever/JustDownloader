from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return "Alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Make sure to call keep_alive in your main script
# keep_alive()  # Uncomment this line in your main script where you want to start the server
