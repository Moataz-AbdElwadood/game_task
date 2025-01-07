from datetime import datetime, timedelta
import uuid
from redis_conf.rediss import add_task_to_redis,redis_client
from base.stubs import BuildingType
from utils.utils import generate_uuid



class Headquarters(BuildingType):
    def requirements_for_level(self, level: int) -> dict:
        requirements =  {"resources": {"wood": level*100, "stone": level*100}, "hq_level": level-1}
        return requirements

    def build_or_upgrade(self, user, level: int):
        # Check requirements
        req = self.requirements_for_level(level)
        if not req:
            # TODO: is exception raised in the websocket or i need to check in the result and return it.
            raise ValueError(f"No requirements found for level {level}")

        # Check HQ level prerequisite
        hq = next((b for b in user["buildings"] if b["type"] == "HQ"), None)
        if not hq or hq["level"] < req["hq_level"]:
            raise ValueError(f"HQ must be at level {req['hq_level']} to upgrade to level {level}")

        # Check resources
        for resource, amount in req["resources"].items():
            if user["resources"].get(resource, 0) < amount:
                raise ValueError(f"Not enough {resource} to upgrade")

        # Deduct resources and upgrade building
        for resource, amount in req["resources"].items():
            user["resources"][resource] -= amount
        hq["level"] = level



        adjusted_build_time = self.get_building_time(level)

        completion_time = datetime.utcnow() + timedelta(seconds=adjusted_build_time)
        print("here1", completion_time)

        # Queue the task and get its task_id
        print("here2")

        redis_task_id = generate_uuid()

        # add_task_to_redis(task_id, completion_time, building_type,level):
        add_task_to_redis(str(user["_id"]),redis_task_id, completion_time,"HQ",level)
        if redis_client.exists(redis_task_id):
            print(f"Task {redis_task_id} successfully added to Redis.")
        else:
            print(f"Failed to store task {redis_task_id} in Redis.")

        print("here3", completion_time)

        return f"Upgrading HQ to level:{level}, task ID: {redis_task_id} , build_time: {adjusted_build_time} seconds"
    
    def get_building_time(self, level) -> int:
        return level * 60 






class Farm(BuildingType):
    def requirements_for_level(self, level: int) -> dict:
            return {"resources": {"wood": level * 100, "stone": level * 50}, "hq_level": level - 1}


    def build_or_upgrade(self, user, level: int):
        print("building2")
        # Check requirements
        req = self.requirements_for_level(level)

        if not req:
            raise ValueError(f"No requirements found for level {level}")

        # Check farm level prerequisite
        hq = next((b for b in user["buildings"] if b["type"] == "HQ"), None)
        if not hq or hq["level"] < req["hq_level"]:
            raise ValueError(f"HQ must be at level {req['hq_level']} to upgrade to level {level}")

        # Check resources
        for resource, amount in req["resources"].items():
            if user["resources"].get(resource, 0) < amount:
                raise ValueError(f"Not enough {resource} to upgrade")

        # Deduct resources and upgrade building
        for resource, amount in req["resources"].items():
            user["resources"][resource] -= amount
        hq["level"] = level
    

        adjusted_build_time = self.get_building_time( level)

        completion_time = datetime.utcnow() + timedelta(seconds=adjusted_build_time)

        print("Building1")
        redis_task_id = uuid.uuid4()
        add_task_to_redis(str(user["_id"]),redis_task_id,completion_time,"Farm",level)
        if redis_client.exists(redis_task_id):
            print(f"Task {redis_task_id} successfully added to Redis.")
        else:
            print(f"Failed to store task {redis_task_id} in Redis.")
        return f"Building in progress task ID: {redis_task_id}"

    def get_building_time(self, level) -> int:
        return level * 40 
    
