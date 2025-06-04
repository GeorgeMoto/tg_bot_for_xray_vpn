from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_keyboard_yes_or_no(text_for_yes, text_for_no, name_callback_data_yes, name_callback_data_no):
    keyboard_yes_no = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=text_for_yes, callback_data=name_callback_data_yes),
            InlineKeyboardButton(text=text_for_no, callback_data=name_callback_data_no)
        ]
    ])
    return keyboard_yes_no


def get_start_key_board():
    buttons = [
        [InlineKeyboardButton(text="🧐 О проекте", callback_data="key_information")],
        [InlineKeyboardButton(text="🚀 Как установить", callback_data="key_download")],
        [InlineKeyboardButton(text="💸️ Оплата", callback_data="key_payments")],
        [InlineKeyboardButton(text="📟 Сведения о подписке", callback_data="key_subscription")],
        [InlineKeyboardButton(text="‼️Важное", callback_data="key_important_info")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_keyboard_to_make_payment():
    buttons = [
        [
            InlineKeyboardButton(text="Произвести оплату", callback_data="key_to_make_payment"),
            InlineKeyboardButton(text="<<< Назад", callback_data="back_to_main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_control_subscription_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Продлить/оформить подписку", callback_data="key_renew_subscription")],
        [InlineKeyboardButton(text="Отмена", callback_data="key_cancel_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_main_menu():
    buttons = [
        [InlineKeyboardButton(text="<<< Назад", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_will_payment():
    buttons = [
        [InlineKeyboardButton(text="<<< Назад", callback_data="back_to_will_payment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)