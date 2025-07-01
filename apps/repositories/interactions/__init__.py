import requests
import uuid 
import logging
from django.conf import settings
from typing import List, Optional, Set, Any, Dict

log = logging.getLogger(__name__)

base_url = settings.BASE_URL

class InteractionService:

    def __init__(self, auth_token: str):
        self.headers = {
            "Authorization": f"Bearer {auth_token}"
        }

    def get_follow_request_status(self, ids: List[int]) -> List[Dict[str, str]]:
        if len(ids) != 2:
            raise ValueError("Exactly two profile IDs must be provided.")

        try:
            endpoint = f"{base_url}/api/interaction/get-follow-request-status"
            params = {"ids": ",".join(str(i) for i in ids)}
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to fetch follow request status for {ids}: {e}")
            raise
