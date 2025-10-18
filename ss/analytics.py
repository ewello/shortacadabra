import requests
import re
from user_agents import parse


def get_geolocation(ip_address):
    """Get geolocation data from IP address using ipapi.co (free tier)"""
    try:
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            return {
                'country': 'Local',
                'region': 'Local',
                'city': 'Local',
                'latitude': None,
                'longitude': None
            }
        
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country_name', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude')
            }
    except Exception:
        pass
    
    return {
        'country': 'Unknown',
        'region': 'Unknown', 
        'city': 'Unknown',
        'latitude': None,
        'longitude': None
    }


def parse_user_agent(user_agent_string):
    """Parse user agent string to extract browser, OS, and device info"""
    try:
        if not user_agent_string:
            return {'browser': 'Unknown', 'os': 'Unknown', 'device_type': 'Unknown'}
        
        user_agent = parse(user_agent_string)
        
        # Determine device type
        device_type = 'desktop'
        if user_agent.is_mobile:
            device_type = 'mobile'
        elif user_agent.is_tablet:
            device_type = 'tablet'
        
        return {
            'browser': user_agent.browser.family if user_agent.browser else 'Unknown',
            'os': user_agent.os.family if user_agent.os else 'Unknown',
            'device_type': device_type
        }
    except Exception:
        return {'browser': 'Unknown', 'os': 'Unknown', 'device_type': 'Unknown'}


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
