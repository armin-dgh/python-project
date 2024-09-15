from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
import redis

application = Flask(__name__)
application.config['CACHE_TYPE'] = 'redis'
application.config['CACHE_REDIS_HOST'] = 'localhost'
application.config['CACHE_REDIS_PORT'] = 6379
application.config['CACHE_REDIS_DB'] = 0
application.config['SECRET_KEY'] = "fejqiofhqouifhq0o92283dkbefukc"

# Initialize Flask-Caching with Redis
cache = Cache(app=application)
cache.init_app(application)

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
socketio = SocketIO(application)
global users
users = redis_client.hgetall('user')
# chats = redis_client.hgetall('chats')
@application.route('/')
def index():
    if "username" in session:
        context = {
            "username": session["username"],
            'massage' : redis_client.hgetall("chats"),
        }
        return render_template("index.html", username=session["username"], massage=redis_client.hgetall("chats"))
    return redirect("login")

@application.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if username in users:
            error = 'یوزر نیم از قبل وجود دارد.'
        elif password != confirm_password:
            error = 'پسورد دوم مطابق با پسورد اول نیست'
        else:
            redis_client.hset("user", username, generate_password_hash(password))
            return redirect(url_for("login"))
        return render_template('register.html', error=error)

    return render_template("register.html")

# @app.route('/login', methods=['GET', 'POST'])
@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = redis_client.hgetall("user")
        print(users)
        # print(check_password_hash(redis_client.hget("user", username), password))
        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            print(session)
            return redirect(url_for('index'))

        error = 'پسورد یا نام کاربری اشتباه است!'
        return render_template('login.html', error=error)
    return render_template('login.html')

@application.route('/logout')
def logout():
    print(session)
    print(users)
    session.pop('username', None)
    return redirect(url_for('index'))
@socketio.on("message")
def handle_message(message):
    redis_client.hset("chats", session["username"], message)
    emit("message", {"username": session["username"], "message": message}, broadcast=True)



if __name__ == "__main__":
    application.secret_key = "fejqiofhqouifhq0o92283dkbefukc"
    socketio.run(application, debug=True)