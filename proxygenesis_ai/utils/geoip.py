"""
GeoIP utilities for proxy geolocation and ASN lookup
"""

import socket
import struct
import json
from typing import Optional, Dict
from pathlib import Path

class GeoIPManager:
    """Manage geolocation lookups for proxies"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.geoip_db = None
        
    def ip_to_int(self, ip: str) -> int:
        """Convert IP address to integer"""
        try:
            return struct.unpack("!I", socket.inet_aton(ip))[0]
        except:
            return 0
    
    def get_location_from_ip(self, ip: str) -> Dict:
        """Get location information from IP address"""
        # Free IP geolocation API fallback
        try:
            import requests
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'asn': f"AS{data.get('as', '').split(' ')[0]}" if data.get('as') else None
                    }
        except Exception as e:
            pass
        
        # Return default if lookup fails
        return {
            'country': 'Unknown',
            'country_code': 'XX',
            'city': 'Unknown',
            'asn': None
        }
    
    def batch_geolocate(self, proxies: list, max_concurrent: int = 10) -> list:
        """Geolocate multiple proxies with rate limiting"""
        import concurrent.futures
        import time
        
        results = []
        
        def geolocate_proxy(proxy):
            ip = proxy.get('ip')
            if ip:
                location = self.get_location_from_ip(ip)
                proxy.update(location)
                time.sleep(0.1)  # Rate limiting
            return proxy
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            results = list(executor.map(geolocate_proxy, proxies))
        
        return results


def enrich_proxy_with_geo(proxy_data: Dict) -> Dict:
    """Enrich proxy data with geolocation information"""
    geo_manager = GeoIPManager()
    
    if 'ip' in proxy_data:
        location = geo_manager.get_location_from_ip(proxy_data['ip'])
        proxy_data.update(location)
    
    return proxy_data


if __name__ == "__main__":
    # Test geolocation
    geo = GeoIPManager()
    
    test_ips = ['8.8.8.8', '1.1.1.1', '185.199.108.153']
    
    for ip in test_ips:
        print(f"\n🌍 Testing IP: {ip}")
        location = geo.get_location_from_ip(ip)
        print(f"   Country: {location.get('country')} ({location.get('country_code')})")
        print(f"   City: {location.get('city')}")
        print(f"   ASN: {location.get('asn')}")
