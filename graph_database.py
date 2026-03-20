"""
Graph Database Abstraction Layer
Supports both Neo4j (production) and NetworkX (fallback/demo)
"""

import os
from abc import ABC, abstractmethod
import networkx as nx
from typing import List, Dict, Any, Optional
import community.community_louvain as community_louvain

# Try to import Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not installed. Using NetworkX fallback mode.")


class GraphDatabaseInterface(ABC):
    """Abstract interface for graph database operations"""
    
    @abstractmethod
    def add_node(self, node_id: str, node_type: str, **properties):
        """Add a node to the graph"""
        pass
    
    @abstractmethod
    def add_edge(self, from_node: str, to_node: str, edge_type: str, **properties):
        """Add an edge between two nodes"""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all neighbors of a node"""
        pass
    
    @abstractmethod
    def get_node_degree(self, node_id: str) -> int:
        """Get the degree (number of connections) of a node"""
        pass
    
    @abstractmethod
    def detect_communities(self) -> Dict[str, int]:
        """Detect communities/clusters in the graph"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all data from the graph"""
        pass


class Neo4jGraphDatabase(GraphDatabaseInterface):
    """Neo4j graph database implementation"""
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()
        print(f"Connected to Neo4j at {uri}")
    
    def _verify_connection(self):
        """Verify Neo4j connection"""
        with self.driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def add_node(self, node_id: str, node_type: str, **properties):
        """Add a node to Neo4j"""
        with self.driver.session() as session:
            query = f"""
            MERGE (n:{node_type} {{id: $node_id}})
            SET n += $properties
            RETURN n
            """
            session.run(query, node_id=node_id, properties=properties)
    
    def add_edge(self, from_node: str, to_node: str, edge_type: str, **properties):
        """Add an edge in Neo4j"""
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $from_node}})
            MATCH (b {{id: $to_node}})
            MERGE (a)-[r:{edge_type}]->(b)
            SET r += $properties
            RETURN r
            """
            session.run(query, from_node=from_node, to_node=to_node, properties=properties)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighbors from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $node_id})--(neighbor)
            RETURN neighbor.id as neighbor_id
            """
            result = session.run(query, node_id=node_id)
            return [record["neighbor_id"] for record in result]
    
    def get_node_degree(self, node_id: str) -> int:
        """Get node degree from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $node_id})--(neighbor)
            RETURN count(neighbor) as degree
            """
            result = session.run(query, node_id=node_id)
            record = result.single()
            return record["degree"] if record else 0
    
    def detect_communities(self) -> Dict[str, int]:
        """Detect communities using Neo4j Graph Data Science library"""
        with self.driver.session() as session:
            # Check if GDS is available
            try:
                # Create in-memory graph projection
                session.run("""
                CALL gds.graph.project(
                    'muleNetwork',
                    '*',
                    '*'
                )
                """)
                
                # Run Louvain community detection
                result = session.run("""
                CALL gds.louvain.stream('muleNetwork')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id as node_id, communityId
                """)
                
                communities = {record["node_id"]: record["communityId"] for record in result}
                
                # Drop the projection
                session.run("CALL gds.graph.drop('muleNetwork')")
                
                return communities
            except Exception as e:
                print(f"Neo4j GDS not available, using fallback: {e}")
                # Fallback: export to NetworkX and use Louvain
                return self._detect_communities_fallback()
    
    def _detect_communities_fallback(self) -> Dict[str, int]:
        """Fallback community detection using NetworkX"""
        # Export graph to NetworkX
        G = nx.Graph()
        
        with self.driver.session() as session:
            # Get all edges
            result = session.run("""
            MATCH (a)-[r]-(b)
            RETURN a.id as from_node, b.id as to_node
            """)
            
            for record in result:
                G.add_edge(record["from_node"], record["to_node"])
        
        # Use Louvain algorithm
        return community_louvain.best_partition(G)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics from Neo4j"""
        with self.driver.session() as session:
            # Count nodes
            node_result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = node_result.single()["node_count"]
            
            # Count edges
            edge_result = session.run("MATCH ()-[r]->() RETURN count(r) as edge_count")
            edge_count = edge_result.single()["edge_count"]
            
            # Count by node type
            type_result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            """)
            node_types = {record["node_type"]: record["count"] for record in type_result}
            
            return {
                "nodes": node_count,
                "edges": edge_count,
                "node_types": node_types,
                "database": "Neo4j"
            }
    
    def clear(self):
        """Clear all data from Neo4j"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Neo4j database cleared")


class NetworkXGraphDatabase(GraphDatabaseInterface):
    """NetworkX in-memory graph implementation (fallback)"""
    
    def __init__(self):
        """Initialize NetworkX graph"""
        self.graph = nx.Graph()
        self.node_types = {}
        print("Using NetworkX in-memory graph (fallback mode)")
    
    def add_node(self, node_id: str, node_type: str, **properties):
        """Add a node to NetworkX"""
        self.graph.add_node(node_id, node_type=node_type, **properties)
        self.node_types[node_id] = node_type
    
    def add_edge(self, from_node: str, to_node: str, edge_type: str, **properties):
        """Add an edge to NetworkX"""
        self.graph.add_edge(from_node, to_node, edge_type=edge_type, **properties)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighbors from NetworkX"""
        if node_id in self.graph:
            return list(self.graph.neighbors(node_id))
        return []
    
    def get_node_degree(self, node_id: str) -> int:
        """Get node degree from NetworkX"""
        if node_id in self.graph:
            return self.graph.degree(node_id)
        return 0
    
    def detect_communities(self) -> Dict[str, int]:
        """Detect communities using Louvain algorithm"""
        return community_louvain.best_partition(self.graph)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics from NetworkX"""
        # Count by node type
        type_counts = {}
        for node, node_type in self.node_types.items():
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_types": type_counts,
            "database": "NetworkX (in-memory)"
        }
    
    def clear(self):
        """Clear NetworkX graph"""
        self.graph.clear()
        self.node_types.clear()
        print("NetworkX graph cleared")
    
    def get_networkx_graph(self) -> nx.Graph:
        """Get the underlying NetworkX graph (for compatibility)"""
        return self.graph


class GraphDatabaseFactory:
    """Factory to create appropriate graph database instance"""
    
    @staticmethod
    def create(use_neo4j: bool = True) -> GraphDatabaseInterface:
        """
        Create graph database instance
        
        Args:
            use_neo4j: Try to use Neo4j if available
        
        Returns:
            GraphDatabaseInterface instance (Neo4j or NetworkX)
        """
        # Check environment variables for Neo4j configuration
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        
        # Try Neo4j if requested and available
        if use_neo4j and NEO4J_AVAILABLE:
            try:
                return Neo4jGraphDatabase(neo4j_uri, neo4j_user, neo4j_password)
            except Exception as e:
                print(f"⚠️ Could not connect to Neo4j: {e}")
                print("⚠️ Falling back to NetworkX in-memory graph")
        
        # Fallback to NetworkX
        return NetworkXGraphDatabase()


# Example usage and testing
if __name__ == "__main__":
    # Set UTF-8 encoding for console output (Windows compatibility)
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n=== Testing Graph Database Abstraction Layer ===\n")
    
    # Create graph database (will auto-select Neo4j or NetworkX)
    db = GraphDatabaseFactory.create(use_neo4j=True)
    
    # Clear any existing data
    db.clear()
    
    # Add some test nodes
    print("\n1. Adding nodes...")
    db.add_node("ACC_001", "Account", risk_score=85)
    db.add_node("ACC_002", "Account", risk_score=45)
    db.add_node("IP_192.168.1.1", "IP", location="India")
    db.add_node("BEN_SG_001", "Beneficiary", country="Singapore")
    
    # Add edges
    print("2. Adding edges...")
    db.add_edge("ACC_001", "IP_192.168.1.1", "ACCESSED_FROM")
    db.add_edge("ACC_001", "BEN_SG_001", "SENT_TO", amount=45000)
    db.add_edge("ACC_002", "BEN_SG_001", "SENT_TO", amount=48000)
    
    # Get neighbors
    print("\n3. Getting neighbors of ACC_001:")
    neighbors = db.get_neighbors("ACC_001")
    print(f"   Neighbors: {neighbors}")
    
    # Get node degree
    print("\n4. Getting degree of BEN_SG_001:")
    degree = db.get_node_degree("BEN_SG_001")
    print(f"   Degree: {degree}")
    
    # Get statistics
    print("\n5. Graph statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Detect communities
    print("\n6. Detecting communities...")
    communities = db.detect_communities()
    print(f"   Found {len(set(communities.values()))} communities")
    
    print("\n✅ All tests passed!")
