# 🗄️ Neo4j Graph Database Setup Guide

## Overview

SatarkSetu now supports **Neo4j graph database** for production-grade graph storage and analysis. The system automatically falls back to NetworkX if Neo4j is not available.

---

## Quick Start (3 Options)

### Option 1: Use NetworkX (Default - No Setup Required)
✅ **Recommended for hackathon demo**
- No installation needed
- Works out of the box
- Perfect for demo with 20k events
- System automatically uses NetworkX fallback

### Option 2: Neo4j Desktop (Easiest for Local Development)
⏱️ **Setup time: 10 minutes**
1. Download Neo4j Desktop: https://neo4j.com/download/
2. Install and create a new database
3. Set password
4. Start the database
5. Update `.env` file with credentials

### Option 3: Neo4j Docker (For Production Demo)
⏱️ **Setup time: 5 minutes**
```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:latest
```

---

## Detailed Setup Instructions

### Option 2: Neo4j Desktop (Recommended)

#### Step 1: Download and Install
1. Go to https://neo4j.com/download/
2. Download Neo4j Desktop for your OS
3. Install the application
4. Launch Neo4j Desktop

#### Step 2: Create Database
1. Click "New" → "Create Project"
2. Name it "SatarkSetu"
3. Click "Add" → "Local DBMS"
4. Name: "SatarkSetu-Graph"
5. Password: Choose a secure password (remember this!)
6. Version: Select latest (5.x)
7. Click "Create"

#### Step 3: Start Database
1. Click "Start" on your database
2. Wait for it to show "Active"
3. Note the connection details:
   - Bolt URL: `bolt://localhost:7687`
   - HTTP URL: `http://localhost:7474`

#### Step 4: Configure SatarkSetu
Edit `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

#### Step 5: Install Python Driver
```bash
pip install neo4j
```

#### Step 6: Test Connection
```bash
python graph_database.py
```

Expected output:
```
✅ Connected to Neo4j at bolt://localhost:7687
✅ All tests passed!
```

---

### Option 3: Neo4j Docker

#### Step 1: Run Neo4j Container
```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/satarksetu2024 \
    -d \
    neo4j:latest
```

#### Step 2: Verify Container is Running
```bash
docker ps
```

You should see neo4j container running.

#### Step 3: Access Neo4j Browser
Open browser: http://localhost:7474

Login:
- Username: `neo4j`
- Password: `satarksetu2024`

#### Step 4: Configure SatarkSetu
Edit `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=satarksetu2024
```

#### Step 5: Test Connection
```bash
python graph_database.py
```

---

## Using Neo4j with SatarkSetu

### Test the Graph Database Layer
```bash
python graph_database.py
```

### Test Detection Engine with Neo4j
```bash
python detection_engine_neo4j.py
```

### Run Dashboard with Neo4j
The dashboard will automatically use Neo4j if configured:
```bash
streamlit run dashboard_enhanced.py --server.maxUploadSize=200
```

---

## Verification

### Check Which Database is Being Used

When you run the detection engine, look for this message:

**Using Neo4j:**
```
✅ Connected to Neo4j at bolt://localhost:7687
✅ Detector initialized with Neo4j
Graph built: 23,054 nodes, 34,305 edges using Neo4j
```

**Using NetworkX (Fallback):**
```
Neo4j driver not installed. Using NetworkX fallback mode.
✅ Using NetworkX in-memory graph (fallback mode)
✅ Detector initialized with NetworkX (in-memory)
Graph built: 23,054 nodes, 34,305 edges using NetworkX (in-memory)
```

---

## Neo4j Browser Queries

Once data is loaded, try these queries in Neo4j Browser (http://localhost:7474):

### 1. View All Nodes
```cypher
MATCH (n)
RETURN n
LIMIT 100
```

### 2. Find High-Risk Accounts
```cypher
MATCH (a:Account)
WHERE a.risk_score > 70
RETURN a
LIMIT 20
```

### 3. Find Mule Rings (Accounts Sharing Beneficiaries)
```cypher
MATCH (a1:Account)-[:SENT_TO]->(b:Beneficiary)<-[:SENT_TO]-(a2:Account)
WHERE a1 <> a2
RETURN a1, b, a2
LIMIT 50
```

### 4. Find Accounts with Foreign IPs
```cypher
MATCH (a:Account)-[:ACCESSED_FROM]->(ip:IP)
WHERE ip.location <> 'India'
RETURN a, ip
LIMIT 20
```

### 5. Count Nodes by Type
```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC
```

---

## Performance Comparison

| Feature | NetworkX | Neo4j |
|---------|----------|-------|
| Setup Time | 0 min | 5-10 min |
| Data Size | <100k nodes | Billions of nodes |
| Query Speed | Fast (in-memory) | Very fast (indexed) |
| Persistence | No | Yes |
| Concurrent Access | No | Yes |
| Graph Algorithms | Basic | Advanced (GDS) |
| Production Ready | No | Yes |

---

## Troubleshooting

### Issue: "Could not connect to Neo4j"
**Solution**: 
1. Check Neo4j is running: `docker ps` or check Neo4j Desktop
2. Verify credentials in `.env` file
3. Check firewall isn't blocking port 7687

### Issue: "Neo4j driver not installed"
**Solution**:
```bash
pip install neo4j
```

### Issue: "Authentication failed"
**Solution**:
- Check username/password in `.env` file
- Default username is always `neo4j`
- Password is what you set during database creation

### Issue: Graph queries are slow
**Solution**:
1. Create indexes in Neo4j:
```cypher
CREATE INDEX account_id FOR (a:Account) ON (a.id);
CREATE INDEX beneficiary_id FOR (b:Beneficiary) ON (b.id);
```

---

## For Hackathon Demo

### Recommended Approach:
✅ **Use NetworkX (no setup required)**
- System works perfectly with NetworkX
- No installation needed
- Fast for demo dataset (20k events)
- Can mention "Neo4j-ready architecture" in presentation

### If You Want to Impress Judges:
✅ **Use Neo4j Docker (5 min setup)**
- Shows production-ready architecture
- Demonstrates graph database knowledge
- Can show Neo4j Browser visualization
- Proves scalability claims

---

## Architecture Benefits

### Why This Hybrid Approach is Smart:

1. **Flexibility**: Works with or without Neo4j
2. **Demo-Ready**: No dependencies for quick demo
3. **Production-Ready**: Easy migration to Neo4j
4. **Scalable**: Architecture supports billions of nodes
5. **Honest**: Can demo either way and be truthful

---

## Next Steps

### For Demo:
1. Test with NetworkX (default): `python detection_engine_neo4j.py`
2. If time permits, set up Neo4j Docker
3. Update presentation to mention "Neo4j-compatible architecture"

### For Production:
1. Deploy Neo4j cluster
2. Enable Graph Data Science (GDS) library
3. Create indexes for performance
4. Set up backup and monitoring

---

## Summary

✅ **NetworkX**: Perfect for hackathon demo (no setup)  
✅ **Neo4j**: Production-grade graph database (5-10 min setup)  
✅ **Hybrid**: System automatically chooses best option  
✅ **Scalable**: Architecture ready for millions of nodes  

**You can confidently say**: "Built with Neo4j-compatible graph database architecture, currently running on NetworkX for demo, production-ready for Neo4j deployment."

---

**Questions?** Check the code in `graph_database.py` for implementation details.
