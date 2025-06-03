import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command

from config import BOT_TOKEN, admins
from keyboard.inline_keyboards import *
from Data import *
from sql.sql_functions import *
from dt_functions.data_formatting_functions import *


# import asyncio
#
# from aiogram.filters import Command
# from aiogram.types import Message, CallbackQuery
# from aiogram.utils import exceptions
#
# from main import bot, dp
# from config import admins
# from keyboard.inline_keyboards import *
# from Data import *
# from sql.sql_functions import *
# from dt_functions.data_formatting_functions import *
#
#
# # send greening message to admin when bot started
# async def send_greeting_to_admin(dp):
#     await bot.send_message(chat_id=admins["George"], text="<b>Бот запущен</b>")
#
#
# @dp.message_handler(Command("start"))
# async def start(message: Message):
#
#     id = message.from_user.id
#     username = message.from_user.username
#     first_name = message.from_user.first_name
#     last_name = message.from_user.last_name
#     id_list = get_id_list()
#
#     if not message.from_user.is_bot and id not in id_list:
#         add_user_to_db(id, username, first_name, last_name)
#         create_backup_db()
#
#     keyboard = get_start_key_board()
#
#     await message.answer(text=greetings, reply_markup=keyboard)
#
#
# @dp.message_handler(Command("links"))
# async def get_number_of_links_(message):
#     if message.from_user.id in admins.values():
#
#         number_of_link_address = get_number_of_link_address()
#         await message.answer(text=f"В базе осталось ссылок для подключений: {number_of_link_address}")
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_information")
# async def get_information(call: CallbackQuery):
#
#     await call.message.edit_text(information_text, reply_markup=get_back_to_main_menu())
#     await call.answer(cache_time=20)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_download")
# async def get_info_download(call: CallbackQuery):
#
#     await call.message.edit_text(download_text, reply_markup=get_back_to_main_menu())
#     await call.answer(cache_time=20)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_important_info")
# async def get_important_info(call: CallbackQuery):
#
#     await call.message.edit_text(important_info_text, reply_markup=get_back_to_main_menu())
#     await call.answer(cache_time=20)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_payments")
# async def get_payments_info(call: CallbackQuery):
#
#     await call.message.edit_text(payments_text, reply_markup=get_keyboard_to_make_payment())
#     await call.answer(cache_time=5)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_subscription")
# async def get_subscription_info(call: CallbackQuery):
#     if get_status(call.from_user.id):
#
#         date = change_date_format(get_finish_date(call.from_user.id))
#         paynot = change_date_format(get_payment_notice(call.from_user.id))
#
#         await call.message.edit_text(payment_notice_text.format(date, paynot), reply_markup=get_back_to_main_menu())
#         await call.answer(cache_time=10)
#
#     else:
#
#         await call.message.edit_text("Вы еще не оформили подписку", reply_markup=get_back_to_main_menu())
#         await call.answer(cache_time=10)
#
#
# @dp.callback_query_handler(lambda call: call.data == "back_to_main_menu")
# async def back_to_main_menu(call: CallbackQuery):
#     await call.message.edit_text(text=greetings, reply_markup=get_start_key_board())
#     await bot.answer_callback_query(call.id)
#
#
# @dp.message_handler(Command("help"))
# async def get_help(message):
#     await message.answer(text=help_text)
#
#
# @dp.message_handler(Command("backup"))
# async def backup(message):
#
#     if message.from_user.id in admins.values():
#
#         keyboard = get_keyboard_yes_or_no("ДА", "НЕТ", "key_copy", "key_cancel_copy")
#         create_backup_db()
#         await message.answer("Backup Запущен. Выслать копию бд?", reply_markup=keyboard)
#
#
# @dp.callback_query_handler(lambda call: call.data in ("key_copy", "key_cancel_copy"))
# async def make_backup(call: CallbackQuery):
#
#     if call.data == "key_copy":
#         await call.message.edit_text("Отправляю копиию бд")
#         with open(PATH_TO_BACKUP_DB, "rb") as file:
#             db = file.read()
#         await bot.send_document(admins["George"], ("copy_backup_db.db", db))
#         await bot.answer_callback_query(call.id)
#
#     elif call.data == "key_cancel_copy":
#         await call.message.edit_text(text=greetings, reply_markup=get_start_key_board())
#         await bot.answer_callback_query(call.id)
#
#
# @dp.message_handler(content_types=["text"])
# async def send_msg(message_to_send):
#
#     if message_to_send.from_user.id in admins.values():
#         msg = message_to_send.text
#
#         if msg.startswith("#"):
#             msg = msg.lstrip("#")
#             id_list = get_id_list()
#
#             for id_user in id_list:
#                 try:
#                     await bot.send_message(id_user, text=msg)
#                     await asyncio.sleep(0.3)
#
#                 except exceptions.ChatNotFound:
#                     continue
#         else:
#             await message_to_send.answer(text="Для массовой рассылки необходимо чтобы текст начинался с символа '#'")
#
#
# @dp.message_handler(content_types=["video"])
# async def send_video(video_to_send):
#
#     if video_to_send.from_user.id in admins.values():
#         id_list = get_id_list()
#
#         for id_user in id_list:
#             try:
#                 await bot.send_video(id_user, video_to_send.video.file_id)
#                 await asyncio.sleep(0.3)
#
#             except exceptions.ChatNotFound:
#                 continue
#
#
# @dp.message_handler(content_types=["photo"])
# async def send_photo(received_photo):
#
#     keyboard = get_control_subscription_keyboard()
#
#     id_for_subscription = received_photo.from_user.id
#     user_name = received_photo.from_user.username
#     first_name = received_photo.from_user.first_name
#     last_name = received_photo.from_user.last_name
#
#     await bot.send_photo(admins["George"], received_photo.photo[-1].file_id,
#                          caption=f"Пользователь с даными: &??&{id_for_subscription}\n{user_name}\n{first_name}\n"
#                                  f"{last_name}&??& \nхочет оформить/продлить подписку",
#                          reply_markup=keyboard)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_renew_subscription")
# async def will_subscribe(callback: types.CallbackQuery):
#
#     user_data_for_subscription = get_users_data_from_photo(callback.message.caption)
#     id_for_subscription = int(user_data_for_subscription[0])
#
#     if not get_status(id_for_subscription):
#         update_status(id_for_subscription)
#         update_start_day(id_for_subscription)
#         set_finish_date(id_for_subscription)
#
#         link_name, link_address = get_link_to_connection()
#         update_link_address(id_for_subscription, link_address)
#         update_link_name(id_for_subscription, link_name)
#         delete_address_data(link_address)
#         await bot.send_message(id_for_subscription, text_for_new_link)
#         await bot.send_message(id_for_subscription, "{}".format(link_address))
#         await bot.send_message(admins["George"], "Пользователю с данными: \n {} \nприсвоена ссылка "
#                                                  "с именем:\n""'{}'".format(user_data_for_subscription, link_name))
#
#     elif get_status(id_for_subscription):
#         update_status(id_for_subscription)
#         update_finish_day(id_for_subscription)
#         await bot.send_message(id_for_subscription, "Вы успешно продлили подписку.")
#         await bot.send_message(admins["George"], "Пользователь с данными: \n {} \nпродлил "
#                                                  "подписку.".format(user_data_for_subscription))
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_cancel_subscription")
# async def cancel_subscription(callback: types.CallbackQuery):
#
#     user_data_for_subscription = get_users_data_from_photo(callback.message.caption)
#     id_for_subscription = int(user_data_for_subscription[0])
#
#     await bot.send_message(id_for_subscription, "Что-то пошло не так. Попробуйте повторить оплату чуть позже. "
#                                                 "Если проблема не решится то наша поддержка на связи "
#                                                 "в боте @Butter_robot_supportBot")
#     await bot.answer_callback_query(callback.id)
#
#
# @dp.callback_query_handler(lambda call: call.data == "key_to_make_payment")
# async def will_payment(call: CallbackQuery):
#
#     if get_status(call.from_user.id):
#         keyboard = get_keyboard_yes_or_no("Продолжить", "<<< Назад", "key_make_payment", "key_cancel_payment")
#         await call.message.edit_text(f"Ваша подписка в настоящий момент активна. "
#                                      f"Срок действия подписки закончится "
#                                      f"<b>{change_date_format(get_finish_date(call.from_user.id))}</b>."
#                                      f" Продолжить оплату?", reply_markup=keyboard)
#         await call.answer(cache_time=5)
#
#     else:
#         await call.message.edit_text(text=how_to_pay_text, reply_markup=get_back_to_will_payment())
#         await call.answer(cache_time=5)
#
#
# @dp.callback_query_handler(lambda call: call.data in ("key_make_payment", "key_cancel_payment"))
# async def continue_payment(call: CallbackQuery):
#
#     if call.data == "key_make_payment":
#         await call.message.edit_text(how_to_pay_subscriber, reply_markup=get_back_to_will_payment())
#         await call.answer(cache_time=5)
#
#     elif call.data == "key_cancel_payment":
#         await call.message.edit_text(text=payments_text, reply_markup=get_keyboard_to_make_payment())
#         await call.answer(cache_time=5)
#
#
# @dp.callback_query_handler(lambda call: call.data == "back_to_will_payment")
# async def back_to_payment_menu(call: CallbackQuery):
#     await call.message.edit_text(payments_text, reply_markup=get_keyboard_to_make_payment())
#     await call.answer(cache_time=5)


