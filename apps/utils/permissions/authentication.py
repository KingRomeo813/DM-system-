import logging
import requests
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed


from apps.repositories import ProfileRepo
log = logging.getLogger(__file__)
class CustomAuthenticated(BasePermission):
    def authenticate(self, request):
        try:
            token = request.headers.get("Authorization")
            if not token:
                return None
            repo = ProfileRepo(token=token)
            token = token.split(" ")[1] if "Bearer" in token else token
            profile = repo.verify_user_by_token()

            if profile:
                    return profile, token
            else:
                raise AuthenticationFailed("Invalid token or authentication failed.")
        except Exception as e:
            log.error(str(e))
            
    def has_permission(self, request, view):
        try:
            token = request.headers.get("Authorization")
            if not token:
                return False
            repo = ProfileRepo(token=token)
            token = token.split(" ")[1] if "Bearer" in token else token
            profile = repo.verify_user_by_token()

            if profile:
                request.user = profile
                request.token = token
                return True
            return False
        except Exception as e:
            log.error(str(e))

class CustomAuthenticated(BasePermission):
    def authenticate(self, request):
        try:
            token = request.headers.get("Authorization")
            if not token:
                return None
            repo = ProfileRepo(token=token)
            token = token.split(" ")[1] if "Bearer" in token else token
            profile = repo.verify_user_by_token()

            if profile:
                    return profile, token
            else:
                raise AuthenticationFailed("Invalid token or authentication failed.")
        except Exception as e:
            log.error(str(e))