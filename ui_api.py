import uuid
import json
import asyncio
import datetime
import httpx
import re
from config import API_HOST, API_USERNAME, API_PASSWORD, INBOUND_ID

# Проверяем есть ли настройка SSL в конфиге
try:
    from config import USE_TLS_VERIFY
except ImportError:
    USE_TLS_VERIFY = False


def generate_email_identifier(user_id, username, first_name):
    """Генерирует email идентификатор для панели XUI"""
    if username:
        return f"{user_id}_@{username.lstrip('@')}"
    elif first_name:
        return f"{user_id}_{first_name}"
    else:
        return f"{user_id}_noname"


async def create_vless_client(user_id, username, first_name, days=30):
    """
    Создает VLESS клиента в панели XUI через прямые HTTP запросы
    Возвращает: (client_uuid, email_identifier, vless_config_url) или (None, None, None)
    """
    try:
        print(f"🔍 Создаем VLESS клиента для пользователя {user_id}")

        # Генерируем данные клиента
        client_uuid = str(uuid.uuid4())
        email_id = generate_email_identifier(user_id, username, first_name)

        # Вычисляем время истечения
        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(days=days)
        expiry_timestamp = int(expiry_time.timestamp() * 1000)

        print(f"🔍 UUID: {client_uuid}")
        print(f"🔍 Email: {email_id}")
        print(f"🔍 Срок действия: {expiry_time}")

        async with httpx.AsyncClient(verify=USE_TLS_VERIFY, timeout=30) as client:
            # Авторизация
            login_data = {
                "username": API_USERNAME,
                "password": API_PASSWORD
            }
            login_response = await client.post(f"{API_HOST}/login", data=login_data)

            if login_response.status_code != 200:
                print(f"❌ Ошибка авторизации: {login_response.status_code}")
                return None, None, None

            # Получаем текущий inbound
            inbound_response = await client.get(f"{API_HOST}/panel/api/inbounds/get/{INBOUND_ID}")

            if inbound_response.status_code != 200:
                print(f"❌ Ошибка получения inbound: {inbound_response.status_code}")
                return None, None, None

            inbound_data = inbound_response.json()

            if not inbound_data.get('success'):
                print(f"❌ API вернул ошибку: {inbound_data}")
                return None, None, None

            # Парсим настройки inbound
            inbound_obj = inbound_data['obj']
            settings = json.loads(inbound_obj.get('settings', '{}'))
            clients = settings.get('clients', [])

            # Создаем объект нового клиента
            new_client = {
                "id": client_uuid,
                "email": email_id,
                "enable": True,
                "flow": "",
                "limitIp": 3,  # До 3 устройств
                "totalGB": 0,  # Безлимитный трафик
                "expiryTime": expiry_timestamp,
                "tgId": str(user_id),
                "subId": ""
            }

            # Добавляем нового клиента к существующим
            clients.append(new_client)
            settings['clients'] = clients

            # Подготавливаем данные для обновления inbound
            update_data = {
                'id': INBOUND_ID,
                'remark': inbound_obj.get('remark', ''),
                'enable': inbound_obj.get('enable', True),
                'expiryTime': inbound_obj.get('expiryTime', 0),
                'listen': inbound_obj.get('listen', ''),
                'port': inbound_obj.get('port'),
                'protocol': inbound_obj.get('protocol'),
                'settings': json.dumps(settings),
                'streamSettings': inbound_obj.get('streamSettings', ''),
                'tag': inbound_obj.get('tag', ''),
                'sniffing': inbound_obj.get('sniffing', ''),
                'allocate': inbound_obj.get('allocate', ''),
            }

            print(f"🔍 Отправляем запрос на создание клиента...")

            # Обновляем inbound с новым клиентом
            update_response = await client.post(f"{API_HOST}/panel/api/inbounds/update/{INBOUND_ID}", json=update_data)

            if update_response.status_code == 200:
                response_data = update_response.json()
                if response_data.get('success'):
                    print(f"✅ Клиент создан успешно: {email_id}")

                    # Генерируем VLESS конфигурацию
                    vless_config = await generate_vless_config_direct(inbound_obj, client_uuid, email_id)

                    return client_uuid, email_id, vless_config
                else:
                    print(f"❌ API вернул ошибку при создании: {response_data}")
                    return None, None, None
            else:
                print(f"❌ HTTP ошибка при создании: {update_response.status_code}")
                print(f"❌ Ответ: {update_response.text}")
                return None, None, None

    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


