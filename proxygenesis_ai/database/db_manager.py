"""
Database module for Proxygenesis AI v2.0
Handles SQLite database operations for proxy history, performance tracking, and ML features
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import os

DATABASE_PATH = "proxygenesis.db"

def get_connection(db_path: str = DATABASE_PATH):
    """Get database connection with row factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: str = DATABASE_PATH):
    """Initialize database tables"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Proxies table with enhanced features
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            protocol TEXT DEFAULT 'http',
            country TEXT,
            country_code TEXT,
            city TEXT,
            asn TEXT,
            anonymity_level TEXT,
            speed_ms REAL,
            uptime_percentage REAL DEFAULT 0.0,
            last_checked TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ip, port)
        )
    ''')
    
    # Proxy history for tracking changes over time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proxy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy_id INTEGER,
            status TEXT,
            speed_ms REAL,
            anonymity_level TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proxy_id) REFERENCES proxies(id)
        )
    ''')
    
    # Cycles table for tracking collection cycles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_proxies INTEGER DEFAULT 0,
            valid_proxies INTEGER DEFAULT 0,
            invalid_proxies INTEGER DEFAULT 0,
            avg_speed_ms REAL,
            avg_uptime REAL,
            status TEXT DEFAULT 'running'
        )
    ''')
    
    # ML predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy_id INTEGER,
            predicted_score REAL,
            actual_score REAL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_version TEXT,
            features_json TEXT,
            FOREIGN KEY (proxy_id) REFERENCES proxies(id)
        )
    ''')
    
    # Performance metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # API keys table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            rate_limit INTEGER DEFAULT 1000
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proxy_ip ON proxies(ip)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proxy_country ON proxies(country)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proxy_active ON proxies(is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_date ON proxy_history(checked_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cycles_status ON cycles(status)')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

class DatabaseManager:
    """Manager class for database operations"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        init_database(db_path)
    
    def add_proxy(self, proxy_data: Dict) -> int:
        """Add or update a proxy in the database"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO proxies (ip, port, protocol, country, country_code, city, asn, 
                                   anonymity_level, speed_ms, uptime_percentage, last_checked, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ip, port) DO UPDATE SET
                    protocol = excluded.protocol,
                    country = excluded.country,
                    country_code = excluded.country_code,
                    city = excluded.city,
                    asn = excluded.asn,
                    anonymity_level = excluded.anonymity_level,
                    speed_ms = excluded.speed_ms,
                    uptime_percentage = excluded.uptime_percentage,
                    last_checked = excluded.last_checked,
                    is_active = excluded.is_active,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                proxy_data.get('ip'),
                proxy_data.get('port'),
                proxy_data.get('protocol', 'http'),
                proxy_data.get('country'),
                proxy_data.get('country_code'),
                proxy_data.get('city'),
                proxy_data.get('asn'),
                proxy_data.get('anonymity_level'),
                proxy_data.get('speed_ms'),
                proxy_data.get('uptime_percentage', 0.0),
                proxy_data.get('last_checked', datetime.now()),
                proxy_data.get('is_active', True)
            ))
            
            proxy_id = cursor.lastrowid
            conn.commit()
            return proxy_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_active_proxies(self, limit: int = 1000) -> List[Dict]:
        """Get all active proxies"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM proxies 
            WHERE is_active = 1 
            ORDER BY uptime_percentage DESC, speed_ms ASC
            LIMIT ?
        ''', (limit,))
        
        proxies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return proxies
    
    def get_proxies_with_filters(self, 
                                 country: Optional[str] = None,
                                 protocol: Optional[str] = None,
                                 anonymity: Optional[str] = None,
                                 min_speed: Optional[float] = None,
                                 max_speed: Optional[float] = None,
                                 min_uptime: Optional[float] = None,
                                 limit: int = 1000) -> List[Dict]:
        """Get proxies with advanced filters"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM proxies WHERE is_active = 1"
        params = []
        
        if country:
            query += " AND (country = ? OR country_code = ?)"
            params.extend([country, country])
        
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        
        if anonymity:
            query += " AND anonymity_level = ?"
            params.append(anonymity)
        
        if min_speed is not None:
            query += " AND speed_ms <= ?"
            params.append(min_speed)
        
        if max_speed is not None:
            query += " AND speed_ms >= ?"
            params.append(max_speed)
        
        if min_uptime is not None:
            query += " AND uptime_percentage >= ?"
            params.append(min_uptime)
        
        query += " ORDER BY uptime_percentage DESC, speed_ms ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        proxies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return proxies
    
    def update_proxy_status(self, proxy_id: int, status: str, speed_ms: float = None, 
                           anonymity_level: str = None, uptime_percentage: float = None):
        """Update proxy status and add to history"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update proxy
            if speed_ms is not None or anonymity_level is not None or uptime_percentage is not None:
                update_fields = []
                params = []
                
                if speed_ms is not None:
                    update_fields.append("speed_ms = ?")
                    params.append(speed_ms)
                
                if anonymity_level is not None:
                    update_fields.append("anonymity_level = ?")
                    params.append(anonymity_level)
                
                if uptime_percentage is not None:
                    update_fields.append("uptime_percentage = ?")
                    params.append(uptime_percentage)
                
                update_fields.append("last_checked = CURRENT_TIMESTAMP")
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                if status == 'valid' or status == 'active':
                    params.append(proxy_id)
                    cursor.execute(f'''
                        UPDATE proxies 
                        SET {', '.join(update_fields)}, is_active = 1
                        WHERE id = ?
                    ''', params)
                else:
                    params.append(proxy_id)
                    cursor.execute(f'''
                        UPDATE proxies 
                        SET {', '.join(update_fields)}, is_active = 0
                        WHERE id = ?
                    ''', params)
            
            # Add to history
            cursor.execute('''
                INSERT INTO proxy_history (proxy_id, status, speed_ms, anonymity_level)
                VALUES (?, ?, ?, ?)
            ''', (proxy_id, status, speed_ms, anonymity_level))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def remove_unstable_proxies(self, threshold_uptime: float = 50.0, 
                                threshold_checks: int = 5):
        """Auto-healing: Remove proxies with low uptime"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        # Find unstable proxies
        cursor.execute('''
            SELECT id, ip, port, uptime_percentage 
            FROM proxies 
            WHERE is_active = 1 
            AND uptime_percentage < ?
            AND id IN (
                SELECT proxy_id 
                FROM proxy_history 
                GROUP BY proxy_id 
                HAVING COUNT(*) >= ?
            )
        ''', (threshold_uptime, threshold_checks))
        
        unstable = cursor.fetchall()
        removed_count = 0
        
        for proxy in unstable:
            cursor.execute('''
                UPDATE proxies SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (proxy['id'],))
            removed_count += 1
            
            print(f"🔧 Auto-healing: Deactivated unstable proxy {proxy['ip']}:{proxy['port']} "
                  f"(uptime: {proxy['uptime_percentage']}%)")
        
        conn.commit()
        conn.close()
        
        return removed_count
    
    def create_cycle(self) -> int:
        """Create a new cycle record"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cycles (status) VALUES ('running')
        ''')
        
        cycle_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cycle_id
    
    def complete_cycle(self, cycle_id: int, total: int, valid: int, invalid: int,
                      avg_speed: float, avg_uptime: float):
        """Complete a cycle with statistics"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE cycles 
            SET completed_at = CURRENT_TIMESTAMP,
                total_proxies = ?,
                valid_proxies = ?,
                invalid_proxies = ?,
                avg_speed_ms = ?,
                avg_uptime = ?,
                status = 'completed'
            WHERE id = ?
        ''', (total, valid, invalid, avg_speed, avg_uptime, cycle_id))
        
        conn.commit()
        conn.close()
    
    def get_cycle_stats(self, limit: int = 10) -> List[Dict]:
        """Get recent cycle statistics"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cycles 
            WHERE status = 'completed'
            ORDER BY completed_at DESC
            LIMIT ?
        ''', (limit,))
        
        cycles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cycles
    
    def get_ml_training_data(self, limit: int = 10000) -> List[Dict]:
        """Get data for ML training with historical features"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.id, p.ip, p.port, p.protocol, p.country, p.country_code,
                p.anonymity_level, p.speed_ms, p.uptime_percentage,
                p.asn, p.city,
                strftime('%w', p.last_checked) as day_of_week,
                strftime('%H', p.last_checked) as hour_of_day,
                ph.status as historical_status,
                COUNT(ph.id) as check_count,
                AVG(ph.speed_ms) as avg_historical_speed
            FROM proxies p
            LEFT JOIN proxy_history ph ON p.id = ph.proxy_id
            GROUP BY p.id
            HAVING check_count > 0
            ORDER BY p.last_checked DESC
            LIMIT ?
        ''', (limit,))
        
        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return data
    
    def save_ml_prediction(self, proxy_id: int, predicted_score: float, 
                          actual_score: float, model_version: str, features: Dict):
        """Save ML prediction for later analysis"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ml_predictions 
            (proxy_id, predicted_score, actual_score, model_version, features_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (proxy_id, predicted_score, actual_score, model_version, 
              json.dumps(features)))
        
        conn.commit()
        conn.close()
    
    def record_metric(self, metric_name: str, metric_value: float):
        """Record a performance metric"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics (metric_name, metric_value)
            VALUES (?, ?)
        ''', (metric_name, metric_value))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Get overall system statistics"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total proxies
        cursor.execute("SELECT COUNT(*) as count FROM proxies")
        stats['total_proxies'] = cursor.fetchone()['count']
        
        # Active proxies
        cursor.execute("SELECT COUNT(*) as count FROM proxies WHERE is_active = 1")
        stats['active_proxies'] = cursor.fetchone()['count']
        
        # Average uptime
        cursor.execute("SELECT AVG(uptime_percentage) as avg FROM proxies WHERE is_active = 1")
        stats['avg_uptime'] = cursor.fetchone()['avg'] or 0
        
        # Average speed
        cursor.execute("SELECT AVG(speed_ms) as avg FROM proxies WHERE is_active = 1")
        stats['avg_speed'] = cursor.fetchone()['avg'] or 0
        
        # Country distribution
        cursor.execute('''
            SELECT country, COUNT(*) as count 
            FROM proxies 
            WHERE is_active = 1 
            GROUP BY country 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['country_distribution'] = [dict(row) for row in cursor.fetchall()]
        
        # Protocol distribution
        cursor.execute('''
            SELECT protocol, COUNT(*) as count 
            FROM proxies 
            WHERE is_active = 1 
            GROUP BY protocol
        ''')
        stats['protocol_distribution'] = [dict(row) for row in cursor.fetchall()]
        
        # Recent cycles
        cursor.execute('''
            SELECT COUNT(*) as count FROM cycles WHERE status = 'completed'
        ''')
        stats['total_cycles'] = cursor.fetchone()['count']
        
        conn.close()
        return stats
    
    def export_proxies(self, format: str = 'json', filters: Dict = None) -> str:
        """Export proxies in multiple formats"""
        proxies = self.get_proxies_with_filters(**filters) if filters else self.get_active_proxies()
        
        if format == 'json':
            import json
            return json.dumps(proxies, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            if proxies:
                writer = csv.DictWriter(output, fieldnames=proxies[0].keys())
                writer.writeheader()
                writer.writerows(proxies)
            return output.getvalue()
        
        elif format == 'yaml':
            import yaml
            return yaml.dump(proxies, default_flow_style=False, allow_unicode=True)
        
        elif format == 'txt':
            lines = []
            for p in proxies:
                lines.append(f"{p['protocol']}://{p['ip']}:{p['port']}")
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

# Initialize database on module import
if __name__ == "__main__":
    init_database()
    print("Database ready!")
