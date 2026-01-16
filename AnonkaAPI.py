import requests
import time

SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=2
)
SESSION.mount('http://', adapter)
SESSION.mount('https://', adapter)

def check_premium(user_id, max_retries=2):
    for attempt in range(max_retries):
        try:
            url = f"http://API_addres/check_premium/{user_id}"
            
            response = SESSION.get(
                url, 
                timeout=(3, 10),  
                headers={'Connection': 'close'}
            )
            
            if response.status_code == 200:
                is_premium = response.json().get("premium", False)
                return is_premium
            else:
                print(f"API статус {response.status_code}, попытка {attempt + 1}/{max_retries}")
                
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
            print(f"Таймаут API (попытка {attempt + 1}): {e}")
        except requests.RequestException as e:
            print(f"Ошибка API (попытка {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            time.sleep(1)
    
    print(f"API недоступен, возвращаем False для пользователя {user_id}")
    return False


def activate_premium(user_id, type):
    try:
        url = f"http://API_addres/activate/{user_id}/{type}/Memodelrulet"

        response = SESSION.get(
            url,
            timeout=(3, 10),
            headers={'Connection': 'close'}
        )

        if response.status_code == 200:
            return True
        else:
            print(f"Ошибка активации премиума, статус {response.status_code}")
            return False 
        
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
        print(f"Таймаут при активации премиума: {e}")
        return False
    except requests.RequestException as e:
        print(f"Ошибка при активации премиума: {e}")
        return False
    


