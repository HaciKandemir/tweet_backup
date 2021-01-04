from flask import Flask, render_template, json
app = Flask(__name__)

@app.route('/')
def main():
    with open("tweets.txt", "r") as f:
        tweets = f.read()
    return render_template('index.html', tweets=json.loads(tweets))

@app.route('/log')
def log():
    with open("log.txt", "r") as f:
        logs = f.readlines()
    return render_template('log.html', logs=logs)
