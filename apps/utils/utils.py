from apps.models import Follower
from django.db.models import Q

def check_mutual(profile1, profile2):
    try:
        user_follow_ids = Follower.objects.filter(follower=profile1).values_list("following_id", flat=True)
        user_follower_ids = Follower.objects.filter(following=profile1).values_list("follower_id", flat=True)

        profile_follow_ids = Follower.objects.filter(follower=profile2).values_list("following_id", flat=True)
        profile_follower_ids = Follower.objects.filter(following=profile2).values_list("follower_id", flat=True)
        all_user_related_ids = set(user_follow_ids) | set(user_follower_ids)
        all_profile_related_ids = set(profile_follow_ids) | set(profile_follower_ids)

        return bool(all_user_related_ids & all_profile_related_ids)
    except Exception as e:
        print("the error, ", str(e))