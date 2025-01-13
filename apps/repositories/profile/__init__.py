import uuid
import logging
import datetime
from typing import Dict, List, Optional, Any, Set
from apps.models import Profile
from services import UserService

log = logging.getLogger(__name__)

class ProfileRepo():
    
    def __init__(self):
        self.service = UserService()

    def get(self, id):
        try:
            return Profile.objects.get(id=id)
        except Exception as e:
            log.error(str(e))
            raise ValueError("Couldn't found profile with given id")
        

    def verify_user_by_token(self, token: str):
        try:
            
            response = self.service.get_current_user(auth_token=token).json()

            required_keys = {"id", "first_name", "last_name", "username"}
            if not required_keys.issubset(response):
                raise ValueError(f"Missing required keys in response: {required_keys - response.keys()}")
            print(response)
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
            obj, _ = Profile.objects.get_or_create(user_id=data["user_id"], email=data["email"])
            obj.first_name = data["first_name"]
            obj.last_name = data["last_name"]
            obj.username = data["username"]
            obj.save()
            return obj
        except Exception as e:
            log.error(str(e))
            raise