import random
import uuid
from datetime import datetime, timezone
from faker import Faker

faker = Faker()

# event types that can happen in a normal social network ish
NORMAL_EVENT_TYPES = ["follow", "unfollow", "post", "like", "comment"]

# anomaly types the simulator can generate deliberately
ANOMALY_TYPES = ["bot_farm", "follower_spike", "coordinated_cluster"]

def generate_account_id():
    # going w short readable ids, easier to spot in logs
    return f"acc_{uuid.uuid4().hex[:6]}"

def generate_account(account_id=None):
    """creates a single fake account with realistic attributes"""
    return {
        "id": account_id or generate_account_id(),
        "username": faker.user_name(),
        "follower_count": random.randint(10, 5000),
        "following_count": random.randint(10, 3000),
        "post_count": random.randint(0, 500),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    
def generate_normal_event(account_pool):
    """
    picks a random account from the pool and generates something believable that
    it might do - follow someone, post something, like a post, post something, etc
    """
    account = random.choice(account_pool)
    event_type = random.choice(NORMAL_EVENT_TYPES)
    
    # for follow/like/comment we need a target account that isnt the same as the "actor"
    target = None
    if event_type in ["follow", "unfollow", "like", "comment"]:
        others = [a for a in account_pool if a["id"] != account["id"]]
        target = random.choice(others)["id"] if others else None
        
    return {
        "account_id": account["id"],
        "event_type": event_type,
        "target_id": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
        "is_anomaly": False
    }
    
def generate_bot_farm_events(account_pool):
    """
    simulates a bot farm waking up; a bunch of accounts
    all start following the same target in a very short window
    """
    bots = random.sample(account_pool, min(15, len(account_pool)))  # pick up to 15 accounts to be bots
    target = random.choice([a for a in account_pool if a not in bots])  # pick a random target for them to follow
    
    events = []
    for bot in bots:
        events.append({
            "account_id": bot["id"],
            "event_type": "follow",
            "target_id": target["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"anomaly_type": "bot_farm"},
            "is_anomaly": True
        })
        
    return events


def generate_follower_spike_events(account_pool):
    """
    one account suddenly gets huge number of followers at a go -
    the kind of thing that happens when someone buys followers or goes viral for some reason
    """
    target = random.choice(account_pool)
    others = [a for a in account_pool if a["id"] != target["id"]]
    followers = random.sample(others, min(30, len(others)))  # up to 30 followers suddenly
    
    events = []
    for follower in followers:
        events.append({
            "account_id": follower["id"],
            "event_type": "follow",
            "target_id": target["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"anomaly_type": "follower_spike"},
            "is_anomaly": True
        })
        
    return events

def generate_coordinated_cluster_events(account_pool):
    """
    a small group of accounts starts interacting w each other
    and nobody else - coordinated inauthentic behavior
    """
    cluster = random.sample(account_pool, min(8, len(account_pool)))  # up to 8 accounts in the cluster
    cluster_ids = {a["id"] for a in cluster}
    
    events = []
    for account in cluster:
        # each account interacts w 2-3 others in the cluster
        targets = [a for a in cluster if a["id"] != account["id"]]
        for target in random.sample(targets, min(3, len(targets))):
            events.append({
                "account_id": account["id"],
                "event_type": random.choice(["follow", "like", "comment"]),
                "target_id": target["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"anomaly_type": "coordinated_cluster"},
                "is_anomaly": True
            })
            
    return events

def generate_anomalies(account_pool):
    """randomly decides to  pick and generate one of the anomaly types"""
    anomaly_type = random.choice(ANOMALY_TYPES)
    
    if anomaly_type == "bot_farm":
        return generate_bot_farm_events(account_pool)
    elif anomaly_type == "follower_spike":
        return generate_follower_spike_events(account_pool)
    elif anomaly_type == "coordinated_cluster":
        return generate_coordinated_cluster_events(account_pool)
    
    return []