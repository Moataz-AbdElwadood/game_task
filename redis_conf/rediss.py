from datetime import datetime, timedelta
import redis


redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

def add_task_to_redis(user_id,task_id, completion_time, building_type,level):
    """
    Add a task to Redis with a specified completion time.
    """
    #TODO check if the same task already exists


    redis_client.hset(
        task_id,
        mapping={
            "completion_time": completion_time.isoformat(),
            "building": building_type,
            "target_level": level,
            "user_id": user_id
        },
    )
    redis_client.expire(task_id, int((completion_time - datetime.utcnow()).total_seconds())+120)

def get_task_from_redis(task_id):
    # redis_client.flushdb() #clean up redis 
    print("++++++++++ ",task_id)
    task_data = redis_client.hgetall(f"{task_id}")
    if not task_data:
        return None

    # Decode byte strings into a Python dictionary
    task_dict = {key.decode('utf-8'): value.decode('utf-8') for key, value in task_data.items()}
    return task_dict

def delete_redis_task(task_id):
    redis_client.delete(task_id)
    return


def get_all_tasks():
    """
    Retrieve all tasks stored in Redis.

    Args:
        redis_client: The Redis client instance.

    Returns:
        list: A list of dictionaries representing the tasks.
    """
    tasks = []
    for key in redis_client.scan_iter():  # Scan all keys in Redis
        try:
            # Retrieve task data
            task_data = redis_client.hgetall(key)

            # Decode the task data (binary to string) and convert to a dictionary
            task = {k.decode('utf-8'): v.decode('utf-8') for k, v in task_data.items()}
            task['id'] = key.decode('utf-8')  # Add the task ID to the task data
            tasks.append(task)
        except Exception as e:
            print(f"Error processing key {key}: {e}")

    return tasks
