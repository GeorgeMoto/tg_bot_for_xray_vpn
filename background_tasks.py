import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from database import get_expired_users, get_users_for_notification, deactivate_user, format_date_for_display
from ui_api import delete_client_by_email
from config import admins

# Настройка логирования для фоновых задач
logger = logging.getLogger(__name__)


async def auto_cleanup_expired_subscriptions(bot: Bot):
    """
    Автоматическая очистка истекших подписок
    Запускается каждые 12 часов
    """
    logger.info("🔍 Запуск автоматической очистки истекших подписок...")

    try:
        expired_users = await get_expired_users()

        if not expired_users:
            logger.info("📭 Нет истекших подписок для очистки")
            return

        deactivated_count = 0
        errors_count = 0

        for user in expired_users:
            try:
                # Деактивируем в БД
                await deactivate_user(user['id'])
                logger.info(f"✅ Пользователь {user['id']} деактивирован в БД")

                # Удаляем из панели XUI
                if user['email_identifier']:
                    deletion_success = await delete_client_by_email(user['email_identifier'])
                    if deletion_success:
                        logger.info(f"✅ Клиент {user['email_identifier']} удален из панели XUI")
                    else:
                        logger.warning(f"⚠️ Не удалось удалить клиента {user['email_identifier']} из панели XUI")

                deactivated_count += 1

                # Уведомляем пользователя о деактивации
                try:
                    await bot.send_message(
                        user['id'],
                        "❌ <b>Ваша подписка истекла</b>\n\n"
                        "Доступ к VPN заблокирован. Для возобновления сервиса "
                        "пожалуйста оплатите новую подписку.\n\n"
                        "По вопросам обращайтесь: @Butter_robot_supportBot"
                    )
                    logger.info(f"📤 Уведомление о деактивации отправлено пользователю {user['id']}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось отправить уведомление пользователю {user['id']}: {e}")

                # Пауза между операциями
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ Ошибка деактивации пользователя {user['id']}: {e}")
                errors_count += 1

        # Уведомляем админа о результатах
        result_message = (
            f"🧹 <b>Автоматическая очистка завершена</b>\n\n"
            f"✅ Деактивировано: {deactivated_count}\n"
            f"❌ Ошибок: {errors_count}\n"
            f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        await bot.send_message(admins["George"], result_message)
        logger.info(f"✅ Автоматическая очистка завершена: {deactivated_count} пользователей деактивировано")

    except Exception as e:
        error_message = f"❌ <b>Ошибка автоматической очистки</b>\n\n{str(e)}\n\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        await bot.send_message(admins["George"], error_message)
        logger.error(f"❌ Критическая ошибка автоматической очистки: {e}")


async def auto_send_payment_notifications(bot: Bot):
    """
    Автоматическая отправка уведомлений об истечении подписки
    Запускается каждые 24 часа в 10:00
    """
    logger.info("🔔 Запуск автоматической отправки уведомлений...")

    try:
        notification_users = await get_users_for_notification()

        if not notification_users:
            logger.info("📭 Нет пользователей для уведомления")
            return

        sent_count = 0
        errors_count = 0

        for user in notification_users:
            try:
                formatted_finish_date = format_date_for_display(user['finish_date'])

                notification_text = (
                    f"🔔 <b>Напоминание об оплате</b>\n\n"
                    f"Ваша подписка закончится <b>{formatted_finish_date}</b>.\n\n"
                    f"❗ Пожалуйста, продлите подписку в течение 3 дней, "
                    f"чтобы не потерять доступ к сервису.\n\n"
                    f"💳 Стоимость: 300 рублей на 30 дней\n"
                    f"❓ По вопросам: @Butter_robot_supportBot"
                )

                await bot.send_message(user['id'], notification_text)
                sent_count += 1
                logger.info(f"📤 Уведомление отправлено пользователю {user['id']}")

                # Пауза между отправками
                await asyncio.sleep(0.3)

            except Exception as e:
                logger.warning(f"⚠️ Ошибка отправки уведомления пользователю {user['id']}: {e}")
                errors_count += 1

        # Уведомляем админа о результатах
        result_message = (
            f"🔔 <b>Уведомления отправлены</b>\n\n"
            f"✅ Отправлено: {sent_count}\n"
            f"❌ Ошибок: {errors_count}\n"
            f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        await bot.send_message(admins["George"], result_message)
        logger.info(f"✅ Автоматические уведомления отправлены: {sent_count} пользователей")

    except Exception as e:
        error_message = f"❌ <b>Ошибка отправки уведомлений</b>\n\n{str(e)}\n\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        await bot.send_message(admins["George"], error_message)
        logger.error(f"❌ Критическая ошибка отправки уведомлений: {e}")


async def cleanup_task(bot: Bot):
    """
    Фоновая задача для очистки истекших подписок
    Выполняется каждые 12 часов
    """
    while True:
        try:
            await auto_cleanup_expired_subscriptions(bot)
            # Ждем 12 часов до следующего запуска
            await asyncio.sleep(12 * 3600)
        except Exception as e:
            logger.error(f"❌ Ошибка в cleanup_task: {e}")
            # При ошибке ждем 30 минут и повторяем
            await asyncio.sleep(1800)


async def notification_task(bot: Bot):
    """
    Фоновая задача для отправки уведомлений
    Выполняется каждые 24 часа в 10:00
    """
    while True:
        try:
            # Получаем текущее время
            now = datetime.now()

            # Если сейчас 10:00, отправляем уведомления
            if now.hour == 10 and now.minute < 5:  # 5-минутное окно
                await auto_send_payment_notifications(bot)
                # После отправки ждем до следующего дня
                await asyncio.sleep(23 * 3600)  # 23 часа
            else:
                # Проверяем каждые 5 минут, не пора ли отправлять
                await asyncio.sleep(300)  # 5 минут

        except Exception as e:
            logger.error(f"❌ Ошибка в notification_task: {e}")
            # При ошибке ждем 10 минут и повторяем
            await asyncio.sleep(600)


def start_background_tasks(bot: Bot):
    """
    Запуск всех фоновых задач
    """
    logger.info("🚀 Запуск фоновых задач...")

    # Создаем задачи
    cleanup_task_obj = asyncio.create_task(cleanup_task(bot))
    notification_task_obj = asyncio.create_task(notification_task(bot))

    logger.info("✅ Фоновые задачи запущены:")
    logger.info("   - Очистка истекших подписок: каждые 24 часа")
    logger.info("   - Уведомления об оплате: каждый день в 10:00")

    return cleanup_task_obj, notification_task_obj