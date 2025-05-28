import uuid
import logging
import datetime
from apps.models import Profile
from services import UserService
from typing import Dict, List, Optional, Any, Set

log = logging.getLogger(__name__)

class ProfileRepo():
    
    def __init__(self, token = str):
        self.service = UserService(auth_token=token)

    def get(self, id):
        try:
            return Profile.objects.get(id=id)
        except Exception as e:
            log.error(str(e))
            raise ValueError("Couldn't found profile with given id")
        
    def profiles_by_ids(self, ids: List) -> List[Profile]:

        try:
            items = []
            profiles = self.service.get_profiles_by_ids(ids=ids)
            print(profiles)
            for profile in profiles:
                data = {
                    "first_name": profile["first_name"],
                    "last_name": profile["last_name"],
                    "email": profile["email"],
                    "user_id": profile["id"],
                    "username": profile["username"],
                    "online": False,
                    "last_seen": False,
                    "is_private": profile["is_private"],
                }
                created_profile = self.update_or_create(data=data)
                items.append(created_profile)
            return items
        except Exception as e:
            log.error(str(e))
            raise ValueError("Couldn't found profile with given id")

    def verify_user_by_token(self):
        try:
            
            response = self.service.get_current_user().json()

            required_keys = {"id", "first_name", "last_name", "username"}
            if not required_keys.issubset(response):
                raise ValueError(f"Missing required keys in response: {required_keys - response.keys()}")
            data = {
                "user_id": response["id"],
                "first_name": response["first_name"],
                "last_name": response["last_name"],
                "email": response["email"],
                "username": response["username"],
            }
            log.error(data)
            return self.update_or_create(data=data)
        except Exception as e:
            log.error(str(e))
            raise

    def update_or_create(self, data: Dict[str, str]) -> Profile:
        """
            Constructs the email data by merging the template and dynamic data.

            Args:
                data (Dict[str, str]): The type of data to create profile.
                data = {
                    "first_name": "": str,
                    "last_name": "": str,
                    "email": "": str:
                    "user_id: "": int,
                    "username: "": str,
                    "online: False: Boolean,
                    "last_seen: datatime field,
                }
            Returns:
                Dict[str, Union[str, Dict[str, str]]]: Email data ready for sending.
        """
        try:
            obj, _ = Profile.objects.get_or_create(email=data["email"])
            obj.user_id = data["user_id"]
            obj.first_name = data["first_name"]
            obj.last_name = data["last_name"]
            obj.username = data["username"]
            obj.save()
            return obj
        except Exception as e:
            log.error(str(e))
            raise