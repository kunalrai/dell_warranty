import os
import time
import json
import csv
import requests
from datetime import datetime

# === CONFIGURATION ===
CLIENT_ID = ''
CLIENT_SECRET = ''
TOKEN_FILE = 'dell_token_cache.json'
TAGS_FILE = 'tags.txt'
CSV_FILE = 'warranty_report.csv'
TOKEN_URL = 'https://apigtwb2c.us.dell.com/auth/oauth/v2/token'
WARRANTY_URL = 'https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-entitlements'


def format_date(date_str):
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d-%b-%Y")
    except:
        return date_str

# === LOAD TAGS ===
def load_service_tags(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Service tag file '{filename}' not found.")
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


# === TOKEN HANDLING ===
def get_cached_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            if time.time() < data['expires_at']:
                return data['access_token']
    return None

def fetch_new_token():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        token_data['expires_at'] = time.time() + token_data['expires_in'] - 60
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        return token_data['access_token']
    else:
        raise Exception(f"Failed to get token: {response.status_code} {response.text}")

def get_token():
    token = get_cached_token()
    return token if token else fetch_new_token()


# === WARRANTY API CALL ===
def get_warranty(service_tags, token):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'servicetags': ','.join(service_tags)}
    response = requests.get(WARRANTY_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Warranty fetch failed: {response.status_code} {response.text}")


# === SAVE TO CSV ===
def save_warranty_to_csv(data, filename):
    rows = []
    for asset in data:
        tag = asset.get('serviceTag')
        model = asset.get('productLineDescription')
        ship_date = asset.get('shipDate')
        entitlements = asset.get('entitlements', [])
        
        # Prioritize EXTENDED over INITIAL
        extended = [e for e in entitlements if e.get('entitlementType') == 'EXTENDED']
        use_entitlements = extended if extended else entitlements
        
        for ent in use_entitlements:
            rows.append({
                'ServiceTag': tag,
                'Model': model,
                'ShipDate': ship_date,
                'EntitlementType': ent.get('entitlementType'),
                'ItemNumber': ent.get('itemNumber'),
                'StartDate': format_date(ent.get('startDate', '')),
                'EndDate': format_date(ent.get('endDate', '')),
                'ServiceLevelCode': ent.get('serviceLevelCode'),
                
            })

    with open(filename, 'w', newline='') as f:
        fieldnames = ['ServiceTag', 'Model', 'ShipDate', 'EntitlementType', 'ItemNumber',
                      'StartDate', 'EndDate', 'ServiceLevelCode']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Warranty report saved to: {filename}")


# === PRINT TO CONSOLE ===
def display_warranty(data):
    for asset in data:
        print(f"\nService Tag: {asset.get('serviceTag')}")
        print(f"Model: {asset.get('productLineDescription')}")
        print(f"Ship Date: {asset.get('shipDate')}")
        for ent in asset.get('entitlements', []):
            print(f"  {ent['entitlementType']} | {ent['startDate']} → {ent['endDate']} | {ent['serviceLevelDescription']}")


# === MAIN ===
if __name__ == '__main__':
    try:
        tags = load_service_tags(TAGS_FILE)
        token = get_token()
        warranty_data = get_warranty(tags, token)
        display_warranty(warranty_data)
        save_warranty_to_csv(warranty_data, CSV_FILE)
    except Exception as e:
        print("❌ Error:", e)
