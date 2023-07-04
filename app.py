from flask import Flask,render_template,request,flash,redirect,session
from flask_bcrypt import Bcrypt
from flask_login import login_user,LoginManager,login_required,logout_user
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime,timedelta
from dotenv import load_dotenv
from flask_toastr import Toastr
from users import User
from static.forms.contact import is_valid,send_email

def connection_result(client):
    try:
        client.admin.command('ping')
        return True
    except  Exception as e :
        return e
    
def check_password(user,given,remember,source):
    if bcrypt.check_password_hash(user['password'],given):
        global current_user
        user_object = User(user)
        current_user = user_object
        login_user(user_object,remember=remember)
        flash({'title': "Success", 'message': "Login Successfull"}, 'success')
        return redirect('/')
    else:
        flash({'title': "Error", 'message': "Invalid Password !"}, 'error')
        return render_template('extra/login.html',value=user[f'{source}'])

load_dotenv()
uri = os.environ.get("DATABASE_URL")
client = MongoClient(uri, server_api=ServerApi('1'))
auth_db = client.get_database('Auth').get_collection('users')
contact_db = client.get_database("Contact").get_collection("users")
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"
bcrypt = Bcrypt()

@login_manager.user_loader
def load_user(user_id):
    global current_user
    user_id = current_user
    return user_id

App = Flask(__name__)
App.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
login_manager.init_app(App)
bcrypt.init_app(App)
toastr = Toastr(app=App)

@App.route("/")
def home():
    return render_template("main/index.html")

@App.before_request
def session_handler():
    session.permanent = True
    App.permanent_session_lifetime = timedelta(minutes=1)

@App.route("/Login",methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("/extra/login.html",value=None)
    elif request.method=="POST":
        username = request.form['username']
        password = request.form['password']
        try:
            remember = request.form['remember']
        except:
            remember = False
        user_with_name , user_with_email = auth_db.find_one(filter={'username' : f'{username}'}) , auth_db.find_one(filter={'email' : f'{username}'})    
        if user_with_name!=None and user_with_email==None:
            return check_password(user_with_name,password,remember=remember,source='username')
        elif user_with_name==None and user_with_email!=None:
            return check_password(user_with_email,password,remember=remember,source='email')
        else:
            flash({'title': "Error", 'message': "Invalid Username or Email !",'options':{'TOASTR_POSITION_CLASS':'toast-top-center'}}, 'error')
            return render_template('extra/login.html',value=username)
    else: return None

@App.route("/Register",methods=["GET","POST"])
def register():
    if request.method=="GET":
        return render_template("/extra/register.html",value=None)
    elif request.method=="POST":
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        if auth_db.find_one(filter={'email' : f'{email}'}) == None:
            if auth_db.find_one(filter={'username' : f'{username}'}) == None:
                auth_db.insert_one({'name' : f'{name}' , 'email' : f'{email}' , 'username' : f'{username}' , 'password' : f'{password}'})
                flash({'title': "Success", 'message': "Registered Successfully!"}, 'success')
                return render_template('extra/login.html',value=username)
            else:
                flash({'title': "Warning", 'message': "Username Already Exists !",}, 'warning')
                return render_template('extra/register.html',value={'name' : f'{name}' , 'email' : f'{email}' , 'username' : f'{username}'})
        else:
            flash({'title': "Warning", 'message': "Email Already Exists !"}, 'warning')
            return render_template('extra/register.html',value={'name' : f'{name}' , 'email' : f'{email}' , 'username' : f'{username}'})
    else: return None

@App.route("/DA-1")
@App.route("/DA-2")
@App.route("/DA-3")
@App.route("/ML-1")
@App.route("/ML-2")
@App.route("/ML-3")
@App.route("/DL-1")
@App.route("/DL-2")
@App.route("/DL-3")
def project_dis():
    re = str(request.url_rule)
    if re in ["/DA-1","/DA-2","/DA-3"]:
        return render_template("portfolio/portfolio-DA.html",value = re)
    elif re in ["/ML-1","/ML-2","/ML-3"]:
        return render_template("portfolio/portfolio-ML.html",value = re)
    elif re in ["/DL-1","/DL-2","/DL-3"]:
        return render_template("portfolio/portfolio-DL.html",value = re)
    else:
        return None

@App.route("/Contact",methods=["GET","POST"])
def contact():
    if request.method=="POST":
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        if contact_db.find_one(filter={'email' : f'{email}'}) == None:          
            if is_valid(email):
                contact_db.insert_one( {'date_time' : f'{datetime.now()}' , 'name' : f'{name}' , 'email' : f'{email}' , 'subject' : f'{subject}' , 'message' : f'{message}' } )
                send_email(name,email,subject,message,other=True)
                flash({'title': "Success", 'message': "Message Sent Successfully !"}, 'success')
            else:                
                flash({'title': "Error", 'message': "Please Provide A Working Email !"}, 'error')
            return redirect('/')
        else:
            flash({'title': "Information", 'message': "Message Already Sent Please Wait For Support !"}, 'info')
            return redirect('/')
    else:
        return False

@App.route("/dashboard")
@login_required
def user_about(userid):
    user = auth_db.find_one(filter={'_id' : f'{userid}'})
    return f"Name = {user['name']}<br>Email = {user['email']}<br>Username = {user['username']}"

@App.route("/Logout")
@login_required
def logout():
    logout_user()
    flash({'title': "Success", 'message': "Logged Out Successfully !"}, 'success')
    return redirect('Login')

if __name__ == "__main__":
    if connection_result(client) == True :
        App.run(debug=True)
    else :
        print(connection_result(client))