async def delete_client_by_email(email_id):
    """
    Удаляет клиента из панели XUI по email через прямые HTTP запросы
    """
    try:
        print(f"🔍 Удаляем клиента: {email_id}")

        async with httpx.AsyncClient(verify=USE_TLS_VERIFY, timeout=30) as client:
            # Авторизация
            login_data = {
                "username": API_USERNAME,
                "password": API_PASSWORD
            }
            login_response = await client.post(f"{API_HOST}/login", data=login_data)

            if login_response.status_code != 200:
                print(f"❌ Ошибка авторизации: {login_response.status_code}")
                return False

            # Получаем текущий inbound
            inbound_response = await client.get(f"{API_HOST}/panel/api/inbounds/get/{INBOUND_ID}")

            if inbound_response.status_code != 200:
                print(f"❌ Ошибка получения inbound: {inbound_response.status_code}")
                return False

            inbound_data = inbound_response.json()

            if not inbound_data.get('success'):
                print(f"❌ API вернул ошибку: {inbound_data}")
                return False

            # Парсим настройки inbound
            inbound_obj = inbound_data['obj']
            settings = json.loads(inbound_obj.get('settings', '{}'))
            clients = settings.get('clients', [])

            # Ищем и удаляем клиента
            original_count = len(clients)
            clients = [c for c in clients if c.get('email') != email_id]

            if len(clients) == original_count:
                print(f"⚠️ Клиент {email_id} не найден в панели")
                return True  # Считаем успехом, если уже нет

            settings['clients'] = clients

            # Подготавливаем данные для обновления inbound
            update_data = {
                'id': INBOUND_ID,
                'remark': inbound_obj.get('remark', ''),
                'enable': inbound_obj.get('enable', True),
                'expiryTime': inbound_obj.get('expiryTime', 0),
                'listen': inbound_obj.get('listen', ''),
                'port': inbound_obj.get('port'),
                'protocol': inbound_obj.get('protocol'),
                'settings': json.dumps(settings),
                'streamSettings': inbound_obj.get('streamSettings', ''),
                'tag': inbound_obj.get('tag', ''),
                'sniffing': inbound_obj.get('sniffing', ''),
                'allocate': inbound_obj.get('allocate', ''),
            }

            # Обновляем inbound без клиента
            update_response = await client.post(f"{API_HOST}/panel/api/inbounds/update/{INBOUND_ID}", json=update_data)

            if update_response.status_code == 200:
                response_data = update_response.json()
                if response_data.get('success'):
                    print(f"✅ Клиент удален: {email_id}")
                    return True
                else:
                    print(f"❌ API вернул ошибку при удалении: {response_data}")
                    return False
            else:
                print(f"❌ HTTP ошибка при удалении: {update_response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Ошибка удаления клиента {email_id}: {e}")
        return False


