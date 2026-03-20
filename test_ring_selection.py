"""
Test stress-cluster selection parsing logic for dashboard helpers.
"""

print("=" * 60)
print("STRESS CLUSTER SELECTION TEST")
print("=" * 60)

test_cases = [
    "Cluster 0 (12 borrowers)",
    "Cluster 1 (8 borrowers)",
    "Cluster 5 (15 borrowers)",
]

for value in test_cases:
    cluster_idx = int(value.split()[1])
    print(f"{value} -> cluster_id={cluster_idx}")

import pandas as pd
from detection_engine_neo4j import SatarkSetuDetectorNeo4j

borrowers = pd.read_csv("borrowers.csv")
transactions = pd.read_csv("loan_transactions.csv")
regional = pd.read_csv("regional_context.csv")
detector = SatarkSetuDetectorNeo4j(borrowers, transactions, regional_df=regional, use_neo4j=False)
detector.build_graph()
clusters = detector.detect_stress_clusters()

for cluster in clusters[:5]:
    dropdown_text = f"Cluster {cluster['cluster_id']} ({cluster['size']} borrowers)"
    extracted_id = int(dropdown_text.split()[1])
    assert extracted_id == cluster["cluster_id"]
    print(f"✅ {dropdown_text}")

print("✅ Stress cluster selection logic is correct")
