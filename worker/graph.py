import logging
import networkx as nx
import community as community_louvain  # this is the python-louvain package

log = logging.getLogger(__name__)

# a cluster is sus if more than this fraction of its edges are internal
INSULARITY_THRESHOLD = 0.85

# clusters smaller than this aren't worth flagging, too small to be meaningful
MIN_CLUSTER_SIZE = 4


def build_graph(events):
    """
    takes a list of recent interaction events and builds a directed graph.
    each account is a node, each interaction is an edge.
    we use a plain Graph (undirected) for louvain since it works on undirected graphs.
    """
    G = nx.Graph()

    for event in events:
        account_id = event.get("account_id")
        target_id = event.get("target_id")

        # only add edges where there's an actual interaction between two accounts
        if account_id and target_id:
            if G.has_edge(account_id, target_id):
                # if the edge already exists, increase the weight; more interactions = stronger connection
                G[account_id][target_id]["weight"] += 1
            else:
                G.add_edge(account_id, target_id, weight=1)

    return G


def detect_suspicious_clusters(G):
    """
    runs louvain community detection on the graph, then checks each
    community to see if it's suspiciously insular; lots of internal
    edges, very few connections to the outside world
    """
    if len(G.nodes) < MIN_CLUSTER_SIZE:
        return []

    # louvain gives us a dict mapping each node to a community id
    partition = community_louvain.best_partition(G)

    # group nodes by their community
    communities = {}
    for node, community_id in partition.items():
        communities.setdefault(community_id, []).append(node)

    suspicious = []

    for community_id, members in communities.items():
        if len(members) < MIN_CLUSTER_SIZE:
            continue

        member_set = set(members)

        # count edges that stay inside the cluster vs edges that go outside
        internal_edges = 0
        external_edges = 0

        for node in members:
            for neighbor in G.neighbors(node):
                if neighbor in member_set:
                    internal_edges += 1
                else:
                    external_edges += 1

        total_edges = internal_edges + external_edges
        if total_edges == 0:
            continue

        insularity = internal_edges / total_edges

        if insularity >= INSULARITY_THRESHOLD:
            suspicious.append({
                "community_id": community_id,
                "members": members,
                "insularity": round(insularity, 3),
                "size": len(members),
                "reason": f"cluster of {len(members)} accounts with {int(insularity * 100)}% internal interactions",
                "score": round(insularity, 3),
            })

    return suspicious


def analyze_graph(events):
    """entry point, builds the graph and returns any suspicious clusters found"""
    G = build_graph(events)
    suspicious_clusters = detect_suspicious_clusters(G)

    log.info(f"graph analysis complete — {len(G.nodes)} nodes, {len(G.edges)} edges, {len(suspicious_clusters)} suspicious clusters")

    return suspicious_clusters