from bson import ObjectId
from datetime import datetime, timedelta
import time
from app import get_user_collection
from celeryy import celery
from redis_conf.rediss import get_task_from_redis, redis_client
from utils.utils import get_user_with_id




# TODO: make the function to be invoked dynamic. Passed as key value pair in redis and call the value (which will be the desired function) to have more 
# than just one function and one behavior. ex: train_soldiers time, travel_time... etc. 

@celery.task()
def check_expired_tasks():
    """
    Periodic task to check for tasks with completion_time exceeded.
    """
    print("Checking expired tasks...")
    now = datetime.utcnow()
    expired_keys = []

    # Fetch all task keys in Redis
    all_keys = redis_client.keys('*')
    print("Fetching task keys",all_keys)
    
    hash_keys = []
    for key in all_keys:
        key_type = redis_client.type(key).decode("utf-8")
        if key_type == "hash":
            hash_keys.append(key.decode("utf-8"))

    print("hash_keys ",hash_keys)

    for key in hash_keys:
        # Fetch task data
        try:
            # decoded_key = key.decode('utf-8') #keys are coming as bytes, converting to strings
            # key_type = redis_client.type(f"celery-task-meta-{decoded_key}")
            # print("type ",key_type)

            # raw_data = redis_client.get(f"celery-task-meta-{decoded_key}")
            # print(f"Raw data for key: {raw_data}")
            exists = redis_client.exists(key)
            print(f"Key exists: {bool(exists)}")  # Should return True


            task_data = redis_client.hgetall(key)
            print(f"Task Data: {task_data}")

            # task_data = redis_client.hgetall(f"{decoded_key}")
            print("task_data",task_data)
        except Exception as e:
            print(f"Failed to decode key: {key}, Error: {e}, TASK_DATA: {task_data}")

        if b"completion_time" in task_data:
            print("hello1")
            completion_time_bytes = task_data[b"completion_time"]

            print("completion_time",completion_time_bytes)
            print("TYPE",type(completion_time_bytes))

            completion_time_str = completion_time_bytes.decode("utf-8")

            # Step 2: Convert the string to a datetime object
            completion_time = datetime.fromisoformat(completion_time_str)

            print("completion_time",completion_time)
            print("TYPE",type(completion_time))
            
            # Check if the task is expired
            if now > completion_time or now > completion_time + timedelta(seconds=33):
                expired_keys.append(key)

    print("hello2",expired_keys)
    # Process expired tasks
    for task_id in expired_keys:
        print("HEY")
        process_expired_task(task_id)


def process_expired_task(task_id):
    """
    Handle logic for an expired task.
    """
    print(f"Processing expired task: {task_id}")
    task_data = get_task_from_redis(task_id)
    print("Processing task",task_data)

    user_id = task_data["user_id"]
    # update the building info in the user document
    user_collection = get_user_collection()
    user_response=get_user_with_id(user_collection,user_id)
    if user_response["status"] == "error":
        print(f"Error getting the user associated with the task: {task_id}")
        return
    
    user = user_response["user"]
    print("User before Update",user)

    # Update the user's building information
    building_type = task_data["building"]
    target_level = int(task_data["target_level"])
    print('target level',target_level)
    for building in user["buildings"]:
        print("INSIDE FOR ", building)
        if building["type"] == building_type:
            print("INSIDE if",building["type"])
            building["level"] = target_level  # Update building level
            building_found=True
            break

    if not building_found:
        # Add new building with level 1
        user["buildings"].append({"type": building_type, "level": 1})

    print("HERE3 after update",user)
    # delete the task from Redis
    redis_client.delete(task_id)

    # Save updated user data back to MongoDB
    result = user_collection.update_one(
        {"_id": ObjectId(user["_id"])},  # Match user by their unique ID
        {"$set": {"buildings": user["buildings"]}}  # Update buildings field
    )

    print("HERE4",result)

    if result.modified_count > 0:
        print(f"Successfully updated user {user_id}'s buildings for task {task_id}.")
    else:
        print(f"No changes made for user {user_id}.")

