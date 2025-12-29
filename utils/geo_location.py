import requests
from config import FLAG_EMOJIS

def detect_location(output_signal):
    results = {'country': 'Unknown', 'isp': 'Unknown', 'ip_address': 'Unknown'}
    geo_apis = [
        {"name": "ipapi.co", "url": "https://ipapi.co/json/"},
        {"name": "FreeIPAPI", "url": "https://freeipapi.com/api/json"},
        {"name": "IPWho", "url": "https://ipwho.is/"},
    ]

    success = False
    for api in geo_apis:
        try:
            response = requests.get(api["url"], timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'org' in data and data['org']:
                results['isp'] = data['org']
            elif 'isp' in data and data['isp']:
                results['isp'] = data['isp']
            elif 'connection' in data and data['connection'].get('org'):
                results['isp'] = data['connection']['org']

            country = data.get('country_name') or data.get('country') or data.get('country_capital') or 'Unknown'
            if country != 'Unknown':
                results['country'] = country

            ip = data.get('ip') or data.get('query') or data.get('ip_address') or 'Unknown'
            if ip != 'Unknown':
                results['ip_address'] = ip

            if results['isp'] != 'Unknown' or results['country'] != 'Unknown':
                flag = FLAG_EMOJIS.get(results['country'], '🌍')
                output_signal.emit(
                    f"Location detected via {api['name']}:\n"
                    f"Country: {results['country']} {flag}\n"
                    f"ISP: {results['isp']}\n"
                    f"Public IP: {results['ip_address']}\n"
                )
                success = True
                break
        except Exception as e:
            output_signal.emit(f"{api['name']} failed, trying next...\n")

    if not success:
        output_signal.emit("All location services failed.\n")

    return results