import json
import os
import time
import random
import logging

import redis
from dotenv import load_dotenv
from generators import generate_account, generate_normal_event, generate_anomaly_events

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [simulator] %(message)s")
log = logging.getLogger(__name__)

# how many accounts to simulate, just big enough to make patterns
ACCOUNT_POOL_SIZE = 200

# roughly how many anomaly gets generated (1 in every N events
ANOMALY_FREQUENCY = 20

# how fast events get generted, in seconds
EVENT_INTERVAL_SECONDS = 0.3

def connect_redis():
    """keeps trying to connect until redis is ready, to avoid race conditions in docker startup"""
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    
    while True:
        try:
            client = redis.Redis(host=host, port=port, decode_responses=True)
            client.ping()
            log.info(f"connected to Redis at {host}:{port}")
            return client
        except redis.ConnectionError:
            log.warning("redis not ready yet, retrying in 2 seconds...")
            time.sleep(2)
            
def push_event(r, event):
    """pushes a single event to the redis queue as a json string"""
    r.rpush("events_queue", json.dumps(event))
    
def main():
    r = connect_redis()
    
    # build the account pool upfront, the accounts that we'll simulate events for
    log.info(f"generating {ACCOUNT_POOL_SIZE} fake accounts...")
    account_pool = [generate_account() for _ in range(ACCOUNT_POOL_SIZE)]
    
    # push all accounts into redis so the worker can register them in postgres
    for account in account_pool:
        r.rpush("accounts_queue", json.dumps(account))
        
    log.info("account pool ready, starting event loop...")
    
    batch_count = 0
    
    while True:
        # generate a a small batch of normal events each iteration
        batch_size = random.randint(5, 8) 
        for _ in range(batch_size):
            event = generate_normal_event(account_pool)
            push_event(r, event)
            
        batch_count += 1
        
        # every ANOMALY_FREQUENCY batches, generate some anomalies
        if batch_count % ANOMALY_FREQUENCY == 0:
            anomaly_events = generate_anomaly_events(account_pool)
            for event in anomaly_events:
                push_event(r, event)
            log.info(f"generated anomaly: {anomaly_events[0]['metadata'].get('anomaly_type')} ({len(anomaly_events)} events)")
            
        time.sleep(EVENT_INTERVAL_SECONDS)
        
if __name__ == "__main__":
    main()