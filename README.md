# System DAG Health API

This project provides a simple Python FastAPI service that:
- Loads a system graph (DAG) from JSON  
- Computes BFS levels  
- Performs async health checks on each component  
- Displays results as JSON, HTML table, and a generated graph PNG  

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
cd health_dag_api/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test with sample JSON
```bash
curl -X POST "http://localhost:8000/health/check"   -H "Content-Type: application/json"   --data-binary "@../sample_data/sample_system.json"
```

### 4. View results
- JSON: `GET /health/check`
- HTML table: `GET /health/table`
- Graph PNG: `GET /health/graph`
- API Docs: `GET /docs`

The static folder will automatically create `graph.png` after the first health check.