import asyncio

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import admins
from keyboard.inline_keyboards import *
from Data import *
from sql.sql_functions import *
from dt_functions.data_formatting_functions import *

# Create a Router instance
router = Router()

# Send greeting message to admin when bot started
async def on_startup(bot: Bot):
    await bot.send_message(chat_id=admins["George"], text="<b>Бот запущен</b>")


@router.message(Command("start"))
async def start(message: Message):
    id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    id_list = get_id_list()

    if not message.from_user.is_bot and id not in id_list:
        add_user_to_db(id, username, first_name, last_name)
        create_backup_db()

    keyboard = get_start_key_board()
    await message.answer(text=greetings, reply_markup=keyboard)


@router.message(Command("links"))
async def get_number_of_links_(message: Message):
    if message.from_user.id in admins.values():
        number_of_link_address = get_number_of_link_address()
        await message.answer(text=f"В базе осталось ссылок для подключений: {number_of_link_address}")


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
    if get_status(call.from_user.id):
        date = change_date_format(get_finish_date(call.from_user.id))
        paynot = change_date_format(get_payment_notice(call.from_user.id))

        await call.message.edit_text(payment_notice_text.format(date, paynot), reply_markup=get_back_to_main_menu())
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
        create_backup_db()
        await message.answer("Backup Запущен. Выслать копию бд?", reply_markup=keyboard)


