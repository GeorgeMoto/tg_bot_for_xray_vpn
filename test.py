import requests
import datetime
import json
import uuid
import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Отключаем предупреждения SSL
urllib3.disable_warnings(InsecureRequestWarning)


class XUI_Tester:
    def __init__(self, host, username, password):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # Отключаем SSL проверку

    def test_login(self):
        """Тестирование авторизации"""
        print("🔍 Тестирую авторизацию...")

        # Пробуем разные пути логина (начинаем с /mypanel/login из URL)
        login_paths = ['/mypanel/login', '/login', '/panel/login', '/xui/login']

        login_data = {
            'username': self.username,
            'password': self.password
        }

        for path in login_paths:
            url = f"{self.host}{path}"
            print(f"   Пробую: {url}")

            try:
                # Сначала получаем страницу логина для возможных CSRF токенов
                get_response = self.session.get(url, timeout=10)
                print(f"   GET статус: {get_response.status_code}")

                # Ищем CSRF токен в HTML
                csrf_token = None
                if 'csrf' in get_response.text.lower() or '_token' in get_response.text.lower():
                    import re
                    csrf_match = re.search(r'name=["\']_token["\'] value=["\']([^"\']+)["\']', get_response.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"   Найден CSRF токен: {csrf_token[:20]}...")
                        login_data['_token'] = csrf_token

                # Отправляем POST с данными авторизации
                response = self.session.post(url, data=login_data, timeout=10, allow_redirects=False)
                print(f"   POST статус: {response.status_code}")

                # Проверяем cookies после авторизации
                cookies_count = len(self.session.cookies)
                print(f"   Cookies после авторизации: {cookies_count}")

                if cookies_count > 0:
                    print(f"   Cookie names: {list(self.session.cookies.keys())}")

                if response.status_code in [200, 302]:
                    if response.status_code == 302:
                        redirect_location = response.headers.get('Location', 'неизвестно')
                        print(f"   Редирект на: {redirect_location}")

                        # Если редирект на панель - это хорошо
                        if 'panel' in redirect_location.lower():
                            print(f"✅ Успешная авторизация через: {path}")
                            return True, path

                    # Для статуса 200 проверяем содержимое
                    content = response.text.lower()
                    if 'error' in content or ('login' in content and 'panel' not in content):
                        print("   ⚠️ Возможно, неверные учетные данные или ошибка")
                        continue

                    print(f"✅ Успешная авторизация через: {path}")
                    return True, path

            except Exception as e:
                print(f"   Ошибка: {e}")

        print("❌ Авторизация не удалась ни через один путь")
        return False, None

    def test_page_access(self):
        """Проверяем, можем ли мы получить доступ к основным страницам"""
        print("\n🔍 Тестирую доступ к страницам панели...")

        # Страницы для проверки
        pages = [
            '/panel',
            '/mypanel/panel',
            '/panel/inbounds',
            '/mypanel/panel/inbounds',
            '/inbounds'
        ]

        for page in pages:
            url = f"{self.host}{page}"
            print(f"   Проверяю: {page}")

            try:
                response = self.session.get(url, timeout=10)
                print(f"   Статус: {response.status_code}")

                if response.status_code == 200:
                    content = response.text.lower()

                    if 'inbound' in content:
                        print(f"   ✅ Найдена страница с inbounds!")
                        print(f"   Первые 200 символов: {response.text[:200]}")
                        return True, page, response.text
                    elif 'login' in content:
                        print(f"   ⚠️ Перенаправлен на логин")
                    else:
                        print(f"   📄 Обычная страница")

            except Exception as e:
                print(f"   Ошибка: {e}")

        return False, None, None

    def test_api_endpoints(self):
        """Тестирование API endpoints"""
        print("\n🔍 Тестирую API endpoints...")

        # Пробуем разные API пути
        api_paths = [
            '/panel/api/inbounds/list',
            '/mypanel/panel/api/inbounds/list',
            '/api/inbounds/list',
            '/xui/api/inbounds/list'
        ]

        for path in api_paths:
            url = f"{self.host}{path}"
            print(f"   Пробую API: {url}")

            try:
                response = self.session.get(url, timeout=10)
                print(f"   Статус: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ API работает через: {path}")
                        print(f"   Структура ответа: {list(data.keys()) if isinstance(data, dict) else 'не словарь'}")
                        return True, path, data
                    except:
                        print("   Ответ не в формате JSON")
                        content_preview = response.text[:200].replace('\n', ' ').replace('\r', ' ')
                        print(f"   Первые 200 символов: {content_preview}")

                        # Проверяем, может это HTML страница авторизации?
                        if 'login' in response.text.lower() or 'username' in response.text.lower():
                            print("   ⚠️ Получена страница логина - сессия не сохранилась")
                        elif 'panel' in response.text.lower() and 'inbound' in response.text.lower():
                            print("   ⚠️ Получена HTML страница панели вместо JSON API")

            except Exception as e:
                print(f"   Ошибка: {e}")

        print("❌ API недоступен ни через один путь")
        return False, None, None

    def get_inbounds_info(self, api_data):
        """Анализ данных inbounds"""
        print("\n📋 Анализ Inbounds:")

        if not api_data.get('success'):
            print("❌ API вернул ошибку:", api_data.get('msg', 'Неизвестная ошибка'))
            return None

        inbounds = api_data.get('obj', [])
        print(f"📊 Найдено inbounds: {len(inbounds)}")

        for i, inbound in enumerate(inbounds):
            print(f"\n🔹 Inbound #{i + 1}:")
            print(f"   ID: {inbound.get('id')}")
            print(f"   Название: {inbound.get('remark', 'Без названия')}")
            print(f"   Протокол: {inbound.get('protocol')}")
            print(f"   Порт: {inbound.get('port')}")
            print(f"   Активен: {'Да' if inbound.get('enable') else 'Нет'}")

            # Анализ клиентов
            try:
                settings = json.loads(inbound.get('settings', '{}'))
                clients = settings.get('clients', [])
                print(f"   Клиентов: {len(clients)}")

                if clients:
                    print("   📋 Клиенты:")
                    for j, client in enumerate(clients[:3]):  # Показываем только первых 3
                        status = "🟢" if client.get('enable') else "🔴"
                        print(
                            f"      {status} {client.get('email', 'Без email')} (ID: {client.get('id', 'N/A')[:8]}...)")

                    if len(clients) > 3:
                        print(f"      ... и еще {len(clients) - 3} клиентов")

            except Exception as e:
                print(f"   Ошибка анализа клиентов: {e}")

        return inbounds

    def create_test_client(self, inbound_id, email="test@example.com", days=30):
        """Создание тестового клиента"""
        print(f"\n🔧 Создаю тестового клиента: {email}")

        # Исправлено: используем современный способ получения времени
        current_time = int(datetime.datetime.now().timestamp() * 1000)
        expiry_time = current_time + (86400000 * days) - 10800000  # MSK timezone

        client_id = str(uuid.uuid4())

        # Структура данных из примера
        client_data = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "id": client_id,
                    "alterId": 90,
                    "email": email,
                    "limitIp": 3,
                    "totalGB": 0,  # Безлимит
                    "expiryTime": expiry_time,
                    "enable": True,
                    "tgId": "",
                    "subId": ""
                }]
            })
        }

        headers = {"Accept": "application/json"}

        # Пробуем разные пути для добавления
        add_paths = [
            '/panel/api/inbounds/addClient',
            '/mypanel/panel/api/inbounds/addClient',
            '/api/inbounds/addClient'
        ]

        for path in add_paths:
            url = f"{self.host}{path}"
            print(f"   Пробую добавление через: {url}")

            try:
                response = self.session.post(url, headers=headers, json=client_data, timeout=10)
                print(f"   Статус: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('success'):
                            print(f"✅ Клиент создан успешно!")
                            print(f"   Email: {email}")
                            print(f"   Client ID: {client_id}")
                            print(f"   Срок: {days} дней")
                            return True, client_id, email
                        else:
                            print(f"❌ API ошибка: {result.get('msg', 'Неизвестная ошибка')}")
                    except:
                        print("   Ответ не в формате JSON")

            except Exception as e:
                print(f"   Ошибка: {e}")

        print("❌ Не удалось создать клиента")
        return False, None, None

    def generate_config_url(self, inbound_data, client_id, email):
        """Генерация конфигурационной ссылки"""
        print(f"\n🔗 Генерирую конфигурацию для {email}")

        try:
            # Извлекаем данные inbound
            protocol = inbound_data.get('protocol')
            port = inbound_data.get('port')

            # Извлекаем IP из host
            import re
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', self.host)
            server_ip = ip_match.group(1) if ip_match else 'your-server-ip'

            # Настройки потока
            stream_settings = json.loads(inbound_data.get('streamSettings', '{}'))
            network = stream_settings.get('network', 'tcp')
            security = stream_settings.get('security', 'none')

            # Генерируем URL в зависимости от протокола
            if protocol == 'vless':
                config_url = f"vless://{client_id}@{server_ip}:{port}/?type={network}&security={security}#{email}"

                # Добавляем дополнительные параметры для Reality
                if security == 'reality':
                    reality_settings = stream_settings.get('realitySettings', {})
                    if reality_settings:
                        dest = reality_settings.get('dest', '')
                        server_names = reality_settings.get('serverNames', [])
                        if server_names:
                            config_url += f"&sni={server_names[0]}"

            elif protocol == 'vmess':
                # Для VMess нужен JSON формат, потом base64
                vmess_config = {
                    "v": "2",
                    "ps": email,
                    "add": server_ip,
                    "port": str(port),
                    "id": client_id,
                    "aid": "90",
                    "net": network,
                    "type": "none",
                    "host": "",
                    "path": "",
                    "tls": security
                }

                import base64
                json_str = json.dumps(vmess_config)
                encoded = base64.b64encode(json_str.encode()).decode()
                config_url = f"vmess://{encoded}"

            else:
                config_url = f"{protocol}://{client_id}@{server_ip}:{port}#{email}"

            print(f"✅ Конфигурация создана:")
            print(f"   Протокол: {protocol}")
            print(f"   Сервер: {server_ip}:{port}")
            print(f"   Сеть: {network}")
            print(f"   Безопасность: {security}")
            print(f"   URL: {config_url}")

            return config_url

        except Exception as e:
            print(f"❌ Ошибка генерации конфигурации: {e}")
            return None

    def full_test(self):
        """Полный тест всех функций"""
        print("🚀 Запуск полного теста 3X-UI API")
        print("=" * 50)

        # 1. Тест авторизации
        login_success, login_path = self.test_login()
        if not login_success:
            print("\n❌ Тест провален: авторизация не удалась")
            return

        # 2. Проверяем доступ к страницам
        page_success, page_path, page_content = self.test_page_access()

        # 3. Тест API
        api_success, api_path, api_data = self.test_api_endpoints()
        if not api_success:
            print("\n⚠️ API недоступен, но это может быть нормально для некоторых версий")
            print("   Панель может работать только через веб-интерфейс")

            if page_success:
                print(f"✅ Веб-интерфейс доступен через: {page_path}")
                print("   Можно использовать веб-скрапинг для автоматизации")
            else:
                print("❌ Ни API, ни веб-интерфейс недоступны")
            return

        # 4. Анализ inbounds
        if api_success:
            inbounds = self.get_inbounds_info(api_data)
            if not inbounds:
                print("\n❌ Тест провален: нет доступных inbounds")
                return

            # 5. Создание тестового клиента
            first_inbound = inbounds[0]
            inbound_id = first_inbound.get('id')

            client_success, client_id, email = self.create_test_client(inbound_id)
            if not client_success:
                print("\n⚠️ Создание клиента не удалось, но это может быть нормально")
                print("   (возможно нужны дополнительные права или клиент уже существует)")

            # 6. Генерация конфигурации
            if client_success:
                config_url = self.generate_config_url(first_inbound, client_id, email)
        else:
            inbounds = None
            client_success = False

        # Итоговый отчет
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЙ ОТЧЕТ:")
        print(f"✅ Авторизация: работает ({login_path})")

        if page_success:
            print(f"✅ Веб-интерфейс: доступен ({page_path})")
        else:
            print("❌ Веб-интерфейс: недоступен")

        if api_success:
            print(f"✅ API: работает ({api_path})")
            print(f"✅ Inbounds: найдено {len(inbounds) if inbounds else 0}")
        else:
            print("❌ API: недоступен")

        if client_success:
            print("✅ Создание клиентов: работает")
            print("✅ Генерация конфигураций: работает")
            print("\n🎉 ВСЕ ФУНКЦИИ РАБОТАЮТ! Можно создавать Telegram бота через API.")
        elif api_success:
            print("⚠️ Создание клиентов: требует проверки")
            print("\n📝 API доступен, но создание клиентов нужно отладить")
        elif page_success:
            print("\n🔧 РЕКОМЕНДАЦИЯ: Использовать веб-скрапинг")
            print("   API недоступен, но веб-интерфейс работает")
            print("   Можно создать бота через автоматизацию веб-формы")
        else:
            print("\n❌ Автоматизация невозможна")
            print("   Ни API, ни веб-интерфейс недоступны")


# Запуск тестирования
if __name__ == "__main__":
    # Ваши настройки
    HOST = "https://45.153.187.138:44441"
    USERNAME = "deffer"
    PASSWORD = "Fkktuj387hbz1216"

    print("3X-UI API Tester")
    print("=" * 30)
    print(f"Сервер: {HOST}")
    print(f"Пользователь: {USERNAME}")
    print()

    # Создаем тестер и запускаем
    tester = XUI_Tester(HOST, USERNAME, PASSWORD)
    tester.full_test()