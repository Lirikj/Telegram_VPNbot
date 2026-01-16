import requests
import json
import uuid
from datetime import datetime, timedelta
from config import api_base_url, ger_api_base_url, username_server, password


def generation_key(user_id, username, server_name, days):
    try:
        if server_name == '🇫🇮 Финляндия':
            api_url = api_base_url
            inbound_id = 1
        elif server_name == '🇩🇪 Германия':
            api_url = ger_api_base_url
            inbound_id = 1
        else:
            api_url = ger_api_base_url
            inbound_id = 1

        timestamp = int(datetime.now().timestamp())
        if username:
            client_email = f'VenomVPN-t.me/{username}-{timestamp}'
        else:
            client_email = f'VenomVPN-{user_id}-{timestamp}'

        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        login_data = {
            'username': username_server,
            'password': password
        }
        
        login_response = session.post(f"{api_url}/login", data=login_data, verify=False, timeout=30)
        
        if login_response.status_code != 200:
            print(f"Ошибка авторизации: {login_response.status_code}")
            return None

        inbound_response = session.get(f"{api_url}/panel/api/inbounds/get/{inbound_id}", verify=False, timeout=30)
        
        if inbound_response.status_code != 200:
            print(f"Ошибка получения inbound: {inbound_response.status_code}")
            return None
        
        try:
            inbound_data = inbound_response.json()
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON inbound: {e}")
            return None
        
        if not inbound_data.get('success'):
            print("Не удалось получить данные inbound")
            return None
        
        client_uuid = str(uuid.uuid4())
        expiry_time = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)
        
        new_client = {
            'id': client_uuid,
            'email': client_email,
            'limitIp': 3,
            'totalGB': 0,
            'expiryTime': expiry_time,
            'enable': True,
            'tgId': str(user_id),
            'subId': '',
            'reset': 0
        }
        
        client_data = {
            'id': inbound_id,
            'settings': json.dumps({
                'clients': [new_client]
            })
        }
        
        add_response = session.post(f"{api_url}/panel/api/inbounds/addClient", data=client_data, verify=False, timeout=30)
        
        if add_response.status_code == 200:
            try:
                add_result = add_response.json()
                if add_result.get('success'):
                    obj = inbound_data['obj']
                    port = obj['port']
                    
                    host = api_url.replace('http://', '').replace('https://', '').split(':')[0]
                    
                    # Получаем параметры REALITY из streamSettings
                    stream_settings = json.loads(obj.get('streamSettings', '{}'))
                    reality_settings = stream_settings.get('realitySettings', {})
                    
                    # Извлекаем необходимые параметры
                    pbk = reality_settings.get('settings', {}).get('publicKey', '')
                    sid = reality_settings.get('shortIds', [''])[0] if reality_settings.get('shortIds') else ''
                    sni = reality_settings.get('serverNames', [''])[0] if reality_settings.get('serverNames') else ''
                    fp = reality_settings.get('settings', {}).get('fingerprint', 'chrome')
                    spx = reality_settings.get('settings', {}).get('spiderX', '/')
                    
                    # Формируем полный VLESS ключ с параметрами REALITY
                    vless_config = (f"vless://{client_uuid}@{host}:{port}?"
                                f"type=tcp&security=reality&pbk={pbk}&fp={fp}"
                                f"&sni={sni}&sid={sid}&spx={spx}#{client_email}")
                    
                    return vless_config
                else:
                    print(f"Ошибка создания клиента: {add_result}")
                    return None
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга ответа добавления: {e}")
                return None
        else:
            print(f"Ошибка создания клиента: {add_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Ошибка при генерации ключа: {e}")
        return None


