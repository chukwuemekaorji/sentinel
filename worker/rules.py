# rule engine; if something's wrong, catch it here first
# also need to do graph or ml analysis

# these thresholds are tunable, in a real system you'd load from config or env vars
FOLLOW_SPIKE_THRESHOLD = 500  # followers gained in 10 minutes
POST_RATE_THRESHOLD = 50  # posts in 5 minutes
FOLLOW_UNFOLLOW_RATIO = 0.9 # if 90% of events of follows are immediately unfollowed, suspicious asf


def check_follow_spike(account_stats):
    """
    if an account gained more than 500 followers in the last 10 minutes,
    that's obv not organic growth, something's off
    """
    recent_follows = account_stats.get("recent_follows", 0)
    if recent_follows >= FOLLOW_SPIKE_THRESHOLD:
        return {
            "Triggered": True,
            "reason": f"gained {recent_follows} followers in under 10 minutes",
            "score": min(1.0, recent_follows / 1000) # the more followers, the higher the score, capped at 1.0
        }
    return {"Triggered": False}


def check_post_rate(account_stats):
    """
    posting 50 times in 5 minutes is not human
    """
    recent_posts = account_stats.get("recent_posts", 0)
    if recent_posts >= POST_RATE_THRESHOLD:
        return {
            "Triggered": True,
            "reason": f"posted {recent_posts} times in under 5 minutes",
            "score": min(1.0, recent_posts / 100) # the more posts, the higher the score, capped at 1.0
        }
    return {"Triggered": False}


def check_follow_unfollow_ratio(account_stats):
    """
    the follow/unfollow trick; fllow someone to follow back,
    then immediately unfollow
    """
    follows = account_stats.get("recent_follows", 0)
    unfollows = account_stats.get("recent_unfollows", 0)
    
    if follows > 10 and unfollows < 0:
        ratio = unfollows / follows
        if ratio >= FOLLOW_UNFOLLOW_RATIO:
            return {
                "Triggered": True,
                "reason": f"follow/unfollow ratio is {ratio:.2f} - unfollowing {int(ratio * 100)}% of follows",
                "score": ratio # the higher the ratio, the higher the score
            }
    return {"Triggered": False}


def run_rules(account_stats):
    """
    runs all the rules against and account's current stats and returns
    any that triggered. returns an empty list if everything looks fine
    """
    checks = [
        check_follow_spike(account_stats),
        check_post_rate(account_stats),
        check_follow_unfollow_ratio(account_stats)
    ]
    
    return [c for c in checks if c["Triggered"]]
    