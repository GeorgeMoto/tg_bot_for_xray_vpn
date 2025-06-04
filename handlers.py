import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import admins, PATH_TO_BACKUP_DB
from keyboard.inline_keyboards import *
from Data import *
from database import *
from ui_api import *


# Create a Router instance
router = Router()


# Send greeting message to admin when bot started
async def on_startup(bot: Bot):
    await bot.send_message(chat_id=admins["George"], text="<b>Бот запущен</b>")
    # Инициализируем БД при запуске
    await init_database()
    # Выполняем миграцию если нужно
    await migrate_database()


@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Получаем список всех пользователей
    id_list = await get_all_user_ids()

    if not message.from_user.is_bot and user_id not in id_list:
        await add_user_to_db(user_id, username, first_name, last_name)
        await create_backup_db()

    keyboard = get_start_key_board()
    await message.answer(text=greetings, reply_markup=keyboard)


@router.message(Command("links"))
async def get_stats(message: Message):
    """Статистика для администратора"""
    if message.from_user.id in admins.values():
        active_users = await get_active_users_count()
        total_users = await get_total_users_count()
        await message.answer(
            text=f"📊 Статистика:\n"
                 f"👥 Всего пользователей: {total_users}\n"
                 f"✅ Активных подписок: {active_users}"
        )


@router.callback_query(F.data == "key_information")
async def get_information(call: CallbackQuery):
    await call.message.edit_text(information_text, reply_markup=get_back_to_main_menu())
    await call.answer(cache_time=20)


@router.callback_query(F.data == "key_download")
async def get_info_download(call: CallbackQuery):
    await call.message.edit_text(download_text, reply_markup=get_back_to_main_menu())
    await call.answer(cache_time=20)


@router.callback_query(F.data == "key_important_info")
async def get_important_info(call: CallbackQuery):
    await call.message.edit_text(important_info_text, reply_markup=get_back_to_main_menu())
    await call.answer(cache_time=20)


@router.callback_query(F.data == "key_payments")
async def get_payments_info(call: CallbackQuery):
    await call.message.edit_text(payments_text, reply_markup=get_keyboard_to_make_payment())
    await call.answer(cache_time=5)


@router.callback_query(F.data == "key_subscription")
async def get_subscription_info(call: CallbackQuery):
    user_status = await get_user_status(call.from_user.id)

    if user_status:
        finish_date = await get_user_finish_date(call.from_user.id)
        notice_date = await get_payment_notice_date(call.from_user.id)

        # Форматируем даты для отображения
        formatted_finish_date = format_date_for_display(finish_date)
        formatted_notice_date = format_date_for_display(notice_date)

        await call.message.edit_text(
            payment_notice_text.format(formatted_finish_date, formatted_notice_date),
            reply_markup=get_back_to_main_menu()
        )
        await call.answer(cache_time=10)
    else:
        await call.message.edit_text("Вы еще не оформили подписку", reply_markup=get_back_to_main_menu())
        await call.answer(cache_time=10)


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(call: CallbackQuery):
    await call.message.edit_text(text=greetings, reply_markup=get_start_key_board())
    await call.answer()


@router.message(Command("help"))
async def get_help(message: Message):
    await message.answer(text=help_text)


@router.message(Command("backup"))
async def backup(message: Message):
    if message.from_user.id in admins.values():
        keyboard = get_keyboard_yes_or_no("ДА", "НЕТ", "key_copy", "key_cancel_copy")
        await create_backup_db()
        await message.answer("Backup Запущен. Выслать копию бд?", reply_markup=keyboard)


@router.callback_query(F.data.in_({"key_copy", "key_cancel_copy"}))
async def make_backup(call: CallbackQuery):
    if call.data == "key_copy":
        await call.message.edit_text("Отправляю копию бд")
        with open(PATH_TO_BACKUP_DB, "rb") as file:
            db = file.read()
        await call.bot.send_document(admins["George"], ("copy_backup_db.db", db))
        await call.answer()
    elif call.data == "key_cancel_copy":
        await call.message.edit_text(text=greetings, reply_markup=get_start_key_board())
        await call.answer()


@router.message(F.text)
async def send_msg(message_to_send: Message):
    if message_to_send.from_user.id in admins.values():
        msg = message_to_send.text

        if msg.startswith("#"):
            msg = msg.lstrip("#")
            id_list = await get_all_user_ids()

            for id_user in id_list:
                try:
                    await message_to_send.bot.send_message(id_user, text=msg)
                    await asyncio.sleep(0.3)
                except Exception as e:
                    continue
        else:
            await message_to_send.answer(text="Для массовой рассылки необходимо чтобы текст начинался с символа '#'")


