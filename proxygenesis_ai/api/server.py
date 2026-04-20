"""
Enhanced REST API with authentication, advanced filters, and multiple export formats
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Request, Response
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import hashlib
import secrets
from datetime import datetime
import json

# Import local modules
import sys
sys.path.append('..')
from database.db_manager import DatabaseManager
from ml_enhanced.predictor import EnhancedMLPredictor
from utils.geoip import GeoIPManager

app = FastAPI(
    title="Proxygenesis AI API",
    description="Advanced Proxy Management API with ML predictions and auto-healing",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize components
db_manager = None
ml_predictor = None
geo_manager = None

def get_db():
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_ml():
    """Get ML predictor instance"""
    global ml_predictor
    if ml_predictor is None:
        ml_predictor = EnhancedMLPredictor()
        ml_predictor.load_model()
    return ml_predictor

def get_geo():
    """Get GeoIP manager instance"""
    global geo_manager
    if geo_manager is None:
        geo_manager = GeoIPManager()
    return geo_manager

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """Verify API key authentication"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Check in database
    cursor.execute('''
        SELECT id, name, rate_limit, last_used_at 
        FROM api_keys 
        WHERE key_hash = ? AND is_active = 1
    ''', (key_hash,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Update last used timestamp
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE key_hash = ?
    ''', (key_hash,))
    conn.commit()
    conn.close()
    
    return {"id": result['id'], "name": result['name']}


# Pydantic models
class ProxyFilter(BaseModel):
    country: Optional[str] = None
    protocol: Optional[str] = None
    anonymity: Optional[str] = None
    min_speed: Optional[float] = None
    max_speed: Optional[float] = None
    min_uptime: Optional[float] = None
    limit: int = 1000

class ProxyCreate(BaseModel):
    ip: str
    port: int
    protocol: Optional[str] = 'http'
    country: Optional[str] = None
    anonymity_level: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    rate_limit: Optional[int] = 1000


# Public endpoints (no auth required for basic info)
@app.get("/")
async def root():
    """API welcome endpoint"""
    return {
        "message": "Welcome to Proxygenesis AI API v2.0",
        "docs": "/docs",
        "endpoints": {
            "proxies": "/api/v1/proxies",
            "export": "/api/v1/export",
            "stats": "/api/v1/stats",
            "autoheal": "/api/v1/autoheal"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# Protected endpoints (require API key)
@app.get("/api/v1/proxies")
async def get_proxies(
    country: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    anonymity: Optional[str] = Query(None),
    min_speed: Optional[float] = Query(None),
    max_speed: Optional[float] = Query(None),
    min_uptime: Optional[float] = Query(None),
    limit: int = Query(1000, le=10000),
    auth: dict = Depends(verify_api_key)
):
    """
    Get proxies with advanced filters
    
    - **country**: Filter by country name or code
    - **protocol**: http, https, socks4, socks5
    - **anonymity**: elite, anonymous, transparent
    - **min_speed**: Maximum response time in ms (lower is better)
    - **max_speed**: Minimum response time in ms
    - **min_uptime**: Minimum uptime percentage
    - **limit**: Max number of proxies to return
    """
    db = get_db()
    
    proxies = db.get_proxies_with_filters(
        country=country,
        protocol=protocol,
        anonymity=anonymity,
        min_speed=min_speed,
        max_speed=max_speed,
        min_uptime=min_uptime,
        limit=limit
    )
    
    return {
        "count": len(proxies),
        "filters": {
            "country": country,
            "protocol": protocol,
            "anonymity": anonymity,
            "min_speed": min_speed,
            "max_speed": max_speed,
            "min_uptime": min_uptime
        },
        "proxies": proxies
    }

@app.get("/api/v1/proxies/{proxy_id}")
async def get_proxy(proxy_id: int, auth: dict = Depends(verify_api_key)):
    """Get specific proxy by ID"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
    proxy = cursor.fetchone()
    conn.close()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    return dict(proxy)

@app.post("/api/v1/proxies")
async def create_proxy(proxy: ProxyCreate, auth: dict = Depends(verify_api_key)):
    """Add a new proxy to the database"""
    db = get_db()
    
    proxy_data = proxy.dict()
    proxy_data['last_checked'] = datetime.now()
    proxy_data['is_active'] = True
    
    try:
        proxy_id = db.add_proxy(proxy_data)
        
        # Enrich with geolocation
        geo = get_geo()
        location = geo.get_location_from_ip(proxy.ip)
        proxy_data.update(location)
        db.add_proxy(proxy_data)  # Update with geo data
        
        return {
            "id": proxy_id,
            "message": "Proxy added successfully",
            "proxy": proxy_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/proxies/{proxy_id}")
async def delete_proxy(proxy_id: int, auth: dict = Depends(verify_api_key)):
    """Delete a proxy from the database"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    return {"message": f"Proxy {proxy_id} deleted successfully"}


@app.get("/api/v1/export")
async def export_proxies(
    format: str = Query("json", regex="^(json|csv|yaml|txt)$"),
    country: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    anonymity: Optional[str] = Query(None),
    min_uptime: Optional[float] = Query(None),
    auth: dict = Depends(verify_api_key)
):
    """
    Export proxies in multiple formats
    
    Supported formats: json, csv, yaml, txt
    """
    db = get_db()
    
    filters = {}
    if country:
        filters['country'] = country
    if protocol:
        filters['protocol'] = protocol
    if anonymity:
        filters['anonymity'] = anonymity
    if min_uptime:
        filters['min_uptime'] = min_uptime
    
    try:
        data = db.export_proxies(format=format, filters=filters if filters else None)
        
        content_types = {
            'json': 'application/json',
            'csv': 'text/csv',
            'yaml': 'application/x-yaml',
            'txt': 'text/plain'
        }
        
        return Response(
            content=data,
            media_type=content_types[format],
            headers={
                "Content-Disposition": f"attachment; filename=proxies.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/stats")
async def get_statistics(auth: dict = Depends(verify_api_key)):
    """Get system statistics and metrics"""
    db = get_db()
    stats = db.get_statistics()
    
    # Add ML model status
    ml = get_ml()
    stats['ml_model_loaded'] = ml.model is not None
    
    # Add cycle stats
    stats['recent_cycles'] = db.get_cycle_stats(limit=5)
    
    return stats

@app.post("/api/v1/autoheal")
async def trigger_autoheal(
    threshold_uptime: float = Query(50.0, ge=0, le=100),
    threshold_checks: int = Query(5, ge=1),
    auth: dict = Depends(verify_api_key)
):
    """
    Trigger auto-healing process to remove unstable proxies
    
    - **threshold_uptime**: Remove proxies with uptime below this percentage
    - **threshold_checks**: Only consider proxies checked at least this many times
    """
    db = get_db()
    
    removed_count = db.remove_unstable_proxies(
        threshold_uptime=threshold_uptime,
        threshold_checks=threshold_checks
    )
    
    return {
        "message": "Auto-healing completed",
        "removed_count": removed_count,
        "thresholds": {
            "uptime": threshold_uptime,
            "checks": threshold_checks
        }
    }

@app.get("/api/v1/predict/{proxy_id}")
async def predict_proxy_quality(proxy_id: int, auth: dict = Depends(verify_api_key)):
    """Get ML prediction for a specific proxy"""
    db = get_db()
    ml = get_ml()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
    proxy = cursor.fetchone()
    conn.close()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    proxy_dict = dict(proxy)
    score, importance = ml.predict(proxy_dict)
    
    return {
        "proxy_id": proxy_id,
        "quality_score": score,
        "quality_label": "Good" if score > 0.7 else "Medium" if score > 0.4 else "Poor",
        "feature_importance": importance
    }

@app.post("/api/v1/ml/retrain")
async def retrain_model(auth: dict = Depends(verify_api_key)):
    """Retrain ML model with latest data"""
    db = get_db()
    ml = get_ml()
    
    success = ml.retrain_with_new_data(db)
    
    if success:
        return {"message": "Model retrained successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to retrain model")


# API Key management
@app.get("/api/v1/keys")
async def list_api_keys(auth: dict = Depends(verify_api_key)):
    """List all API keys (admin only)"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, created_at, last_used_at, is_active, rate_limit
        FROM api_keys
        ORDER BY created_at DESC
    ''')
    
    keys = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Don't expose key hashes
    return {"keys": keys}

@app.post("/api/v1/keys")
async def create_api_key(key_data: APIKeyCreate, auth: dict = Depends(verify_api_key)):
    """Create a new API key"""
    db = get_db()
    
    # Generate random API key
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO api_keys (key_hash, name, rate_limit)
        VALUES (?, ?, ?)
    ''', (key_hash, key_data.name, key_data.rate_limit))
    
    key_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": key_id,
        "name": key_data.name,
        "api_key": raw_key,
        "warning": "Save this key! It won't be shown again."
    }

@app.delete("/api/v1/keys/{key_id}")
async def revoke_api_key(key_id: int, auth: dict = Depends(verify_api_key)):
    """Revoke an API key"""
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE api_keys SET is_active = 0 WHERE id = ?
    ''', (key_id,))
    
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    
    if updated == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": f"API key {key_id} revoked"}


# Cycles management
@app.get("/api/v1/cycles")
async def get_cycles(limit: int = Query(10, le=100), auth: dict = Depends(verify_api_key)):
    """Get recent collection cycles"""
    db = get_db()
    cycles = db.get_cycle_stats(limit=limit)
    return {"cycles": cycles}

@app.post("/api/v1/cycles/start")
async def start_cycle(auth: dict = Depends(verify_api_key)):
    """Start a new collection cycle"""
    db = get_db()
    cycle_id = db.create_cycle()
    return {"cycle_id": cycle_id, "status": "started"}

@app.post("/api/v1/cycles/{cycle_id}/complete")
async def complete_cycle(
    cycle_id: int,
    total: int,
    valid: int,
    invalid: int,
    avg_speed: float,
    avg_uptime: float,
    auth: dict = Depends(verify_api_key)
):
    """Complete a collection cycle with statistics"""
    db = get_db()
    db.complete_cycle(cycle_id, total, valid, invalid, avg_speed, avg_uptime)
    return {"message": f"Cycle {cycle_id} completed", "stats": {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "avg_speed": avg_speed,
        "avg_uptime": avg_uptime
    }}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Proxygenesis AI API v2.0...")
    print("📖 API Docs: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
