from datetime import datetime, timedelta
from celery_conf.celeryy import  make_celery
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from pymongo import MongoClient
from buildings.concretes import Farm, Headquarters
from redis_conf.rediss import add_task_to_redis, delete_redis_task, get_task_from_redis
from utils.utils import create_user, get_remaining_time, get_user_with_email, get_user_with_id



app = Flask(__name__)
app.config['SECRET_KEY'] = 'khjk32j13j123j12312jjj4jklLJ#*#&@O@:J!*'

socketio = SocketIO(app, cors_allowed_origins="*")

make_celery(app)

# mongodb connection
client = MongoClient("mongodb://localhost:27017/")
db = client["test"]
users_collection = db["users"]

bcrypt = Bcrypt(app)
jwt = JWTManager(app)


def get_user_collection():
    return users_collection


@app.route("/")
def home():
    return "Hello..Welcome"


# users_collection.create_index("email", unique=True)


def handle_register(data):
    username=data.get("username")
    email=data.get("email")
    password=data.get("password")

    if not username:
        emit("register_response", {"status": "error", "message": "username Required."})
        return
    
    if not email:
        emit("register_response", {"status": "error", "message": "Email Required."})
        return
    
    if not password:
        emit("register_response", {"status": "error", "message": "Password Required."})

    

    # insert data to mongodb
    user_data = {
        "username": username,
        "email": email,
        "password": password
     }
    
    resp = create_user(users_collection,user_data,bcrypt)
    if resp["status"] == "success":
        emit("register_response", {"status": "success", "message": "User registered successfully", "user_id": resp["user_id"]})

    if resp["status"] == "error":
        emit("register_response", {"status": "error", "message": resp["message"]})


  

def handle_login(data):
    email= data.get("email")
    password=data.get("password")

    if not email:
        emit("login_response", {"status": "error", "message": "Email Required."})
        return

    if not password:
        emit("login_response", {"status": "error", "message": "Password Required"})

    user = get_user_with_email(users_collection,email)
    if user["status"] == "success":
        if not bcrypt.check_password_hash(user["user"]["password"] , password):
            emit("login_response", {"status": "error", "message":"Password is incorrenct"})
        
        else:
            access_token = create_access_token(identity={"email": email})

            emit("login_response", {"status": "success", "message": "Login Successful", "user_id": user["user"]["_id"],"token": access_token})
            return
    
    else:
        print("here error")
        emit("login_response", {"status": "error", "message": "Invalid email"})



   
   
   


#TODO : check if a building with the same type is already being
def handle_building(data):
    """
      Handle the create or upgrade building logic 
        data : {
            user_id: user_id    -> string   # normally a websocket session would be open and no user_id is required but here since we test with each request on its own websocket and its own file in node we need to specify the user_id 
            building_type: farm|HQ -> string
            building_level: level   -> int
        }

        return {task} -> celery task object 
    """
    print("build2")
    user_id=data["user_id"]
    building_type = data["building_type"]
    level = data["building_level"]
    

    if not user_id:
        emit("building_response", {"status": "error", "message": "User ID required."})
        return
     

    if not building_type:
        emit("building_response", {"status": "error", "message": "Building type required."})
        return
    
    if not level:
        emit("building_response", {"status": "error", "message": "Building level required."})
        return
    
    # check if user exists
    user_response = get_user_with_id(users_collection,user_id)
    print("build3")
    #TODO redo the return from get_user_with_id to make it return an object
    if user_response["status"] == "error":
        print("build4")
        emit("building_response", {"status": "error","message":user_response["message"]})
        return
    user = user_response["user"]
    if building_type == "HQ":
        building= Headquarters()
    else:
        building=Farm()
        
    requirements = building.requirements_for_level(level)
    # Extract the resource requirements
    required_resources = requirements["resources"]

    # Check if the user has enough resources
    for resource, amount in required_resources.items():
        if user["resources"].get(resource, 0) < amount:
            raise ValueError(f"Not enough {resource}. Required: {amount}, Available: {user['resources'].get(resource, 0)}")

    try:
        # Schedule building completion
        print("User ID:", str(user["_id"])  )
        result= building.build_or_upgrade(user,level)
        emit("building_response", {"status": "success", "message":result})
    except ValueError as e:
        emit("building_response", {"status": "error", "message":e})
    





def speed_up(data):
    """
        user_id : string
        task_id : task_id
        speed_up_time : float
        speed_up_type : percentage|precision

    """
    user_id=data["user_id"]
    task_id = data["task_id"]
    speed_up_time = data["speed_up_time"]
    speed_up_type = data["speed_up_type"] 
    print("speed1 ", data)

    task_data= get_task_from_redis(task_id)

    if task_data == None:
        print("NO TASK FOUND")
        emit("speed_response", {"status": "error", "message": "Task not found"})
        return
    
    remaining_time=get_remaining_time(task_data) # Remaining time in seconds 

    print("speed5")
    
    if speed_up_type == "percentage":
    # Recalculate new build time
        print("speed8")
        new_build_time = int(remaining_time * speed_up_time)
    else:
        print("speed9")
        new_build_time = int(remaining_time-speed_up_time)
        
    completion_time=datetime.utcnow() + timedelta(seconds=new_build_time)
    # Revoke current task
    print("speed10")
    delete_redis_task(task_id) #delete the task from redis

    print("speed11",task_data)

    # Queue a new task with updated time
    add_task_to_redis(user_id,task_id,completion_time,task_data["building"],task_data["target_level"]) # creating a new task in redis with the same task_ID
    print("speed12")
    emit("speed_response",{"status": "success", "message":f"new task created with remaining_time: {new_build_time}.secs and task_id: {task_id}"})

@socketio.on("speedUP")
def speedUP(data):
    speed_up(data)


@socketio.on("register")
def register(data):
    handle_register(data)

@socketio.on("login")
def login(data):
    handle_login(data)

@socketio.on("build")
def build(data):
    print("build1")
    handle_building(data)



if __name__ == "__main__":
    socketio.run(app, debug=True)



