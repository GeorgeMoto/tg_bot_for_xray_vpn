import aiosqlite as sqlite_async
import datetime
import calendar
import shutil
from contextlib import asynccontextmanager
from typing import Optional, List, Tuple

from config import PATH_TO_DB, PATH_TO_BACKUP_DB

@asynccontextmanager
async def get_db():
    """Асинхронный контекст менеджер для работы с БД"""
    async with sqlite_async.connect(PATH_TO_DB) as db:
        yield db


def format_date_for_display(date_string):
    """Конвертирует дату из формата YYYY-MM-DD в DD.MM.YYYY для отображения"""
    try:
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return date_string


def parse_user_data_from_caption(caption):
    """Извлекает данные пользователя из caption фото"""
    try:
        return caption.split("&??&")[1].split("\n")
    except (IndexError, AttributeError):
        return []


async def init_database():
    """Инициализация базы данных с новой структурой"""
    async with get_db() as db:
        # Создаем таблицу users с новой структурой
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY,
                             username
                             TEXT,
                             first_name
                             TEXT,
                             last_name
                             TEXT,
                             email_identifier
                             TEXT,
                             start_date
                             TEXT,
                             finish_date
                             TEXT,
                             status
                             INTEGER
                             DEFAULT
                             0,
                             vless_config
                             TEXT,
                             client_uuid
                             TEXT,
                             created_at
                             TIMESTAMP
                             DEFAULT
                             CURRENT_TIMESTAMP
                         )
                         """)

        await db.commit()
        print("✅ База данных инициализирована")


async def add_user_to_db(user_id: int, username: str, first_name: str, last_name: str):
    """Добавление нового пользователя в базу данных"""
    async with get_db() as db:
        await db.execute("""
                         INSERT
                         OR IGNORE INTO users 
            (id, username, first_name, last_name, email_identifier, start_date, finish_date, status, vless_config, client_uuid) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                         """, (
                             user_id, username, first_name, last_name,
                             None, "2000-01-01", "2000-01-01", 0, None, None
                         ))
        await db.commit()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    """Получение пользователя по ID"""
    async with get_db() as db:
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'email_identifier': row[4],
                    'start_date': row[5],
                    'finish_date': row[6],
                    'status': row[7],
                    'vless_config': row[8],
                    'client_uuid': row[9],
                    'created_at': row[10] if len(row) > 10 else None
                }
            return None


async def get_all_user_ids() -> List[int]:
    """Получение списка всех ID пользователей"""
    async with get_db() as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def update_user_subscription(user_id: int, client_uuid: str, vless_config: str,
                                   email_identifier: str, days: int = 30):
    """Обновление подписки пользователя (новая или продление)"""
    today = datetime.date.today().strftime('%Y-%m-%d')

    # Вычисляем дату окончания
    today_date = datetime.date.today()
    days_in_month = calendar.monthrange(today_date.year, today_date.month)[1]
    finish_date = (today_date + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    async with get_db() as db:
        await db.execute("""
                         UPDATE users
                         SET client_uuid      = ?,
                             vless_config     = ?,
                             email_identifier = ?,
                             start_date       = ?,
                             finish_date      = ?,
                             status           = 1
                         WHERE id = ?
                         """, (client_uuid, vless_config, email_identifier, today, finish_date, user_id))
        await db.commit()


async def extend_user_subscription(user_id: int, days: int = 30):
    """Продление существующей подписки"""
    user = await get_user_by_id(user_id)
    if not user:
        return False

    # Получаем текущую дату окончания
    current_finish = datetime.datetime.strptime(user['finish_date'], '%Y-%m-%d').date()

    # Если подписка еще активна, продлеваем от текущей даты окончания
    # Если истекла, продлеваем от сегодня
    start_date = max(current_finish, datetime.date.today())

    days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
    new_finish_date = (start_date + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    async with get_db() as db:
        await db.execute("""
                         UPDATE users
                         SET finish_date = ?,
                             status      = 1
                         WHERE id = ?
                         """, (new_finish_date, user_id))
        await db.commit()

    return True


async def get_user_status(user_id: int) -> bool:
    """Получение РЕАЛЬНОГО статуса подписки пользователя"""
    user = await get_user_by_id(user_id)
    if not user or user['status'] == 0:
        return False

    # Проверяем дату окончания подписки
    today = datetime.date.today().strftime('%Y-%m-%d')

    # Если подписка истекла, автоматически деактивируем
    if user['finish_date'] < today:
        await deactivate_user(user_id)
        return False

    return True


async def get_user_finish_date(user_id: int) -> Optional[str]:
    """Получение даты окончания подписки"""
    user = await get_user_by_id(user_id)
    return user['finish_date'] if user else None


async def get_payment_notice_date(user_id: int) -> Optional[str]:
    """Получение даты для напоминания об оплате (за 3 дня до окончания)"""
    finish_date_str = await get_user_finish_date(user_id)
    if not finish_date_str:
        return None

    finish_date = datetime.datetime.strptime(finish_date_str, '%Y-%m-%d').date()
    notice_date = finish_date - datetime.timedelta(days=3)
    return notice_date.strftime('%Y-%m-%d')


async def deactivate_user(user_id: int):
    """Деактивация пользователя с полной очисткой VPN данных"""
    async with get_db() as db:
        await db.execute("""
            UPDATE users 
            SET status = 0,
                client_uuid = NULL,
                email_identifier = NULL,
                vless_config = NULL
            WHERE id = ?
        """, (user_id,))
        await db.commit()


async def activate_user(user_id: int):
    """Активация пользователя"""
    async with get_db() as db:
        await db.execute("UPDATE users SET status = 1 WHERE id = ?", (user_id,))
        await db.commit()


async def get_users_for_notification() -> List[dict]:
    """Получение пользователей, которым нужно отправить напоминание об оплате"""
    today = datetime.date.today().strftime('%Y-%m-%d')

    async with get_db() as db:
        async with db.execute("""
                              SELECT id, username, first_name, finish_date
                              FROM users
                              WHERE status = 1
                                AND date (finish_date
                                  , '-3 days') = ?
                              """, (today,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'finish_date': row[3]
                }
                for row in rows
            ]


async def get_expired_users() -> List[dict]:
    """Получение пользователей с истекшей подпиской"""
    today = datetime.date.today().strftime('%Y-%m-%d')

    async with get_db() as db:
        async with db.execute("""
                              SELECT id, client_uuid, username, first_name, email_identifier
                              FROM users
                              WHERE status = 1
                                AND finish_date < ?
                              """, (today,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'client_uuid': row[1],
                    'username': row[2],
                    'first_name': row[3],
                    'email_identifier': row[4]
                }
                for row in rows
            ]


async def get_active_users_count() -> int:
    """Получение количества активных пользователей"""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE status = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_total_users_count() -> int:
    """Получение общего количества пользователей"""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def create_backup_db():
    """Создание резервной копии базы данных"""
    try:
        shutil.copy2(PATH_TO_DB, PATH_TO_BACKUP_DB)
        print("✅ Резервная копия БД создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False


async def get_user_config(user_id: int) -> Optional[str]:
    """Получение VLESS конфигурации пользователя"""
    user = await get_user_by_id(user_id)
    return user['vless_config'] if user else None


async def delete_user_config(user_id: int):
    """Удаление конфигурации пользователя (теперь дублирует deactivate_user)"""
    await deactivate_user(user_id)


# Функция для миграции старой БД к новой структуре
async def migrate_database():
    """Миграция базы данных к новой структуре"""
    async with get_db() as db:
        # Проверяем существует ли старая таблица Links
        async with db.execute("""
                              SELECT name
                              FROM sqlite_master
                              WHERE type = 'table'
                                AND name = 'Links'
                              """) as cursor:
            if await cursor.fetchone():
                print("🔄 Найдена старая таблица Links, выполняем миграцию...")

                # Удаляем старую таблицу Links (если нужны данные, сначала перенесите их)
                await db.execute("DROP TABLE IF EXISTS Links")
                await db.commit()
                print("✅ Старая таблица Links удалена")

        # Добавляем новые колонки если их нет
        try:
            await db.execute("ALTER TABLE users ADD COLUMN email_identifier TEXT")
            await db.execute("ALTER TABLE users ADD COLUMN vless_config TEXT")
            await db.execute("ALTER TABLE users ADD COLUMN client_uuid TEXT")
            await db.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            await db.commit()
            print("✅ Новые колонки добавлены")
        except:
            # Колонки уже существуют
            pass

