from flask import Flask, make_response, redirect, render_template, request, jsonify, url_for
from flask_jwt_extended import create_access_token, get_jwt, set_access_cookies, unset_jwt_cookies, get_jwt_identity, jwt_required, JWTManager, verify_jwt_in_request
import os
import secrets

from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from forms.loginForm import LoginForm
from forms.newAccountForm import NewAccountForm
from forms.postForm import PostForm
from forms.profileForm import ProfileForm
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models.User import Post, User, db

from flask_bootstrap import Bootstrap5
import logging

logging.basicConfig(
    # Comment out file, use stdout/systemd instead
    # filename='/var/log/challengeGrader/gradingCheck.log', 
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
# Using the secret does not work with multiple workers (if different worker processes request, get mismatching vals)
# Should put this in a config file, but this is sufficient. Change in yours
app.secret_key = "UYfJxNfKbqGcmmn5lwQC1Q" #secrets.token_urlsafe(16)

def getTopoValue(name, default = "11deadbeef313373"):
    val = os.environ.get(name, "").strip()
    if val == "":
        logging.warning(f"USING DEFAULT VALUE for {name}!!!")
        return str(default)
    return str(val)


access_code = "6729304764889247"

logging.info(f"API Access code: {access_code}")

db_name = 'socialmedia.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

# Give tim the token
with app.app_context():
    logging.info("Set token in database for targettim")
    tim = User.query.filter_by(username="targettim").first()
    tim.password = getTopoValue("tokenSQL")
    db.session.add(tim)
    db.session.commit()

bootstrap = Bootstrap5(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Set up JWT manager
# Replace with a strong secret key
app.config["JWT_SECRET_KEY"] = getTopoValue("jwtSecret", "8159345abcedef37") 
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # jwt-form does this for us already
jwt = JWTManager(app)

# Used to set up a fake error message that leaks code segments
# Wanted to use Flask's Debug mode to leak it, but that's too much power.
jwtErrorLeak = """...
# Set up JWT manager
# Replace with a strong secret key
# TODO: Fix. Under crunch to get Premium working... 
app.config["JWT_SECRET_KEY"] = "{value}"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
jwt = JWTManager(app)
...
""".format(value=app.config["JWT_SECRET_KEY"])

@jwt.invalid_token_loader
def my_invalid_token_callback(jwt_error_string):
    jwt_error_string = "Line 15, JWT: " + jwt_error_string.lower()
    return render_template("error_cookie.html", code_snippet=jwtErrorLeak, error=jwt_error_string, line=8), 500

@jwt.token_verification_loader
@jwt.unauthorized_loader
def my_valid_token_callback(headers, data):    
    if data.get("isPremium", False):
        logging.info(f"{current_user.username} has a premium cookie")
        current_user.userIsPremium = True
    else:
        current_user.userIsPremium = False
    # if verify_jwt_in_request(optional=True, locations = ['cookies']):
    #     jwt_premium = get_jwt() 
    #     if jwt_premium.get("isPremium", False):
    #         self.userIsPremium = True   
    return True

@app.route("/home", methods=["GET"])
@login_required
@jwt_required()
def home():      
    return render_template("home.html", user=current_user, posts=Post.query.filter(Post.draft != 1), active_page="Home", tokenJWT=getTopoValue("tokenJWT"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = NewAccountForm()
    if form.validate_on_submit():
        # Check unique user. 
        user = User.query.filter_by(username=request.form.get("username")).first()

        if user:
            form.username.errors.append('That username is already on Finsta!')
        else:
            new_user = User(username=request.form.get("username"), password=request.form.get("password"))

            # add the new user to the database
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.  
        if request.form.get("username").lower() in ["finsta", "sillysara", "prettypenny", "gregariousgreg", "targettim"]:
            form.username.errors.append('No logins to that account! Find another way...')
        else:
            user = User.query.filter_by(username=request.form.get("username"), password=request.form.get("password")).first()

            if not user:
                form.username.errors.append('')  # So it turns red as well
                form.password.errors.append('Please check your login details and try again.')
            else:
                # user should be an instance of your `User` class
                login_user(user, remember=True)
                
                #JWT token for the related task
                access_token = create_access_token(identity=user.username, additional_claims={"isPremium": False}, expires_delta=False)

                # Create a response object
                response = make_response(redirect('/home'))
                
                set_access_cookies(response, access_token)

                return response
    return render_template('login.html', form=form)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    response = make_response(redirect('/'))
    unset_jwt_cookies(response)
    logout_user()
    return response

@app.route("/profile", methods=["GET"])
@login_required 
@jwt_required()
def my_profile():
    return render_template("profile.html", user=current_user)

@app.route("/profile/<string:user>", methods=["GET"])  # Login not required to view someone else's profile; this is mainly to avoid any complications during the XSS
def profile(user=""):    
    targetUser = User.query.filter_by(username=user).first()
    if targetUser:
        return render_template("profile.html", user=targetUser)
    return redirect(url_for('home'))

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required 
@jwt_required()
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.add(current_user)
        db.session.commit()
        return redirect('/profile')
    return render_template("edit_profile.html", user=current_user, form=form)

@app.route("/post", methods=["GET", "POST"])
@login_required 
@jwt_required()
def post():
    form = PostForm(obj=current_user)
    if form.validate_on_submit():
        p = Post()
        form.populate_obj(p)
        p.username = current_user.username
        db.session.add(p)
        db.session.commit()
        return redirect('/profile')

    return render_template("edit_post.html", user=current_user, form=form)

@app.route("/search", methods=["GET"])
def search():
    key = request.args.get("apiKey", "") 
    if len(key) != len(access_code):
        return jsonify({"status":"ERROR", "data":[], "message":"Invalid apiKey - wrong length"}), 400
    if key != access_code:
        return jsonify({"status":"ERROR", "data":[], "message":"Invalid apiKey - authorization failed"}), 400
    posts = Post.query.all()

    archive = request.args.get("archive", None)
    if archive is not None and archive.lower() not in ["true", "false"]:
        return jsonify({"status":"ERROR", "data":[], "message":"Parameter `archive` must be true/false"}), 400

    check = ["archive", "author", "apiKey", "tag", "text", "title"]

    for x in request.args.keys():
        if x not in check:
            return jsonify({"status":"ERROR", "data":[], "message":f"Unknown parameter"}), 400

    if archive is not None and archive.lower() == "true" :
        t = getTopoValue("tokenAPI")
        posts.append(Post(username="finsta", title=t, text=t, tags=""))

    rm = []
    # Run the API filters -- Acts like a LIKE "%x%" in SQL
    # Doing it this way instead of SQL because I needed to cheat and add the flag
    for post in posts:    
        if request.args.get("tag", "").lower() not in post.tags.lower():
            rm.append(post)
            continue
        if request.args.get("text", "").lower() not in post.text.lower():
            rm.append(post)
            continue
        if request.args.get("author", "").lower() not in post.username.lower():
            rm.append(post)
            continue
        if request.args.get("title", "").lower() not in post.title.lower():
            rm.append(post)
            continue
    posts = [x for x in posts if x not in rm]

    x = {"status":"Success", "data":list(posts), "message":"Success"}

    return jsonify(x), 200

@app.route("/user", methods=["GET"])
def user_search():
    if request.args.get("username", None) is None:
        return redirect(url_for("home"))

    # This is weird, but kinda neat
    try:
        query = "SELECT username FROM Users WHERE username LIKE '%" + request.args.get("username", "") + "%';"
        with db.engine.connect() as conn:
            result = conn.execute(text(query))
            return profile(result.fetchall()[0][0])
    except OperationalError as e:
        x = '''...
with db.engine.connect() as conn:
    result = conn.execute(text(query))
    return profile(result.fetchall()[0][0])
...'''
        return render_template("error_cookie.html", code_snippet=x, error=e, line=245), 500
    except IndexError as e:
        return redirect(url_for("home")) 

@app.route("/")
def hello_world():
    return render_template("index.html")
