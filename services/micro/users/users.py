
import requests
import uuid 
import logging
from django.conf import settings
log = logging.getLogger(__name__)

base_url = settings.BASE_URL
class UserService:
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
        
    def get_current_user(self, auth_token: str) -> requests.Response:
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}"
            }
            endpoint = "/api/user/current-profile/"
            url = base_url + endpoint
            response = requests.get(url, headers=headers)
            return response
        
        except Exception as e:
            log.error(str(e))
            raise

    def get_all_users(self, auth_token):
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}"
            }
            endpoint = "/api/user/getallusers/"
            url = base_url + endpoint 
            print(url)
            response = requests.get(url, headers=headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to fetch all users: {e}")
            raise
