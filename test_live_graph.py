"""
Quick smoke test for borrower network visualization helpers.
"""

print("=" * 60)
print("BORROWER NETWORK VISUALIZATION TEST")
print("=" * 60)

try:
    import pandas as pd
    import networkx as nx
    import plotly.graph_objects as go
    from detection_engine_neo4j import SatarkSetuDetectorNeo4j
except Exception as exc:
    print(f"Import error: {exc}")
    raise

borrowers = pd.read_csv("borrowers.csv")
transactions = pd.read_csv("loan_transactions.csv")
regional = pd.read_csv("regional_context.csv")
detector = SatarkSetuDetectorNeo4j(borrowers, transactions, regional_df=regional, use_neo4j=False)
stats = detector.build_graph()
clusters = detector.detect_stress_clusters()

print(f"Graph ready: {stats['nodes']} nodes, {stats['edges']} edges")
print(f"Stress clusters: {len(clusters)}")

if clusters:
    cluster = clusters[0]
    subgraph = nx.Graph()
    for borrower in cluster["borrowers"][:8]:
        for peer in cluster["borrowers"][:8]:
            if borrower != peer:
                subgraph.add_edge(borrower, peer)

    pos = nx.spring_layout(subgraph, k=0.5, iterations=30)
    edge_trace = go.Scatter(x=[], y=[], mode="lines", hoverinfo="none")
    node_trace = go.Scatter(x=[], y=[], text=[], mode="markers+text", hoverinfo="text")
    for edge in subgraph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace["x"] += tuple([x0, x1, None])
        edge_trace["y"] += tuple([y0, y1, None])
    for node in subgraph.nodes():
        x, y = pos[node]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])
        node_trace["text"] += tuple([node])
    fig = go.Figure(data=[edge_trace, node_trace])
    print(f"Visualization figure created for cluster {cluster['cluster_id']}: {len(fig.data)} traces")

print("✅ Borrower visualization smoke test complete")
