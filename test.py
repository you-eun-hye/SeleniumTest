from flask import Flask
import urllib.request

app = Flask(__name__)

@app.route("/")
def cookie():
    return "cookie"

if __name__ == '__main__':
    app.run(debug=True)