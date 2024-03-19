from application import app
from flask import request, jsonify, render_template, redirect
from .models import *
from flask_restful import Resource, request, abort
from datetime import datetime, timedelta
from flask_restful import Resource, request, abort
from flask import jsonify
from datetime import datetime
from dateutil import tz, parser
from application.models import User, Response, Ticket, FAQ, Category, Flagged_Post
from application.models import  db
from application.workers import celery
from celery import chain
from application.tasks import send_email, response_notification
from datetime import datetime, timedelta
import jwt
from .config import Config
from werkzeug.exceptions import HTTPException 
from application import index

local_token=""
@app.route("/")
def home():
    print(local_token)
    return 'hi'

@app.route("/sitaram", methods=["GET", "POST"])
def home_ram():      
    return render_template("login.html")

@app.route("/signin", methods=["GET", "POST"])
def post1():
    email = request.form["email"]
    password = request.form["password"]
    test = User.query.filter_by(email_id=email).first()
    # print(test)
    if (test is None):
        abort(409,message="User does not exist")
    elif (test.password == password):
        token = jwt.encode({
            'user_id': test.user_id,
            'exp': datetime.utcnow() + timedelta(minutes=300)
        }, Config.SECRET_KEY, algorithm="HS256")
        # access_token = create_access_token(identity=email)
        # print(token)
        global local_token
        local_token=token
        print(local_token)
        return jsonify({"message":"Login Succeeded!", "token":token,"user_id":test.user_id,"role":test.role_id})
    else:
        abort(401, message="Bad Email or Password")

def token_required(function):
	@functools.wraps(function)
	def loggedin(*args,**kwargs):
		auth_token=None
		# try:
		# 	auth_token = request.headers['secret_authtoken']
		
		# except:
		# 	return jsonify({"status":'unsuccessful, missing the authtoken'})
		auth_token =local_token
		try: 
			output = jwt.decode(auth_token,Config.SECRET_KEY,algorithms=["HS256"])
			#print(output)
			user = User.query.filter_by(user_id = output["user_id"]).first()
		except:
			return jsonify({"status":"failure, your token details do not match"})
		
		return function(user,*args,**kwargs)
	return loggedin

@app.route("/users", methods=["GET"])
@token_required
def get_users(current_user):
    print(current_user)
    users = User.query.all()
    results = [
        {
            "user_id": user.user_id,
            "user_name": user.user_name,
            #"name": user.name,
            "email_id": user.email_id,
            "role_id": user.role_id
        } for user in users]

    return jsonify(results)

# from application.workers import celery
# from application.tasks import send_email
# @app.route("/email", methods=["POST"])
# def post_email():
#     html = request.get_json()['html']
#     email = request.get_json()['email']
#     subject = request.get_json()['subject']
#     send_email.s(eid=email, html=html, subject=subject).apply_async()
#     return jsonify({'message': 'success'})

# from application.workers import celery
# from application.tasks import unanswered_ticket_notification
# @app.route("/notification")
# def get_notif():
#     unanswered_ticket_notification.s().apply_async()
#     return "OK"