def extend_key(user_id, username, server_name, extra_days):
    try:
        if server_name == '🇫🇮 Финляндия':
            api_url = api_base_url
            inbound_id = 22
        else:
            api_url = ger_api_base_url
            inbound_id = 1
            
        search_patterns = []
        if username:
            search_patterns.append(f'VenomVPN-t.me/{username}')
        search_patterns.append(f'VenomVPN-{user_id}')
            
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        })
        
        login_data = {
            'username': username_server,
            'password': password
        }
        
        login_response = session.post(f"{api_url}/login", data=login_data, verify=False, timeout=30)
        
        if login_response.status_code != 200:
            return False
            
        inbound_response = session.get(f"{api_url}/panel/api/inbounds/get/{inbound_id}", verify=False, timeout=30)
        
        if inbound_response.status_code != 200:
            return False
            
        inbound_data = inbound_response.json()
        
        if not inbound_data.get('success'):
            return False
            
        obj = inbound_data['obj']
        settings = json.loads(obj.get('settings', '{}'))
        clients = settings.get('clients', [])
        
        found_client = None
        for client in clients:
            client_email = client.get('email', '')
            for pattern in search_patterns:
                if pattern in client_email:
                    found_client = client
                    break
            if found_client:
                break
        
        if not found_client:
            return False
            
        current_expiry = found_client.get('expiryTime', 0)
        additional_ms = extra_days * 24 * 60 * 60 * 1000
        now_ms = int(datetime.now().timestamp() * 1000)
        
        if current_expiry > now_ms:
            new_expiry = current_expiry + additional_ms
        else:
            new_expiry = now_ms + additional_ms
            
        found_client['expiryTime'] = new_expiry
        
        obj['settings'] = json.dumps(settings)
        
        update_data = {
            'id': inbound_id,
            'remark': obj['remark'],
            'enable': obj['enable'],
            'expiryTime': obj['expiryTime'],
            'listen': obj['listen'],
            'port': obj['port'],
            'protocol': obj['protocol'],
            'settings': obj['settings'],
            'streamSettings': obj['streamSettings'],
            'sniffing': obj['sniffing'],
            'tag': obj['tag']
        }
        
        update_response = session.post(f"{api_url}/panel/api/inbounds/update/{inbound_id}", 
                                    data=update_data, verify=False, timeout=30)
        
        if update_response.status_code == 200:
            try:
                result = update_response.json()
                return result.get('success', False)
            except json.JSONDecodeError:
                return False
        else:
            return False
        
    except Exception as e:
        return False


def delete_key(user_id, username, server_name):
    try:
        if server_name == '🇫🇮 Финляндия':
            api_url = api_base_url
            inbound_id = 22
        else:
            api_url = ger_api_base_url
            inbound_id = 1
            
        search_patterns = []
        if username:
            search_patterns.append(f'VenomVPN-t.me/{username}')
        search_patterns.append(f'VenomVPN-{user_id}')
            
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        })
        
        login_data = {
            'username': username_server,
            'password': password
        }
        
        login_response = session.post(f"{api_url}/login", data=login_data, verify=False, timeout=30)
        
        if login_response.status_code != 200:
            return False
            
        inbound_response = session.get(f"{api_url}/panel/api/inbounds/get/{inbound_id}", verify=False, timeout=30)
        
        if inbound_response.status_code != 200:
            return False
            
        inbound_data = inbound_response.json()
        
        if not inbound_data.get('success'):
            return False
            
        obj = inbound_data['obj']
        settings = json.loads(obj.get('settings', '{}'))
        clients = settings.get('clients', [])
        
        found_client = None
        for client in clients:
            client_email = client.get('email', '')
            for pattern in search_patterns:
                if pattern in client_email:
                    found_client = client
                    break
            if found_client:
                break
        
        if not found_client:
            return False
            
        # Удаляем клиента
        delete_response = session.post(f"{api_url}/panel/api/inbounds/{inbound_id}/delClient/{found_client['id']}", 
                                    verify=False, timeout=30)
        
        if delete_response.status_code == 200:
            try:
                result = delete_response.json()
                return result.get('success', False)
            except json.JSONDecodeError:
                return False
        else:
            return False
        
    except Exception as e:
        return False