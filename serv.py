import os
import time
import redis
from flask import *
from werkzeug.utils import secure_filename
from PIL import Image

# объявляем все необходимое для работы сервера
app = Flask(__name__)
allowed_ext = set(['png', 'jpg'])
app.config['UPLOAD_FOLDER'] = './pictures'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
allowed_size = [str(i) for i in range(1, 10000)]
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)  # подключаемся к бд
headwidth = [25, 18, 6, 24, 9, 5, 6]
headdata = ['DATE', 'ACTIVITY TYPE', 'REQ ID', 'FILE NAME', 'REQ IP', 'WIDTH', 'HEIGHT']
# файл для логирования
try:
    f = open("log.txt", "x")
    for i in range(len(headdata)):
        f.write(headdata[i] + ' ' * (headwidth[i] - len(headdata[i])) + ' |')
    f.write('\n')
    f.close()
except:
    pass


# логгирование
def logging(*msg):
    f = open('log.txt', "a")
    for i in range(len(msg)):
        f.write(str(msg[i]) + " "*(headwidth[i]-len(str(msg[i]))) + ' |')
    f.write('\n')
    f.close()


# проверка на расширение
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


# формирование запроса на изменение изображения, добавление информации в бд
def answer(file, r_w, r_h, id):
    filename = secure_filename(file.filename)
    logging(time.ctime(), 'CLIENT UPLOAD', str(id), filename, request.remote_addr, r_w, r_h)
    r.hset(f"request:{id}", "orgn_pic", filename)
    r.hset(f"request:{id}", "req_ip", request.remote_addr)
    r.hset(f"request:{id}", "req_width", r_w)
    r.hset(f"request:{id}", "req_height", r_h)
    r.hset(f"request:{id}", "status", "in queue")
    yield f"Request id - {id}<br>Check it on /results page"
    pic_processing(file, r_w, r_h, id, filename)


# процес изменения изображения
def pic_processing(file, r_w, r_h, id, filename):
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    r.hset(f"request:{id}", "status", "processing")
    img = Image.open('./pictures/' + filename)
    img = img.resize((r_w, r_h))
    img.save(f"./results/{filename}")
    r.hset(f"request:{id}", "status", "done")
    logging(time.ctime(), "DONE", str(id), filename, '-', r_w, r_h)


# страница принимающая всю информацию
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if not(request.values["width"] in allowed_size and request.values["height"] in allowed_size):
            return "Bad size"
        else:
            r_h = int(request.values["height"])
            r_w = int(request.values["width"])
        if file and allowed_file(file.filename):
            id = int(r.get("id"))
            r.incr("id")
            return Response(stream_with_context(answer(file, r_w, r_h, id)))
        else:
            return 'No selected or wrong file'
    return """
    <!doctype html>
    <h1>Change pic resolution</h1>
    <form action="" method=post enctype=multipart/form-data>
      Размер: <input type=number min=1 max=9999 name=width>Х
      <input type=number min=1 max=9999 name=height>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    """


# страница отdечающая о готовности
@app.route("/results/", methods=['GET', 'POST'])
def results():
    if request.method == 'POST' and request.values["id"] != '':
        try:
            id = int(request.values["id"])
        except ValueError:
            return "Send integer please"
        if r.hget(f"request:{id}", "status") == "done":
            filename = r.hget(f"request:{id}", "orgn_pic")
            logging(time.ctime(), "CLIENT DOWNLOAD", str(id),  filename, request.remote_addr)
            return send_from_directory("./results", filename)
        elif r.hget(f"request:{id}", "status") == "processing":
            logging(time.ctime(), "CLIENT WAITING FOR",  str(id), '-', request.remote_addr)
            return "Your picture is stil in process"
        logging(time.ctime(), "CLIENT WRONG WITH",  str(id), '-', request.remote_addr)
        return "Wrong id!"
    return """
    <!doctype html>
    <h1>Get pic by id</h1>
    <form action="" method=post enctype=multipart/form-data>
      <input type=number name=id>
      <input type=submit value=Submit>
    </form>
    """
 