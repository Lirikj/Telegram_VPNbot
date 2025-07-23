import requests
import json
import uuid
import traceback
import time
from config import api_base_url, username, password
                 

session = requests.Session()

login_url = f"{api_base_url}/login"
login_data = {
    "username": username,
    "password": password
}

def authenticate():
    try:
        login_response = session.post(login_url, json=login_data, timeout=10)
        print(f"Статус авторизации: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                print("Авторизация успешна!")
                return True
            else:
                print(f"Ошибка авторизации: {login_result}")
                return False
        else:
            print(f"Ошибка при авторизации. Статус: {login_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при авторизации: {e}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при авторизации: {e}")
        return False


def generation_key(user_id, username, days):
    if not authenticate():
        print("Ошибка авторизации")
        return None
        
    inbounds_url = f"{api_base_url}/panel/inbound/list"

    try:
        response = session.post(inbounds_url, timeout=10)
        
        if response.status_code == 200:
            if not response.text.strip():
                print("Ошибка: сервер вернул пустой ответ")
                return None
                
            try:
                response_data = response.json()
                if response_data.get('success'):
                    inbounds = response_data.get('obj', [])
                else:
                    print(f"API вернул ошибку: {response_data.get('msg', 'Неизвестная ошибка')}")
                    return None
            except json.JSONDecodeError as e:
                print(f"Ошибка при разборе JSON: {e}")
                print(f"Полный ответ сервера: {response.text}")
                return None
            
            # Ищем VLESS или VMESS подключение
            vless_inbound = None
            for inbound in inbounds:
                if inbound['protocol'] in ['vless', 'vmess']:
                    vless_inbound = inbound
                    break
            
            if vless_inbound:
                inbound_id = vless_inbound['id']
                print(f"Выбрано {vless_inbound['protocol'].upper()} подключение с ID: {inbound_id}")
            elif len(inbounds) > 0:
                inbound_id = inbounds[0]['id']
                vless_inbound = inbounds[0]
                print(f"VLESS подключение не найдено, используем первое доступное с ID: {inbound_id}")
            else:
                print(f"Ошибка: нет доступных подключений")
                return None
        else:
            print(f"Ошибка при получении списка подключений. Статус: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при подключении: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

    current_time = int(time.time() * 1000)  
    expiry_time = current_time + (days * 24 * 60 * 60 * 1000)

    client_uuid = str(uuid.uuid4())

    client_data = {
        "id": inbound_id,
        "settings": json.dumps({
            "clients": [{
                "id": client_uuid,
                "flow": "xtls-rprx-vision",
                "email": username,
                "limitIp": 1,
                "totalGB": 0,
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": user_id,
                "subId": ""
            }]
        })
    }

    add_client_url = f"{api_base_url}/panel/inbound/addClient"

    try:
        response = session.post(add_client_url, json=client_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("Клиент успешно добавлен.")
            else:
                print(f"Ошибка API при добавлении клиента: {result.get('msg', 'Неизвестная ошибка')}")
                return None
        else:
            print(f"Ошибка при добавлении клиента. Статус: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return None
    except Exception as e:
        print(f"Ошибка при добавлении клиента: {e}")
        return None

    try:
        inbound_details = vless_inbound
        server_address = "213.176.65.174"  
        server_port = inbound_details['port']

        stream_settings = inbound_details['streamSettings']
        if isinstance(stream_settings, str):
            stream_settings = json.loads(stream_settings)

        security = stream_settings.get('security', 'none')
        
        sni = ""
        if security == "tls":
            sni = stream_settings.get('tlsSettings', {}).get('serverName', '')
        elif security == "reality":
            server_names = stream_settings.get('realitySettings', {}).get('serverNames', [])
            sni = server_names[0] if server_names else 'yahoo.com'
        
        network_type = stream_settings.get('network', 'tcp')
        params = f"type={network_type}&security={security}"
        
        if security == "reality":
            reality_settings = stream_settings.get('realitySettings', {})
            reality_config = reality_settings.get('settings', {})
            
            public_key = reality_config.get('publicKey', 'RvGP3uVPDjy08TIWg4W4ub79ScoW7ta6bCMU2NmOj3c')
            params += f"&pbk={public_key}"
            
            fingerprint = reality_config.get('fingerprint', 'chrome')
            params += f"&fp={fingerprint}"
            
            if sni:
                params += f"&sni={sni}"
            
            short_ids = reality_settings.get('shortIds', ['c8'])
            if short_ids and len(short_ids) > 0:
                params += f"&sid={short_ids[0]}"
            
            spider_x = reality_config.get('spiderX', '/')
            params += f"&spx={spider_x}"
            
            params += f"&flow=xtls-rprx-vision"
        
        elif security == "tls":
            if sni:
                params += f"&sni={sni}"
            params += f"&flow=xtls-rprx-vision"
        
        else:
            params += f"&flow=xtls-rprx-vision"
        
        vless_url = f"vless://{client_uuid}@{server_address}:{server_port}?{params}#Vless%20VPN-{username}"
        
        print(f"Сгенерирован VLESS ключ для пользователя {user_id}")
        return vless_url
        
    except Exception as e:
        print(f"Ошибка при формировании VLESS URL: {e}")
        return None


def extend_user_subscription(user_id, additional_days):
    if not authenticate():
        return False
    
    try:
        inbounds_url = f"{api_base_url}/panel/inbound/list"
        response = session.post(inbounds_url, timeout=10)
        
        if response.status_code != 200:
            print(f"Ошибка при получении списка подключений: {response.status_code}")
            return False
            
        response_data = response.json()
        if not response_data.get('success'):
            print(f"API ошибка: {response_data.get('msg', 'Неизвестная ошибка')}")
            return False
            
        inbounds = response_data.get('obj', [])
        
        client_found = False
        for inbound in inbounds:
            if 'clientStats' in inbound and inbound['clientStats']:
                for client in inbound['clientStats']:
                    if str(client.get('tgId', '')) == str(user_id):
                        current_expiry = client.get('expiryTime', 0)
                        if current_expiry == 0:
                            new_expiry = int(time.time() * 1000) + (additional_days * 24 * 60 * 60 * 1000)
                        else:
                            new_expiry = current_expiry + (additional_days * 24 * 60 * 60 * 1000)
                        
                        update_data = {
                            "id": inbound['id'],
                            "settings": json.dumps({
                                "clients": [{
                                    "id": client['id'],
                                    "flow": client.get('flow', 'xtls-rprx-vision'),
                                    "email": client.get('email', ''),
                                    "limitIp": client.get('limitIp', 1),
                                    "totalGB": client.get('totalGB', 0),
                                    "expiryTime": new_expiry,
                                    "enable": True,
                                    "tgId": user_id,
                                    "subId": client.get('subId', '')
                                }]
                            })
                        }
                        
                        update_url = f"{api_base_url}/panel/inbound/updateClient/{client['id']}"
                        update_response = session.post(update_url, json=update_data)
                        
                        if update_response.status_code == 200:
                            print(f"Подписка пользователя {user_id} продлена на {additional_days} дней")
                            client_found = True
                            return True
                        else:
                            print(f"Ошибка при обновлении клиента: {update_response.status_code}")
                            print(f"Ответ: {update_response.text}")
                            return False
        
        if not client_found:
            print(f"Клиент с telegram ID {user_id} не найден на сервере")
            return False
            
    except Exception as e:
        print(f"Ошибка при продлении подписки: {e}")
        return False


def get_client_info(user_id):
    if not authenticate():
        return None
    
    try:
        inbounds_url = f"{api_base_url}/panel/inbound/list"
        response = session.post(inbounds_url, timeout=10)
        
        if response.status_code != 200:
            return None
            
        response_data = response.json()
        if not response_data.get('success'):
            return None
            
        inbounds = response_data.get('obj', [])
        
        for inbound in inbounds:
            if 'clientStats' in inbound and inbound['clientStats']:
                for client in inbound['clientStats']:
                    if str(client.get('tgId', '')) == str(user_id):
                        return {
                            'id': client['id'],
                            'email': client.get('email', ''),
                            'expiryTime': client.get('expiryTime', 0),
                            'totalGB': client.get('totalGB', 0),
                            'enable': client.get('enable', True),
                            'inbound_id': inbound['id']
                        }
        return None
        
    except Exception as e:
        print(f"Ошибка при получении информации о клиенте: {e}")
        return None