async def extend_client_subscription(client_uuid, days=30):
    """
    Продлевает подписку клиента через прямые HTTP запросы к API панели
    """
    try:
        print(f"🔍 Продлеваем подписку для UUID: {client_uuid}")

        async with httpx.AsyncClient(verify=USE_TLS_VERIFY, timeout=30) as client:
            # Авторизация
            login_data = {
                "username": API_USERNAME,
                "password": API_PASSWORD
            }
            login_response = await client.post(f"{API_HOST}/login", data=login_data)

            if login_response.status_code != 200:
                print(f"❌ Ошибка авторизации: {login_response.status_code}")
                return False

            # Получение inbound с клиентами
            inbound_response = await client.get(f"{API_HOST}/panel/api/inbounds/get/{INBOUND_ID}")

            if inbound_response.status_code != 200:
                print(f"❌ Ошибка получения inbound: {inbound_response.status_code}")
                return False

            inbound_data = inbound_response.json()

            if not inbound_data.get('success'):
                print(f"❌ API вернул ошибку: {inbound_data}")
                return False

            # Парсинг настроек inbound
            inbound_obj = inbound_data['obj']
            settings = json.loads(inbound_obj.get('settings', '{}'))
            clients = settings.get('clients', [])

            print(f"🔍 Найдено клиентов в inbound: {len(clients)}")

            # Поиск клиента по UUID
            client_found = False

            for i, client_data in enumerate(clients):
                if client_data.get('id') == client_uuid:
                    print(f"✅ Найден клиент с UUID: {client_uuid}")
                    print(f"🔍 Email: {client_data.get('email')}")
                    print(f"🔍 Текущий Expiry: {client_data.get('expiryTime')}")

                    # Вычисляем новое время истечения
                    current_time = datetime.datetime.now()
                    current_expiry_ms = client_data.get('expiryTime', 0)

                    if current_expiry_ms and current_expiry_ms > int(current_time.timestamp() * 1000):
                        # Продлеваем от текущей даты истечения
                        current_expiry = datetime.datetime.fromtimestamp(current_expiry_ms / 1000)
                        new_expiry_time = current_expiry + datetime.timedelta(days=days)
                    else:
                        # Продлеваем от текущего времени
                        new_expiry_time = current_time + datetime.timedelta(days=days)

                    new_expiry_ms = int(new_expiry_time.timestamp() * 1000)

                    # Обновляем клиента
                    clients[i]['expiryTime'] = new_expiry_ms
                    clients[i]['enable'] = True

                    print(f"🔍 Новое время истечения: {new_expiry_time}")

                    client_found = True
                    break

            if not client_found:
                print(f"❌ Клиент с UUID {client_uuid} не найден в настройках inbound")
                return False

            # Подготавливаем данные для обновления inbound
            settings['clients'] = clients

            update_data = {
                'id': INBOUND_ID,
                'remark': inbound_obj.get('remark', ''),
                'enable': inbound_obj.get('enable', True),
                'expiryTime': inbound_obj.get('expiryTime', 0),
                'listen': inbound_obj.get('listen', ''),
                'port': inbound_obj.get('port'),
                'protocol': inbound_obj.get('protocol'),
                'settings': json.dumps(settings),
                'streamSettings': inbound_obj.get('streamSettings', ''),
                'tag': inbound_obj.get('tag', ''),
                'sniffing': inbound_obj.get('sniffing', ''),
                'allocate': inbound_obj.get('allocate', ''),
            }

            print(f"🔍 Отправляем обновление inbound...")

            # Обновляем inbound
            update_response = await client.post(f"{API_HOST}/panel/api/inbounds/update/{INBOUND_ID}", json=update_data)

            if update_response.status_code == 200:
                response_data = update_response.json()
                if response_data.get('success'):
                    print(f"✅ Подписка продлена для клиента: {client_uuid}")
                    return True
                else:
                    print(f"❌ API вернул ошибку при обновлении: {response_data}")
                    return False
            else:
                print(f"❌ Ошибка HTTP при обновлении: {update_response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Ошибка продления подписки {client_uuid}: {e}")
        return False


async def generate_vless_config_direct(inbound_obj, client_uuid, email):
    """Генерирует VLESS конфигурационную ссылку напрямую из данных inbound"""
    try:
        # Извлекаем IP из host
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', API_HOST)
        server_ip = ip_match.group(1) if ip_match else 'server-ip'

        # Получаем настройки из inbound
        port = inbound_obj.get('port')
        protocol = inbound_obj.get('protocol')

        # Парсим streamSettings
        stream_settings_str = inbound_obj.get('streamSettings', '{}')
        stream_settings = json.loads(stream_settings_str) if stream_settings_str else {}

        network = stream_settings.get('network', 'tcp')
        security = stream_settings.get('security', 'none')

        # Формируем базовую VLESS ссылку БЕЗ хэша
        vless_url = f"vless://{client_uuid}@{server_ip}:{port}?type={network}&security={security}"

        # Если используется reality, добавляем дополнительные параметры
        if security == "reality":
            reality_settings = stream_settings.get('realitySettings', {})
            if reality_settings:
                public_key = reality_settings.get("publicKey", "")
                server_names = reality_settings.get("serverNames", [])
                short_ids = reality_settings.get("shortIds", [])

                # Добавляем публичный ключ (pbk) - это самый важный параметр!
                if public_key:
                    vless_url += f"&pbk={public_key}"

                # Добавляем fingerprint (используем chrome вместо firefox)
                vless_url += "&fp=chrome"

                # Добавляем server name indication
                if server_names:
                    vless_url += f"&sni={server_names[0]}"

                # Добавляем short ID
                if short_ids:
                    vless_url += f"&sid={short_ids[0]}"

                # Добавляем spider X (путь)
                vless_url += "&spx=%2F"

        # Добавляем хэш с email В КОНЦЕ
        vless_url += f"#{email}"

        print(f"✅ VLESS конфигурация сгенерирована: {vless_url}")
        return vless_url

    except Exception as e:
        print(f"❌ Ошибка генерации VLESS конфигурации: {e}")