@router.callback_query(F.data.in_({"key_copy", "key_cancel_copy"}))
async def make_backup(call: CallbackQuery):
    if call.data == "key_copy":
        await call.message.edit_text("Отправляю копиию бд")
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
            id_list = get_id_list()

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
        id_list = get_id_list()

        for id_user in id_list:
            try:
                await video_to_send.bot.send_video(id_user, video_to_send.video.file_id)
                await asyncio.sleep(0.3)
            except Exception as e:
                continue


@router.message(F.photo)
async def send_photo(received_photo: Message):
    keyboard = get_control_subscription_keyboard()

    id_for_subscription = received_photo.from_user.id
    user_name = received_photo.from_user.username
    first_name = received_photo.from_user.first_name
    last_name = received_photo.from_user.last_name

    await received_photo.bot.send_photo(
        admins["George"],
        received_photo.photo[-1].file_id,
        caption=f"Пользователь с даными: &??&{id_for_subscription}\n{user_name}\n{first_name}\n"
                f"{last_name}&??& \nхочет оформить/продлить подписку",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "key_renew_subscription")
async def will_subscribe(callback: CallbackQuery):
    user_data_for_subscription = get_users_data_from_photo(callback.message.caption)
    id_for_subscription = int(user_data_for_subscription[0])

    if not get_status(id_for_subscription):
        update_status(id_for_subscription)
        update_start_day(id_for_subscription)
        set_finish_date(id_for_subscription)

        link_name, link_address = get_link_to_connection()
        update_link_address(id_for_subscription, link_address)
        update_link_name(id_for_subscription, link_name)
        delete_address_data(link_address)
        await callback.bot.send_message(id_for_subscription, text_for_new_link)
        await callback.bot.send_message(id_for_subscription, "{}".format(link_address))
        await callback.bot.send_message(
            admins["George"],
            "Пользователю с данными: \n {} \nприсвоена ссылка с именем:\n""'{}'".format(
                user_data_for_subscription, link_name
            )
        )
    elif get_status(id_for_subscription):
        update_status(id_for_subscription)
        update_finish_day(id_for_subscription)
        await callback.bot.send_message(id_for_subscription, "Вы успешно продлили подписку.")
        await callback.bot.send_message(
            admins["George"],
            "Пользователь с данными: \n {} \nпродлил подписку.".format(user_data_for_subscription)
        )


@router.callback_query(F.data == "key_cancel_subscription")
async def cancel_subscription(callback: CallbackQuery):
    user_data_for_subscription = get_users_data_from_photo(callback.message.caption)
    id_for_subscription = int(user_data_for_subscription[0])

    await callback.bot.send_message(
        id_for_subscription,
        "Что-то пошло не так. Попробуйте повторить оплату чуть позже. "
        "Если проблема не решится то наша поддержка на связи "
        "в боте @Butter_robot_supportBot"
    )
    await callback.answer()


@router.callback_query(F.data == "key_to_make_payment")
async def will_payment(call: CallbackQuery):
    if get_status(call.from_user.id):
        keyboard = get_keyboard_yes_or_no("Продолжить", "<<< Назад", "key_make_payment", "key_cancel_payment")
        await call.message.edit_text(
            f"Ваша подписка в настоящий момент активна. "
            f"Срок действия подписки закончится "
            f"<b>{change_date_format(get_finish_date(call.from_user.id))}</b>."
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