@router.message(F.video)
async def send_video(video_to_send: Message):
    if video_to_send.from_user.id in admins.values():
        id_list = await get_all_user_ids()

        for id_user in id_list:
            try:
                await video_to_send.bot.send_video(id_user, video_to_send.video.file_id)
                await asyncio.sleep(0.3)
            except Exception as e:
                continue


@router.message(F.photo)
async def send_photo(received_photo: Message):
    """Обработка скриншота оплаты"""
    keyboard = get_control_subscription_keyboard()

    user_id = received_photo.from_user.id
    username = received_photo.from_user.username
    first_name = received_photo.from_user.first_name
    last_name = received_photo.from_user.last_name

    await received_photo.bot.send_photo(
        admins["George"],
        received_photo.photo[-1].file_id,
        caption=f"Пользователь с данными: &??&{user_id}\n{username}\n{first_name}\n"
                f"{last_name}&??& \nхочет оформить/продлить подписку",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "key_renew_subscription")
async def will_subscribe(callback: CallbackQuery):
    """Обработка подтверждения оплаты администратором"""
    user_data_for_subscription = parse_user_data_from_caption(callback.message.caption)
    user_id = int(user_data_for_subscription[0])
    username = user_data_for_subscription[1] if len(user_data_for_subscription) > 1 else None
    first_name = user_data_for_subscription[2] if len(user_data_for_subscription) > 2 else None

    # Проверяем статус пользователя
    user_status = await get_user_status(user_id)

    if not user_status:
        # Новый пользователь - создаем VPN конфигурацию
        await process_new_subscription(callback, user_id, username, first_name)
    else:
        # Существующий пользователь - продлеваем подписку
        await process_subscription_renewal(callback, user_id, username, first_name)


async def process_new_subscription(callback: CallbackQuery, user_id: int, username: str, first_name: str):
    """Обработка новой подписки"""
    try:
        # Создаем клиента в панели XUI на 30 дней
        client_uuid, email_identifier, vless_config = await create_vless_client(user_id, username, first_name, 30)

        if client_uuid and vless_config and email_identifier:
            # Обновляем данные в БД
            await update_user_subscription(user_id, client_uuid, vless_config, email_identifier, 30)

            # Отправляем конфигурацию пользователю
            await callback.bot.send_message(user_id, text_for_new_link)
            await callback.bot.send_message(user_id, vless_config)

            # Уведомляем админа об успехе
            await callback.bot.send_message(
                admins["George"],
                f"✅ Пользователю {email_identifier} создана новая подписка на 30 дней\n"
                f"UUID: {client_uuid}\n"
                f"Конфигурация отправлена"
            )
        else:
            # Ошибка создания клиента
            await callback.bot.send_message(
                user_id,
                "❌ Произошла ошибка при создании подписки. "
                "Обратитесь в поддержку @Butter_robot_supportBot"
            )
            await callback.bot.send_message(
                admins["George"],
                f"❌ Ошибка создания VPN клиента для пользователя {user_id}"
            )

    except Exception as e:
        print(f"Ошибка при создании новой подписки: {e}")
        await callback.bot.send_message(
            user_id,
            "❌ Произошла техническая ошибка. "
            "Обратитесь в поддержку @Butter_robot_supportBot"
        )


async def process_subscription_renewal(callback: CallbackQuery, user_id: int, username: str, first_name: str):
    """Обработка продления подписки"""
    try:
        # Получаем данные пользователя
        user = await get_user_by_id(user_id)
        if not user:
            await callback.bot.send_message(user_id, "❌ Пользователь не найден в базе данных")
            return

        email_identifier = user['email_identifier']

        # Продлеваем подписку в панели XUI на 30 дней
        if await extend_client_subscription(email_identifier, 30):
            # Продлеваем подписку в БД
            success = await extend_user_subscription(user_id, 30)

            if success:
                # Уведомляем пользователя
                await callback.bot.send_message(user_id, "✅ Вы успешно продлили подписку на 30 дней.")

                # Уведомляем админа
                await callback.bot.send_message(
                    admins["George"],
                    f"✅ Пользователь {email_identifier} продлил подписку на 30 дней"
                )
            else:
                await callback.bot.send_message(
                    user_id,
                    "❌ Ошибка продления подписки в базе данных. "
                    "Обратитесь в поддержку @Butter_robot_supportBot"
                )
        else:
            await callback.bot.send_message(
                user_id,
                "❌ Ошибка продления подписки в панели. "
                "Обратитесь в поддержку @Butter_robot_supportBot"
            )

    except Exception as e:
        print(f"Ошибка при продлении подписки: {e}")
        await callback.bot.send_message(
            user_id,
            "❌ Произошла техническая ошибка. "
            "Обратитесь в поддержку @Butter_robot_supportBot"
        )


