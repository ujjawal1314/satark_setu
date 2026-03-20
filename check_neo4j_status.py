"""
Check Neo4j and Graph Database Status
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
import os

print("=" * 70)
print("NEO4J & GRAPH DATABASE STATUS CHECK")
print("=" * 70)

# Load environment
load_dotenv()

print("\n1. ENVIRONMENT CONFIGURATION")
print("-" * 70)
use_neo4j = os.getenv('USE_NEO4J', 'false')
neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')

print(f"USE_NEO4J: {use_neo4j}")
print(f"NEO4J_URI: {neo4j_uri}")
print(f"NEO4J_USER: {neo4j_user}")
print(f"NEO4J_PASSWORD: {'*' * len(neo4j_password)}")

print("\n2. NEO4J DRIVER AVAILABILITY")
print("-" * 70)
try:
    from neo4j import GraphDatabase
    print("✅ Neo4j driver installed")
    NEO4J_AVAILABLE = True
except ImportError:
    print("❌ Neo4j driver NOT installed")
    print("   Install with: pip install neo4j")
    NEO4J_AVAILABLE = False

print("\n3. GRAPH DATABASE MODULE")
print("-" * 70)
try:
    from graph_database import GraphDatabaseFactory, NEO4J_AVAILABLE as MODULE_NEO4J
    print("✅ graph_database.py module loaded")
    print(f"   Neo4j available in module: {MODULE_NEO4J}")
except Exception as e:
    print(f"❌ Error loading graph_database.py: {e}")
    sys.exit(1)

print("\n4. CURRENT MODE")
print("-" * 70)
if use_neo4j.lower() == 'true':
    print("🔵 CONFIGURED FOR: Neo4j")
    print("   System will attempt to connect to Neo4j")
else:
    print("🟢 CONFIGURED FOR: NetworkX (in-memory)")
    print("   System will use NetworkX fallback mode")

print("\n5. NEO4J CONNECTION TEST")
print("-" * 70)
if use_neo4j.lower() == 'true' and NEO4J_AVAILABLE:
    print("Testing Neo4j connection...")
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        driver.verify_connectivity()
        print("✅ Neo4j connection successful!")
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   System will fall back to NetworkX")
elif use_neo4j.lower() == 'true' and not NEO4J_AVAILABLE:
    print("⚠️ Neo4j configured but driver not installed")
    print("   Install with: pip install neo4j")
else:
    print("⏭️ Skipped (USE_NEO4J=false)")

print("\n6. DETECTION ENGINE TEST")
print("-" * 70)
try:
    import pandas as pd
    from detection_engine_neo4j import SatarkSetuDetectorNeo4j
    
    # Load minimal data
    cyber_df = pd.read_csv('cyber_events.csv').head(100)
    txn_df = pd.read_csv('transactions.csv').head(100)
    
    print("Creating detector...")
    detector = SatarkSetuDetectorNeo4j(cyber_df, txn_df)
    
    # Check which database is being used
    db_type = type(detector.graph_db).__name__
    print(f"✅ Detector created successfully")
    print(f"   Using database: {db_type}")
    
    # Get stats
    stats = detector.graph_db.get_stats()
    print(f"   Nodes: {stats.get('num_nodes', 0)}")
    print(f"   Edges: {stats.get('num_edges', 0)}")
    
except Exception as e:
    print(f"❌ Error creating detector: {e}")
    import traceback
    traceback.print_exc()

print("\n7. DASHBOARD INTEGRATION")
print("-" * 70)
print("The dashboard uses detection_engine_neo4j.py which:")
print("  • Automatically selects Neo4j or NetworkX based on USE_NEO4J")
print("  • Falls back to NetworkX if Neo4j connection fails")
print("  • Shows database status in sidebar")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if use_neo4j.lower() == 'true':
    print("📊 CURRENT MODE: Neo4j (Configured)")
    if NEO4J_AVAILABLE:
        print("✅ Neo4j driver installed")
        print("⚠️ Check if Neo4j server is running:")
        print("   docker run --name neo4j -p 7474:7474 -p 7687:7687 \\")
        print("              -e NEO4J_AUTH=neo4j/password -d neo4j:latest")
    else:
        print("❌ Neo4j driver not installed")
        print("   Install with: pip install neo4j")
else:
    print("📊 CURRENT MODE: NetworkX (In-Memory)")
    print("✅ No Neo4j setup required")
    print("✅ Works out of the box")
    print("✅ Perfect for demos")
    print("\nTo enable Neo4j:")
    print("  1. Start Neo4j server (see above)")
    print("  2. Set USE_NEO4J=true in .env")
    print("  3. Restart dashboard")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("For your demo: Keep USE_NEO4J=false")
print("  • NetworkX is faster for small datasets")
print("  • No external dependencies")
print("  • Instant startup")
print("  • Same functionality")
print("\nFor production: Set USE_NEO4J=true")
print("  • Handles billions of nodes")
print("  • Persistent storage")
print("  • Advanced graph queries")
print("=" * 70)
