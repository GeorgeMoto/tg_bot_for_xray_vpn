import uuid
import json
import asyncio
import datetime
import httpx
from py3xui import AsyncApi, Client
from config import API_HOST, API_USERNAME, API_PASSWORD, INBOUND_ID

# Проверяем есть ли настройка SSL в конфиге
try:
    from config import USE_TLS_VERIFY
except ImportError:
    USE_TLS_VERIFY = False

# Глобальная переменная для API
_api = None


async def get_api():
    """Получает или создает API экземпляр"""
    global _api
    if _api is None:
        _api = AsyncApi(API_HOST, API_USERNAME, API_PASSWORD, use_tls_verify=USE_TLS_VERIFY)
        await _api.login()
    return _api


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
    Создает VLESS клиента в панели XUI
    Возвращает: (client_uuid, email_identifier, vless_config_url) или (None, None, None)
    """
    try:
        api = await get_api()

        # Генерируем данные клиента
        client_uuid = str(uuid.uuid4())
        email_id = generate_email_identifier(user_id, username, first_name)

        # Вычисляем время истечения (30 дней от текущего времени)
        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(days=days)
        expiry_timestamp = int(expiry_time.timestamp() * 1000)

        print(f"Создаем клиента: {email_id}")
        print(f"UUID: {client_uuid}")
        print(f"Срок действия: {expiry_time}")

        # Создаем объект клиента
        new_client = Client(
            id=client_uuid,
            email=email_id,
            enable=True,
            limit_ip=3,  # До 3 устройств
            total_gb=0,  # Безлимитный трафик
            expiry_time=expiry_timestamp,
            tg_id=str(user_id),
            sub_id=""
        )

        # Добавляем клиента в inbound
        await api.client.add(INBOUND_ID, [new_client])

        # Ждем немного для синхронизации
        await asyncio.sleep(1)

        # Проверяем создался ли клиент
        if await verify_client_created(email_id):
            # Генерируем VLESS конфигурацию
            vless_url = await generate_vless_config(client_uuid, email_id)
            print(f"✅ Клиент создан: {email_id}")
            return client_uuid, email_id, vless_url
        else:
            print(f"❌ Клиент не найден после создания")
            return None, None, None

    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        return None, None, None


async def verify_client_created(email_id):
    """Проверяет создался ли клиент в панели"""
    try:
        async with httpx.AsyncClient(verify=USE_TLS_VERIFY, timeout=10) as client:
            # Авторизуемся
            await client.post(f"{API_HOST}/login", data={
                "username": API_USERNAME,
                "password": API_PASSWORD
            })

            # Получаем список inbounds
            response = await client.get(f"{API_HOST}/panel/api/inbounds/list")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    for inbound in data.get('obj', []):
                        if inbound.get('id') == INBOUND_ID:
                            settings = json.loads(inbound.get('settings', '{}'))
                            clients = settings.get('clients', [])

                            for client_data in clients:
                                if client_data.get('email') == email_id:
                                    return True
        return False
    except Exception:
        return False


async def delete_client_by_email(email_id):
    """
    Удаляет клиента из панели XUI по email
    Используется для удаления просроченных подписок
    """
    try:
        api = await get_api()

        # Находим клиента по email
        client = await api.client.get_by_email(email_id)

        if client:
            # Удаляем клиента
            result = await api.client.delete(client.email)

            if result:
                print(f"✅ Клиент удален из панели: {email_id}")
                return True
            else:
                print(f"❌ Ошибка удаления клиента: {email_id}")
                return False
        else:
            print(f"⚠️ Клиент не найден в панели: {email_id}")
            return True  # Считаем успехом, если уже нет

    except Exception as e:
        print(f"❌ Ошибка удаления клиента {email_id}: {e}")
        return False


async def extend_client_subscription(email_id, days=30):
    """
    Продлевает подписку клиента на указанное количество дней
    Используется при продлении подписки
    """
    try:
        api = await get_api()

        # Находим клиента по email
        client = await api.client.get_by_email(email_id)

        if not client:
            print(f"❌ Клиент не найден: {email_id}")
            return False

        # Вычисляем новое время истечения
        current_time = datetime.datetime.now()
        if client.expiry_time and client.expiry_time > int(current_time.timestamp() * 1000):
            # Если подписка еще активна, продлеваем от текущей даты истечения
            current_expiry = datetime.datetime.fromtimestamp(client.expiry_time / 1000)
            new_expiry_time = current_expiry + datetime.timedelta(days=days)
        else:
            # Если истекла, продлеваем от текущего времени
            new_expiry_time = current_time + datetime.timedelta(days=days)

        # Обновляем время истечения
        client.expiry_time = int(new_expiry_time.timestamp() * 1000)
        client.enable = True

        # Обновляем клиента
        result = await api.client.update(client.id, client)

        if result:
            print(f"✅ Подписка продлена для клиента: {email_id}")
            return True
        else:
            print(f"❌ Ошибка продления подписки: {email_id}")
            return False

    except Exception as e:
        print(f"❌ Ошибка продления подписки {email_id}: {e}")
        return False


async def generate_vless_config(client_uuid, email):
    """Генерирует VLESS конфигурационную ссылку"""
    try:
        api = await get_api()

        # Получаем inbound для извлечения настроек
        inbound = await api.inbound.get_by_id(INBOUND_ID)

        # Извлекаем IP из host
        import re
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', API_HOST)
        server_ip = ip_match.group(1) if ip_match else 'server-ip'

        # Получаем настройки из inbound
        port = inbound.port
        network = inbound.stream_settings.network
        security = inbound.stream_settings.security

        # Формируем базовую VLESS ссылку
        vless_url = f"vless://{client_uuid}@{server_ip}:{port}/?type={network}&security={security}#{email}"

        # Если используется reality, добавляем дополнительные параметры
        if security == "reality" and hasattr(inbound.stream_settings, 'reality_settings'):
            reality_settings = inbound.stream_settings.reality_settings
            if reality_settings:
                public_key = reality_settings.get("publicKey", "")
                server_names = reality_settings.get("serverNames", [])
                short_ids = reality_settings.get("shortIds", [])

                if public_key:
                    vless_url += f"&pbk={public_key}"
                if server_names:
                    vless_url += f"&sni={server_names[0]}"
                if short_ids:
                    vless_url += f"&sid={short_ids[0]}"

                vless_url += "&fp=firefox&spx=%2F"

        return vless_url

    except Exception as e:
        print(f"❌ Ошибка генерации VLESS конфигурации: {e}")
        return f"vless://{client_uuid}@server-ip:443/?type=tcp&security=none#{email}"


async def test_xui_connection():
    """Проверка доступности панели XUI"""
    try:
        print(f"🔗 Подключаемся к: {API_HOST}")
        print(f"🔐 SSL проверка: {'включена' if USE_TLS_VERIFY else 'отключена'}")

        api = await get_api()
        inbound = await api.inbound.get_by_id(INBOUND_ID)

        if inbound:
            print(f"✅ Найден inbound ID {INBOUND_ID}:")
            print(f"   Протокол: {inbound.protocol}")
            print(f"   Порт: {inbound.port}")
            print(f"   Клиентов: {len(inbound.settings.clients) if inbound.settings.clients else 0}")
            return True
        else:
            print(f"❌ Inbound с ID {INBOUND_ID} не найден")
            return False

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


# Функция для тестирования
async def test_xui_functions():
    """Тестирование основных функций для бота"""
    print("🔍 Тестирование упрощенных XUI функций...")

    # Тест подключения
    if not await test_xui_connection():
        print("❌ Тест не пройден: нет подключения к XUI")
        return False

    # Тест создания клиента на 30 дней
    test_user_id = 999999999
    test_username = "test_user"
    test_first_name = "Test"

    client_uuid, email_id, vless_url = await create_vless_client(
        test_user_id, test_username, test_first_name, 30  # 30 дней
    )

    if client_uuid and email_id and vless_url:
        print(f"✅ Тестовый клиент создан на 30 дней")
        print(f"Email: {email_id}")
        print(f"VLESS: {vless_url[:80]}...")

        # Тест продления на 30 дней
        if await extend_client_subscription(email_id, 30):
            print("✅ Тест продления прошел")

        # Удаляем тестового клиента
        if await delete_client_by_email(email_id):
            print("✅ Тестовый клиент удален")
    else:
        print("❌ Не удалось создать тестового клиента")

    print("✅ Все тесты завершены")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_xui_functions())
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Установите библиотеку: pip install py3xui")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")