@router.callback_query(F.data == "key_cancel_subscription")
async def cancel_subscription(callback: CallbackQuery):
    """Отмена оформления подписки"""
    user_data_for_subscription = parse_user_data_from_caption(callback.message.caption)
    user_id = int(user_data_for_subscription[0])

    await callback.bot.send_message(
        user_id,
        "❌ Что-то пошло не так. Попробуйте повторить оплату чуть позже. "
        "Если проблема не решится то наша поддержка на связи "
        "в боте @Butter_robot_supportBot"
    )
    await callback.answer()


@router.callback_query(F.data == "key_to_make_payment")
async def will_payment(call: CallbackQuery):
    """Обработка желания оплатить"""
    user_status = await get_user_status(call.from_user.id)

    if user_status:
        finish_date = await get_user_finish_date(call.from_user.id)
        formatted_finish_date = format_date_for_display(finish_date)

        keyboard = get_keyboard_yes_or_no("Продолжить", "<<< Назад", "key_make_payment", "key_cancel_payment")
        await call.message.edit_text(
            f"Ваша подписка в настоящий момент активна. "
            f"Срок действия подписки закончится "
            f"<b>{formatted_finish_date}</b>."
            f" Продолжить оплату?",
            reply_markup=keyboard
        )
        await call.answer(cache_time=5)
    else:
        await call.message.edit_text(text=how_to_pay_text, reply_markup=get_back_to_will_payment())
        await call.answer(cache_time=5)


@router.callback_query(F.data.in_({"key_make_payment", "key_cancel_payment"}))
async def continue_payment(call: CallbackQuery):
    if call.data == "key_make_payment":
        await call.message.edit_text(how_to_pay_subscriber, reply_markup=get_back_to_will_payment())
        await call.answer(cache_time=5)
    elif call.data == "key_cancel_payment":
        await call.message.edit_text(text=payments_text, reply_markup=get_keyboard_to_make_payment())
        await call.answer(cache_time=5)


@router.callback_query(F.data == "back_to_will_payment")
async def back_to_payment_menu(call: CallbackQuery):
    await call.message.edit_text(payments_text, reply_markup=get_keyboard_to_make_payment())
    await call.answer(cache_time=5)


# Команды для администратора
@router.message(Command("users"))
async def admin_users_stats(message: Message):
    """Расширенная статистика для админа"""
    if message.from_user.id in admins.values():
        active_users = await get_active_users_count()
        total_users = await get_total_users_count()

        # Получаем пользователей для уведомлений
        notification_users = await get_users_for_notification()
        expired_users = await get_expired_users()

        stats_text = f"📊 <b>Детальная статистика:</b>\n\n" \
                     f"👥 Всего пользователей: {total_users}\n" \
                     f"✅ Активных подписок: {active_users}\n" \
                     f"🔔 Нужно уведомить: {len(notification_users)}\n" \
                     f"⏰ Истекших подписок: {len(expired_users)}"

        await message.answer(stats_text)


@router.message(Command("notify"))
async def send_payment_notifications(message: Message):
    """Отправка уведомлений об окончании подписки"""
    if message.from_user.id in admins.values():
        notification_users = await get_users_for_notification()

        if not notification_users:
            await message.answer("📭 Нет пользователей для уведомления")
            return

        sent_count = 0
        for user in notification_users:
            try:
                formatted_finish_date = format_date_for_display(user['finish_date'])
                await message.bot.send_message(
                    user['id'],
                    f"🔔 <b>Напоминание об оплате</b>\n\n"
                    f"Ваша подписка закончится <b>{formatted_finish_date}</b>.\n"
                    f"Пожалуйста, продлите подписку, чтобы не потерять доступ к сервису."
                )
                sent_count += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю {user['id']}: {e}")

        await message.answer(f"✅ Отправлено уведомлений: {sent_count}")


@router.message(Command("cleanup"))
async def cleanup_expired_users(message: Message):
    """Очистка истекших подписок"""
    if message.from_user.id in admins.values():
        expired_users = await get_expired_users()

        if not expired_users:
            await message.answer("🧹 Нет истекших подписок для очистки")
            return

        # Деактивируем пользователей и удаляем из панели XUI
        deactivated_count = 0
        for user in expired_users:
            try:
                # Деактивируем в БД
                await deactivate_user(user['id'])

                # Удаляем из панели XUI
                if user['email_identifier']:
                    await delete_client_by_email(user['email_identifier'])

                deactivated_count += 1
            except Exception as e:
                print(f"Ошибка деактивации пользователя {user['id']}: {e}")

        await message.answer(f"🧹 Деактивировано и удалено из панели: {deactivated_count} пользователей")