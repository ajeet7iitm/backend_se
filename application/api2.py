from flask_restful import Resource, request, abort
import requests
from flask import jsonify
from datetime import datetime
from dateutil import tz, parser
from application.models import User, Response, Ticket, FAQ, Category, Flagged_Post
from application.models import token_required, db
from application.workers import celery
from celery import chain
from application.tasks import send_email, response_notification
from datetime import datetime, timedelta
import jwt
from .config import Config
from werkzeug.exceptions import HTTPException 
from application import index

class Get_Duser(Resource):
    def post(self):
        if request.is_json:
            email = request.json["email"]
            password = request.json["password"]
        else:
            email = request.form["email"]
            password = request.form["password"]
        test = User.query.filter_by(email_id=email).first()
        # print(test)
        if (test is None):
            abort(409,message="User does not exist")
        elif (test.password == password):
            token = jwt.encode({
                'user_id': test.user_id,
                'exp': datetime.utcnow() + timedelta(minutes=80)
            }, Config.SECRET_KEY, algorithm="HS256")
            # access_token = create_access_token(identity=email)
            # print(token)
            return jsonify({"message":"Login Succeeded!", "token":token,"user_id":test.user_id,"role":test.role_id})
        else:
            abort(401, message="Bad Email or Password")
            
class Sitaram(Resource): 
       @token_required
       def get(user,self):
           x=requests.get("http://localhost:4200/u/21f1000907.json")  
           return x.json()

class Discourse_post(Resource):
    @token_required
    def get(user,self):
        data = {
            
            "title": "testing apis with ajeet and george",
            "raw": "Love encompasses a range of strong and positive emotional and mental states, from the most sublime virtue or good habit, the deepest interpersonal affection, to the simplest pleasure.[1] An example of this range of meanings is that the love of a mother differs from the love of a spouse, which differs from the love for food. Most commonly, love refers to a feeling of strong attraction and emotional attachment",
            "topic_id": 5,
            "category": 0,
           
            # Add other data parameters as needed
        }
        headers = {
            #'X-CSRF-Token': csrf_token,
            "Api_Key": "805203cb88be4b6020394bb489667f1052bc2fb93ad1d66cc836f2dbfd0c69af",
            "Api_Username": "21f1000907"
        }


        # Sending the POST request
        response = requests.post("http://localhost:4200/posts.json", json=data,headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return {"message": "POST request successful",
                    "response": response.json()}, 200
        else:
            return {"message": "POST request failed",
                    "response": response.json()}, 500


class Discourse_test1(Resource):
    @token_required
    def get(user,self):
        if(user.role_id==1):
            ticket=Ticket.query.filter_by(creator_id=user.user_id).all()
            result=[]
            for t in ticket:
                d={}
                d['ticket_id']=t.ticket_id
                d['title']=t.title
                d['description']=t.description
                d['creation_date']=str(t.creation_date)
                d['creator_id']=t.creator_id
                d['number_of_upvotes']=t.number_of_upvotes
                d['is_read']=t.is_read
                d['is_open']=t.is_open
                d['is_offensive']=t.is_offensive
                d['is_FAQ']=t.is_FAQ
                d['rating']=t.rating
                result.append(d)
            return jsonify({"data": result})
        else:
            abort(403,message="You are not authorized to view this page")
    @token_required
    def post(user,self):
        if(user.role_id==1):
            data=request.get_json()
            ticket=Ticket(title=data['title'],
                          description=data['description'],
                          creation_date=datetime.now(),
                          creator_id=user.user_id,
                          number_of_upvotes=data['number_of_upvotes'],
                          is_read=data['is_read'],
                          is_open=data['is_open'],
                          is_offensive=data['is_offensive'],
                          is_FAQ=data['is_FAQ'])
            db.session.add(ticket)
            db.session.commit()
            tk_obj = {
                'objectID': ticket.ticket_id,
                'ticket_id': ticket.ticket_id,
                'title': ticket.title,
                'description': ticket.description,
                'creation_date': ticket.creation_date,
                'creator_id': ticket.creator_id,
                'number_of_upvotes': ticket.number_of_upvotes,
                'is_read': ticket.is_read,
                'is_offensive': ticket.is_offensive,
                'is_FAQ': ticket.is_FAQ,
                'rating': ticket.rating,
                'responses': []
            }
            index.save_object(obj=tk_obj)
            return jsonify({'message':'Ticket created successfully'})
        else:
            abort(403,message="You are not authorized to view this page")
        
    @token_required
    def patch(user, self):
        if user.role_id==1:
            args = request.get_json(force = True)
            a = None
            try:
                a = int(args["ticket_id"])
                #print(a)
                #print(user.user_id)
            except:
                abort(400, message = "Please mention the ticketId field in your form")
            ticket = None
            try:
                ticket = Ticket.query.filter_by(ticket_id = a, creator_id = user.user_id).first()
            except:
                abort(404, message = "There is no such ticket by that ID")
            title = None
            try:
                title = args["title"]
                ticket.title = title
            except:
                pass
            description = None
            try:
                description = args["description"]
                ticket.description = description
            except:
                pass
            number_of_upvotes = None

            try:
                number_of_upvotes = int(args["number_of_upvotes"])
                ticket.number_of_upvotes = number_of_upvotes
            except:
                pass
            is_read = None
            try:
                if args["is_read"] is not None:
                    is_read = args["is_read"]
                    ticket.is_read = is_read
            except:
                pass
            is_open = None
            try:
                if args["is_open"] is not None:
                    is_open = args["is_open"]
                    ticket.is_open = is_open
            except:
                pass
            is_offensive = None
            try:
                if args["is_offensive"] is not None:
                    is_offensive = args["is_offensive"]
                    ticket.is_offensive = is_offensive
            except:
                pass
            is_FAQ = None
            try:
                if args["is_FAQ"] is not None:
                    is_FAQ = args["is_FAQ"]
                    ticket.is_FAQ = is_FAQ
            except:
                pass 
            try:
                rating =  args["rating"]
                ticket.rating = rating
                #print("I am here!")
            except:
                pass  
            db.session.commit()
            tk_obj = {
                'objectID': ticket.ticket_id,
                'ticket_id': ticket.ticket_id,
                'title': ticket.title,
                'description': ticket.description,
                'creation_date': ticket.creation_date,
                'creator_id': ticket.creator_id,
                'number_of_upvotes': ticket.number_of_upvotes,
                'is_read': ticket.is_read,
                'is_offensive': ticket.is_offensive,
                'is_FAQ': ticket.is_FAQ,
                'rating': ticket.rating,
                'responses': [resp.response for resp in ticket.responses]
            }
            index.partial_update_object(obj=tk_obj)
            return jsonify({"message": "Ticket updated successfully"})
        
        else:
            abort(403,message= "You are not authorized to access this!")