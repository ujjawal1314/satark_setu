"""Simple test showing borrower graph construction works."""

import pandas as pd

from detection_engine_neo4j import SatarkSetuDetectorNeo4j


print("=" * 60)
print("BORROWER GRAPH SIMPLE TEST")
print("=" * 60)

borrowers = pd.read_csv("borrowers.csv").head(50)
transactions = pd.read_csv("loan_transactions.csv").head(200)
regional = pd.read_csv("regional_context.csv")

detector = SatarkSetuDetectorNeo4j(borrowers, transactions, regional_df=regional, use_neo4j=False)
stats = detector.build_graph()

print(f"Database: {stats['database']}")
print(f"Nodes: {stats['nodes']}")
print(f"Edges: {stats['edges']}")
print("✅ Borrower graph build works")
