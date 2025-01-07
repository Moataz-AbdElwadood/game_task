from datetime import datetime
import uuid
from bson import ObjectId


def generate_uuid():
    id = uuid.uuid4()
    return str(id)



def get_remaining_time(task_data):
    """
        Calculate the remaining time of a task in seconds.
    """
    print("here20",task_data)
    finish_time = datetime.fromisoformat(task_data["completion_time"])
    remaining_time = ( finish_time - datetime.utcnow() ).seconds

    return max(0, remaining_time)




def get_user_with_email(users_collection,email):
    """Retrieve a user document by email."""


    user = users_collection.find_one({"email": email})

    if not user:
        return {"status": "error", "message": "User not found"}
    user["_id"] = str(user["_id"])  
    return {"status": "success", "user": user}



def create_user(users_collection,user_data,bcrypt):
    """Insert a new user document into the database."""
    if users_collection.find_one({"username": user_data["username"]}):
        return {"status": "error", "message": "User already exists"}
    

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(user_data["password"]).decode("utf-8")

    user_data["buildings"]=[{
        "type": "HQ",
        "level": 1
    },
    ]

    user_data["resources"] = {
        "wood": 150000,
        "stone": 150000,
        "gold": 150000,
    }
    
    user_data["password"]=hashed_password

    user_id = users_collection.insert_one(user_data).inserted_id
    return {"status": "success", "user_id": str(user_id)}



def get_user_with_id(users_collection,id):
    """Retrieve a user document by email."""
    try:

        object_id = ObjectId(id)



        user = users_collection.find_one({"_id": object_id})

        if not user:
            return {"status": "error", "message": "User not found"}
        
        user["_id"] = str(user["_id"])
        return {"status": "success", "user": user}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

   
   

