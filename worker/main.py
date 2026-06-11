import json
import os
import time
import logging
import threading
from datetime import datetime, timezone, timedelta

import redis
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from rules import run_rules
from graph import analyze_graph
from anomaly import run_anomaly_detection

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
log = logging.getLogger(__name__)

# how often each detection layer runs
GRAPH_INTERVAL_SECONDS = 60
ANOMALY_INTERVAL_SECONDS = 300


def connect_redis():
    """retries until redis is available — same pattern as the simulator"""
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))

    while True:
        try:
            client = redis.Redis(host=host, port=port, decode_responses=True)
            client.ping()
            log.info(f"connected to redis at {host}:{port}")
            return client
        except redis.ConnectionError:
            log.warning("redis not ready, retrying in 2 seconds...")
            time.sleep(2)


def connect_postgres():
    """retries until postgres is available"""
    while True:
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
            )
            conn.autocommit = True
            log.info("connected to postgres")
            return conn
        except psycopg2.OperationalError:
            log.warning("postgres not ready, retrying in 2 seconds...")
            time.sleep(2)


def register_account(conn, account):
    """
    writes a new account to postgres if it doesn't already exist.
    we use ON CONFLICT DO NOTHING so it's safe to call multiple times
    for the same account without causing duplicates.
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO accounts (id, username, follower_count, following_count, post_count, risk_score, status)
            VALUES (%s, %s, %s, %s, %s, 0.0, 'clean')
            ON CONFLICT (id) DO NOTHING
        """, (
            account["id"],
            account["username"],
            account.get("follower_count", 0),
            account.get("following_count", 0),
            account.get("post_count", 0),
        ))


def write_event(conn, event):
    """writes a raw event to the events table"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO events (account_id, event_type, target_id, metadata_)
            VALUES (%s, %s, %s, %s)
        """, (
            event["account_id"],
            event["event_type"],
            event.get("target_id"),
            json.dumps(event.get("metadata", {})),
        ))


def write_flag(conn, r, account_id, source, reason, score):
    """
    writes a flag to postgres and, if the score is high enough,
    publishes it to the redis pub/sub channel so the frontend
    gets notified in real time
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO flags (account_id, source, reason, score)
            VALUES (%s, %s, %s, %s)
        """, (account_id, source, reason, score))

        # update the account's overall risk score — simple average for now
        cur.execute("""
            UPDATE accounts
            SET risk_score = (
                SELECT AVG(score) FROM flags WHERE account_id = %s
            ),
            status = CASE
                WHEN status = 'clean' THEN 'flagged'
                ELSE status
            END
            WHERE id = %s
        """, (account_id, account_id))

    # anything above 0.7 gets pushed to the frontend immediately
    if score >= 0.7:
        flag_payload = json.dumps({
            "account_id": account_id,
            "source": source,
            "reason": reason,
            "score": score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        r.publish("high_risk_flags", flag_payload)
        log.info(f"high risk flag published — {account_id} ({source}, score {score})")


def get_recent_events(conn, minutes=1):
    """fetches events from the last N minutes for graph analysis"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT account_id, event_type, target_id, metadata_
            FROM events
            WHERE timestamp >= NOW() - INTERVAL '%s minutes'
        """, (minutes,))
        return cur.fetchall()


def get_account_stats(conn):
    """
    builds a stats dict per account that both the graph and anomaly
    detectors can use — follower counts, recent activity rates, etc.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                a.id,
                a.follower_count,
                a.following_count,
                a.post_count,
                COUNT(CASE WHEN e.event_type = 'follow'
                    AND e.timestamp >= NOW() - INTERVAL '10 minutes' THEN 1 END) AS recent_follows,
                COUNT(CASE WHEN e.event_type = 'post'
                    AND e.timestamp >= NOW() - INTERVAL '5 minutes' THEN 1 END) AS recent_posts,
                COUNT(CASE WHEN e.event_type = 'follow' THEN 1 END) AS total_follows,
                COUNT(CASE WHEN e.event_type = 'unfollow' THEN 1 END) AS total_unfollows
            FROM accounts a
            LEFT JOIN events e ON e.account_id = a.id
            GROUP BY a.id, a.follower_count, a.following_count, a.post_count
        """)
        return cur.fetchall()


def graph_analyzer_loop(conn, r):
    """
    runs in a background thread every 60 seconds.
    pulls recent events, builds the graph, flags suspicious clusters.
    """
    while True:
        try:
            time.sleep(GRAPH_INTERVAL_SECONDS)
            log.info("running graph analysis...")

            events = get_recent_events(conn, minutes=1)
            suspicious_clusters = analyze_graph(events)

            for cluster in suspicious_clusters:
                for account_id in cluster["members"]:
                    write_flag(
                        conn, r,
                        account_id=account_id,
                        source="graph_analyzer",
                        reason=cluster["reason"],
                        score=cluster["score"],
                    )

        except Exception as e:
            log.error(f"graph analyzer error: {e}")


def anomaly_detector_loop(conn, r):
    """
    runs in a background thread every 5 minutes.
    builds feature vectors for all accounts and runs isolation forest + z-scores.
    """
    while True:
        try:
            time.sleep(ANOMALY_INTERVAL_SECONDS)
            log.info("running anomaly detection...")

            accounts = get_account_stats(conn)
            flagged = run_anomaly_detection([dict(a) for a in accounts])

            for flag in flagged:
                write_flag(
                    conn, r,
                    account_id=flag["account_id"],
                    source="anomaly_detector",
                    reason=flag["reason"],
                    score=flag["score"],
                )

                # also store the feature vector for this account so we can track drift
                account = next((a for a in accounts if a["id"] == flag["account_id"]), None)
                if account:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO feature_vectors (account_id, features)
                            VALUES (%s, %s)
                        """, (flag["account_id"], json.dumps(dict(account))))

        except Exception as e:
            log.error(f"anomaly detector error: {e}")


def main():
    r = connect_redis()
    conn = connect_postgres()

    # register all accounts from the simulator's accounts queue before processing events
    log.info("registering accounts from queue...")
    while True:
        raw = r.lpop("accounts_queue")
        if not raw:
            break
        account = json.loads(raw)
        register_account(conn, account)
    log.info("accounts registered")

    # start the graph analyzer and anomaly detector in background threads
    threading.Thread(target=graph_analyzer_loop, args=(conn, r), daemon=True).start()
    threading.Thread(target=anomaly_detector_loop, args=(conn, r), daemon=True).start()

    log.info("worker ready, listening for events...")

    # main loop; pull events off the queue and process them one at a time
    while True:
        try:
            # blpop blocks until something arrives, no busywaiting
            result = r.blpop("events_queue", timeout=5)
            if not result:
                continue

            _, raw = result
            event = json.loads(raw)

            # write the raw event to postgres
            write_event(conn, event)

            # get this account's current stats and run the rule engine
            accounts = get_account_stats(conn)
            account_stats = next(
                (dict(a) for a in accounts if a["id"] == event["account_id"]), None
            )

            if account_stats:
                triggered_rules = run_rules(account_stats)
                for rule in triggered_rules:
                    write_flag(
                        conn, r,
                        account_id=event["account_id"],
                        source="rule_engine",
                        reason=rule["reason"],
                        score=rule["score"],
                    )

        except Exception as e:
            log.error(f"worker error processing event: {e}")


if __name__ == "__main__":
    main()