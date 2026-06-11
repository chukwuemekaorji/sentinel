import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from scipy import stats

log = logging.getLogger(__name__)

# how sensitive isolation forest, lower means more flags, higher means fewer
# -0.3 is a good starting point, tune if too many false positives
ISOLATION_FOREST_THRESHOLD = -0.3

# how many standard deviations away from the mean counts as an anomaly
ZSCORE_THRESHOLD = 3.0

def build_feature_vector(account):
    """
    turns an account's activity data into a list of numbers that the ml model can work w
    the order matters cos we have to be consistent everytime we call it
    """
    return [
        account.get("follower_count", 0),
        account.get("following_count", 0),
        account.get("post_count", 0),
        account.get("recent_follows", 0),
        account.get("recent_posts", 0),
        account.get("total_follows", 0),
        account.get("total_unfollows", 0),
        # follow/ followg ratio, bots tend to follow way more
        account.get("following_count", 0) / max(account.get("follower_count", 1), 1),
    ]   
    
    
def  run_isolation_forest(feature_matrix, account_ids):
    """
    isolation forest works by randomly splitting the data and seeing
    how quickly each point gets isolated. outliers get isolated faster
    bc they're far from the bulk of data
    returns a list of (account_id, score) for accounts that lool sus
    """
    if len(feature_matrix) < 10:
        # not enough data to get meaningful results yet
        return []
    
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(feature_matrix)
    
    # decision_function gives a score where lower means more anomalous
    scores = model.decision_function(feature_matrix)
    
    flagged = []
    for i, score in enumerate(scores):
        if score < ISOLATION_FOREST_THRESHOLD:
            flagged.append({
                "account_id": account_ids[i],
                "score": round(abs(score), 3),
                "reason": f"isolation forest score {score:.3f} - statistically unusual behavior pattern",
            })
            
    return flagged


def run_zscore_analysis(feature_matrix, account_ids):
    """
    z-scores tell us how far each account's stats are from the average.
    if any single feature is more than 3 standard deviations out, it's worth flagging
    this catches different things than isolation forestn - single extreme features rather
    than overall unusual partterns
    """
    if len(feature_matrix) < 10:
        return []
    
    matrix = np.array(feature_matrix)
    z_scores = np.abs(stats.zscore(matrix, axis=0))
    
    flagged = []
    for i, account_z in enumerate(z_scores):
        max_z = np.max(account_z)
        if max_z > ZSCORE_THRESHOLD:
            flagged.append({
                "account_id": account_ids[i],
                "score": round(min(max_z / 10, 1.0), 3),
                "reason": f"z-score {max_z:.2f} on one or more features - extreme outlier in account stats",
            })
            
    return flagged
    
    def run_anomaly_detection(accounts):
        """
        entry point; this one takes a list of account stats dicts, builds feature vectors,
        runs both detection methods and returns combined results deduplicated by account_id
        """
        if not accounts:
            return[]
        
        account_ids = [a["id"] for a in accounts]
        feature_matrix = [build_feature_vector(a) for a in accounts]
        
        if_flags = run_isolation_forest(feature_matrix, account_ids)
        z_flags = run_zscore_analysis(feature_matrix, account_ids)
        
        # merge results; if an account was caught by both, keep the higher score
        combined = {}
        for flag in if_flags + z_flags:
            acc_id = flag["account_id"]
            if acc_id not in combined or flag["score"] > combined[acc_id]["score"]:
                combined[acc_id] = flag
                
        log.info(f"anomaly detection complete - {len(accounts)} accounts analyzed, {len(combined)} flagged")
        
        return list(combined.values())
         
    