async def check_client_sync(user_id):
    """
    Проверяет синхронизацию между БД и панелью XUI
    """
    try:
        from database import get_user_by_id

        # Получаем данные из БД
        user = await get_user_by_id(user_id)
        if not user:
            return {"status": "error", "message": "Пользователь не найден в БД"}

        client_uuid = user['client_uuid']
        email_identifier = user['email_identifier']

        if not client_uuid:
            return {"status": "error", "message": "UUID клиента отсутствует в БД"}

        print(f"🔍 Проверяем синхронизацию для пользователя {user_id}")

        async with httpx.AsyncClient(verify=USE_TLS_VERIFY, timeout=30) as client:
            # Авторизация
            login_data = {
                "username": API_USERNAME,
                "password": API_PASSWORD
            }
            login_response = await client.post(f"{API_HOST}/login", data=login_data)

            if login_response.status_code != 200:
                return {"status": "error", "message": f"Ошибка авторизации в панели: {login_response.status_code}"}

            # Получение inbound
            inbound_response = await client.get(f"{API_HOST}/panel/api/inbounds/get/{INBOUND_ID}")

            if inbound_response.status_code != 200:
                return {"status": "error", "message": f"Ошибка получения inbound: {inbound_response.status_code}"}

            inbound_data = inbound_response.json()

            if not inbound_data.get('success'):
                return {"status": "error", "message": f"API панели вернул ошибку: {inbound_data}"}

            # Поиск клиента в панели
            inbound_obj = inbound_data['obj']
            settings = json.loads(inbound_obj.get('settings', '{}'))
            clients = settings.get('clients', [])

            # Ищем клиента по UUID
            panel_client = None
            for client_data in clients:
                if client_data.get('id') == client_uuid:
                    panel_client = client_data
                    break

            if panel_client:
                # Клиент найден в панели
                current_time = datetime.datetime.now()
                expiry_ms = panel_client.get('expiryTime', 0)

                if expiry_ms:
                    expiry_time = datetime.datetime.fromtimestamp(expiry_ms / 1000)
                    is_expired = expiry_time < current_time
                else:
                    expiry_time = None
                    is_expired = True

                return {
                    "status": "synced",
                    "message": "Клиент найден в панели",
                    "db_data": {
                        "user_id": user_id,
                        "client_uuid": client_uuid,
                        "email_identifier": email_identifier,
                        "status": user['status'],
                        "finish_date": user['finish_date']
                    },
                    "panel_data": {
                        "email": panel_client.get('email'),
                        "enable": panel_client.get('enable'),
                        "expiry_time": expiry_time.strftime('%Y-%m-%d %H:%M:%S') if expiry_time else None,
                        "is_expired": is_expired,
                        "total_gb": panel_client.get('totalGB'),
                        "limit_ip": panel_client.get('limitIp')
                    }
                }
            else:
                # Клиент не найден в панели
                return {
                    "status": "not_synced",
                    "message": "Клиент не найден в панели XUI",
                    "db_data": {
                        "user_id": user_id,
                        "client_uuid": client_uuid,
                        "email_identifier": email_identifier,
                        "status": user['status'],
                        "finish_date": user['finish_date']
                    },
                    "panel_clients_count": len(clients),
                    "available_uuids": [c.get('id') for c in clients[:5]]
                }

    except Exception as e:
        return {"status": "error", "message": f"Ошибка проверки: {str(e)}"}