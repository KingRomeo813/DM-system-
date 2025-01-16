
import requests
import uuid 
import logging
from django.conf import settings
from typing import List, Optional, Set, Any, Dict

log = logging.getLogger(__name__)

base_url = settings.BASE_URL
class UserService:

    def __init__(self, auth_token: str):
        self.headers = {
            "Authorization": f"Bearer {auth_token}"
        }

    def get_user(self, user_id: uuid):
        try:
            data = {
                    "email": "admin@admin.com",
                    "password": "admin"
                }
            response = requests.post(f"{self.base_url}/core/login/", data, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to fetch user {user_id}: {e}")
            raise

    def get_profiles_by_ids(self, ids: List[int]) -> List[Dict[str, str]]:
        try:
            endpoint = "/api/user/get-profiles/"
            data = {
                    "profile_ids": ids
                }
            print(data)
            url = base_url + endpoint
            response = requests.post(url, headers=self.headers, json=data)
            return response.json()
        except Exception as e:
            log.error(str(e))
            raise
        
    def get_current_user(self) -> requests.Response:
        try:
            endpoint = "/api/user/current-profile/"
            url = base_url + endpoint
            response = requests.get(url, headers=self.headers)
            return response
        
        except Exception as e:
            log.error(str(e))
            raise

    def get_all_users(self):
        try:
            endpoint = "/api/user/getallusers/"
            url = base_url + endpoint 
            print(url)
            response = requests.get(url, headers=self.headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to fetch all users: {e}")
            raise
