from flask import Flask, render_template, request, url_for, redirect
from sawo import createTemplate, verifyToken
import json
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
import os
import json
import requests
from replit import db

load_dotenv()
API_KEY = os.environ['API_KEY']

UPLOAD_FOLDER = 'static/uploads/'
app = Flask(__name__, static_url_path='/')
createTemplate("templates/partials", flask=True)

load = ''
loaded = 0

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
my_secret = os.environ['API_KEY']

def demo_cal(num):
    if int(num)==1:
        data_load = "testdata2burger.json"
    else:
        data_load= "testdata.json"
    with open(data_load, "r") as f:
        data = json.load(f)
    return data

def get_cal(fname):
      img = f"static/uploads/{fname}"
      sec =  os.environ['secret']
      headers = {'Authorization': 'Bearer ' + sec}
      url = 'https://api.logmeal.es/v2/recognition/complete'
      resp = requests.post(url,files={'image': open(img, 'rb')},headers=headers)
      print(resp.json())
      url = 'https://api.logmeal.es/v2/recipe/nutritionalInfo'
      resp = requests.post(url,json={'imageId': resp.json()['imageId']}, headers=headers)
      print(resp.json())
      return resp.json() 


@app.route("/demo/<num>")
def demo(num):
    data = demo_cal(num)
    fname = "samplefood.jpg"
    if int(num)==1:
        fname = "demo1.jpg"
    else:
        fname = "demo2.jpg"
    #print(num)
    return render_template("demo.html",fname=fname, data=data)

@app.route('/result', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      global load
      f = request.files['file']
      fname = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
      data = get_cal(fname)
      if data=="Error":
          return "Something went wrong!"
      an_object = data["foodName"]
      check_list = isinstance(an_object, list)
      if check_list==True:
          data["foodName"] = data["foodName"][0]
      if load:
        if load["identifier"] in db.keys():
          data1 = db[load["identifier"]]
          data1.append([data, fname])
          db[load["identifier"]] = data1
        else:
          db[load["identifier"]] = []
      return render_template("result.html",fname=fname, data=data)

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

def setPayload(payload):
    global load
    load = payload


def setLoaded(reset=False):
    global loaded
    if reset:
        loaded = 0
    else:
        loaded += 1


@app.route("/")
def index():
    global load
    if load:
      loaded=True
    else:
      loaded=False

    return render_template("index.html", loaded=loaded)

@app.route("/history")
def history():
    global load
    if load:
      dbase = db[load["identifier"]]
      print("this is exec")
      print(dbase)

      return render_template("history.html", dbase=dbase)
    return redirect("/")

@app.route("/logout")
def logout():
    global load
    load=""
    return redirect("/")

@app.route("/login_page")
def login_page():
    setLoaded()
    setPayload(load if loaded < 2 else '')
    sawo = {
        "auth_key": API_KEY,
        "to": "login",
        "identifier": "email"
    }
    return render_template("login.html", sawo=sawo, load=load)


@app.route("/login", methods=["POST", "GET"])
def login():
    payload = json.loads(request.data)["payload"]
    setLoaded(True)
    setPayload(payload)
    status = 200 if(verifyToken(payload)) else 404
    return {"status": status}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
