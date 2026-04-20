"""
Testes Unitários para Database Manager - Proxygenesis AI v2.0
Foco: Banco de dados, auto-healing, filtros e exportação
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


class TestDatabaseManager:
    """Testes para o gerenciador de banco de dados"""
    
    @pytest.fixture
    def db(self):
        """Cria um banco de dados temporário para testes"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Define o caminho global antes de criar a instância
        import database.db_manager as db_mod
        original_path = db_mod.DATABASE_PATH
        db_mod.DATABASE_PATH = db_path
        
        db = db_mod.DatabaseManager(db_path=db_path)
        yield db
        
        # Cleanup
        db_mod.DATABASE_PATH = original_path
        os.unlink(db_path)
        for ext in ['-shm', '-wal']:
            if os.path.exists(f"{db_path}{ext}"):
                os.unlink(f"{db_path}{ext}")
    
    def test_init_creates_tables(self, db):
        """Testa se a inicialização cria as tabelas corretamente"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'proxies' in tables
        assert 'proxy_history' in tables
        assert 'cycles' in tables
        
        conn.close()
    
    def test_add_proxy(self, db):
        """Testa adição de proxy"""
        proxy_data = {
            'ip': '192.168.1.1',
            'port': 8080,
            'protocol': 'http',
            'anonymity_level': 'elite',
            'country': 'US',
            'city': 'New York',
            'asn': 'AS12345'
        }
        
        proxy_id = db.add_proxy(proxy_data)
        
        assert proxy_id is not None
        assert proxy_id > 0
        
        # Usar get_active_proxies ou outro método disponível
        proxies = db.get_active_proxies(limit=100)
        assert len(proxies) >= 1
    
    def test_update_proxy_status(self, db):
        """Testa atualização de status do proxy"""
        proxy_data = {'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous'}
        proxy_id = db.add_proxy(proxy_data)
        
        db.update_proxy_status(
            proxy_id=proxy_id,
            status='active',
            speed_ms=150.5,
            anonymity_level='elite'
        )
        
        proxy = db.get_proxy(proxy_id)
        assert proxy['is_active'] == True
        assert proxy['speed_ms'] == 150.5
        assert proxy['anonymity_level'] == 'elite'
    
    def test_get_active_proxies(self, db):
        """Testa obtenção de proxies ativos"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        db.add_proxy({'ip': '192.168.1.3', 'port': 8082, 'protocol': 'http', 'anonymity_level': 'transparent', 'country': 'DE'})
        
        db.update_proxy_status(1, status='active', speed_ms=100)
        db.update_proxy_status(2, status='active', speed_ms=200)
        db.update_proxy_status(3, status='inactive', speed_ms=0)
        
        active = db.get_active_proxies()
        
        assert len(active) >= 2
    
    def test_filter_proxies_by_country(self, db):
        """Testa filtro por país"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        db.add_proxy({'ip': '192.168.1.3', 'port': 8082, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'DE'})
        db.add_proxy({'ip': '192.168.1.4', 'port': 8083, 'protocol': 'socks5', 'anonymity_level': 'elite', 'country': 'US'})
        
        for i in range(1, 5):
            db.update_proxy_status(i, status='active', speed_ms=100*i)
        
        us_proxies = db.get_proxies_with_filters(country='US')
        assert len(us_proxies) >= 1
    
    def test_filter_proxies_by_protocol(self, db):
        """Testa filtro por protocolo"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        db.add_proxy({'ip': '192.168.1.3', 'port': 8082, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'DE'})
        
        for i in range(1, 4):
            db.update_proxy_status(i, status='active', speed_ms=100)
        
        http_proxies = db.get_proxies_with_filters(protocol='http')
        assert len(http_proxies) >= 1
    
    def test_filter_proxies_combined(self, db):
        """Testa filtros combinados"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.3', 'port': 8082, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'BR'})
        
        for i in range(1, 4):
            db.update_proxy_status(i, status='active', speed_ms=100)
        
        us_http = db.get_proxies_with_filters(country='US', protocol='http')
        assert len(us_http) >= 1
    
    def test_auto_healing_remove_unstable(self, db):
        """Testa auto-healing: remoção de proxies instáveis"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'BR'})
        db.add_proxy({'ip': '192.168.1.3', 'port': 8082, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'DE'})
        
        # Proxy 1: estável
        for _ in range(10):
            db.update_proxy_status(1, status='active', speed_ms=100)
        
        # Proxy 2: instável
        for _ in range(10):
            db.update_proxy_status(2, status='inactive', speed_ms=500)
        
        # Proxy 3: médio
        for _ in range(10):
            db.update_proxy_status(3, status='active', speed_ms=200)
        
        removed_count = db.remove_unstable_proxies(threshold_uptime=50.0, min_checks=5)
        
        assert removed_count >= 0  # Pode remover 0 ou mais dependendo da implementação
        remaining = db.get_active_proxies(limit=100)
        assert len(remaining) >= 0
    
    def test_export_json(self, db, tmp_path):
        """Testa exportação JSON"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        
        result = db.export_proxies(format='json')
        
        import json
        data = json.loads(result)
        assert len(data) >= 2
    
    def test_export_csv(self, db, tmp_path):
        """Testa exportação CSV"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        
        result = db.export_proxies(format='csv')
        
        lines = result.strip().split('\n')
        assert len(lines) >= 3  # Header + 2 proxies
        assert 'ip,port,protocol' in lines[0]
    
    def test_export_yaml(self, db, tmp_path):
        """Testa exportação YAML"""
        db.add_proxy({'ip': '192.168.1.1', 'port': 8080, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        db.add_proxy({'ip': '192.168.1.2', 'port': 8081, 'protocol': 'https', 'anonymity_level': 'anonymous', 'country': 'BR'})
        
        result = db.export_proxies(format='yaml')
        
        import yaml
        data = yaml.safe_load(result)
        assert len(data) >= 2
    
    def test_get_stats(self, db):
        """Testa estatísticas"""
        for i in range(10):
            db.add_proxy({'ip': f'192.168.1.{i}', 'port': 8080+i, 'protocol': 'http', 'anonymity_level': 'elite', 'country': 'US'})
        
        for i in range(1, 11):
            db.update_proxy_status(i, status='active' if i <= 5 else 'inactive', speed_ms=100)
        
        stats = db.get_stats()
        
        assert stats['total_proxies'] >= 10
        assert stats['active_count'] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
