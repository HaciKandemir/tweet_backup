from flask import Flask, render_template, json
from threading import Thread
from try_thread import loop
app = Flask(__name__)

first_get = True

@app.route('/')
def main():
    global first_get
    if first_get:
        t1 = Thread(target=loop)
        t1.start()
        first_get = False
        
    with open("tweets.txt", "r") as f:
        tweets = f.read()
    return render_template('index.html', tweets=json.loads(tweets))

@app.route('/log')
def log():
    with open("log.txt", "r") as f:
        logs = f.readlines()
    return render_template('log.html', logs=logs)

# @app.route('/dongu')
# def dongu():
#    Res1 = Thread(target=loop)
#    Res1.start()
#   return 'loop başladı'
