"""
Работает с этими модулями:

python-telegram-bot==13.11
redis==4.3.0
"""
import logging
import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from textwrap import dedent

from api_elasticpath import add_proudct_to_cart, create_customer_record
from api_elasticpath import get_cart, get_cart_products, get_catalog
from api_elasticpath import get_fish_picture_url, get_product_detail
from api_elasticpath import get_token, remove_products_from_cart


_database = None
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def start(update: Update, context: CallbackContext) -> str:
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')
    access_token = get_token(client_id).get('access_token', None)
    logger.debug(f'access_token: {access_token}')
    goods = get_catalog('https://api.moltin.com/v2/products', access_token)
    logger.debug(f'goods: {goods}')
    keyboard = [[InlineKeyboardButton(
        good.get('name'), callback_data=good.get('id')
    )] for good in goods.get('data', None)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose: ', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    logger.debug(query.data)
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')
    access_token = get_token(client_id).get('access_token', None)
    fish = get_product_detail(
        'https://api.moltin.com/v2/products/',
        query.data,
        access_token
    )
    logger.debug(fish)
    price_formatted = (
        fish
        .get('meta')
        .get('display_price')
        .get('with_tax')
        .get('formatted')
    )
    fish_detail = f'''
    {fish.get('name')}

    {price_formatted} per kg
    {fish.get('meta').get('stock').get('level')}kg on stock

    {fish.get('description')}
    '''
    context.bot.delete_message(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id
    )
    context.user_data['chosen'] = query.data
    quantity_row = [
        InlineKeyboardButton(
            f'{quantity} шт.', callback_data=quantity
        ) for quantity in (1, 5, 10)
    ]
    keyboard = [quantity_row]
    keyboard.append([InlineKeyboardButton('Назад', callback_data='Back'), ])
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='Basket')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if fish.get("relationships"):
        fish_picture = (
            fish
            .get("relationships")
            .get("main_image")
            .get("data")
            .get("id")
        )
    if fish_picture:
        url = get_fish_picture_url(fish_picture, access_token)
        query.message.reply_photo(
            url, caption=dedent(fish_detail), reply_markup=reply_markup
        )
    else:
        query.message.reply_text(
            text=dedent(fish_detail), reply_markup=reply_markup
        )
    return 'HANDLE_DESCRIPTION'


def handle_description(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    good = context.user_data.get("chosen")
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')
    access_token = get_token(client_id).get('access_token', None)
    logger.debug(f'access_token: {access_token}')
    response = query.data
    logger.debug(f'handle_desc: {response}')
    logger.debug(f'handle_desc: {query}')
    logger.debug(f'handle_desc: (choses) {good}')
    if response == 'Back':
        goods = get_catalog('https://api.moltin.com/v2/products', access_token)
        logger.debug(f'goods: {goods}')
        keyboard = [[InlineKeyboardButton(
            good.get('name'), callback_data=good.get('id')
        )] for good in goods.get('data', None)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.debug(query.message)
        query.message.reply_text('Please choose: ', reply_markup=reply_markup)
        return 'HANDLE_MENU'
    elif response.isnumeric() and int(response) in (1, 5, 10):
        logger.debug(response)
        qunatity = int(response)
        cart = get_cart(
            'https://api.moltin.com/v2/carts/',
            access_token,
            str(update.effective_user.id)
        )
        logger.debug('have a cart')
        cart = add_proudct_to_cart(
            'https://api.moltin.com/v2/carts/',
            good,
            qunatity,
            access_token,
            str(update.effective_user.id)
        )
        logger.debug(f'added products: {cart}')
    else:
        logger.debug(f'elseeee {response}')
        products = get_cart_products(
            'https://api.moltin.com/v2/carts/',
            access_token,
            str(update.effective_user.id)
        )
        response = ''
        keyboard = []
        for fish in products.get('data'):
            response += fish.get('name') + '\n'
            response += fish.get('description') + '\n'
            price = fish.get('meta').get('display_price').get('with_tax')
            response += f"{price.get('unit').get('formatted')} per kg\n"
            response += (
                f"{fish.get('quantity')}kg in cart for "
                f"{price.get('value').get('formatted')}\n\n")

            logger.debug(fish)
            keyboard.append([InlineKeyboardButton(
                f"Убрать из корзины {fish.get('name')}",
                callback_data=fish.get('id')
            )])
        keyboard.append(
            [InlineKeyboardButton('В меню', callback_data='menu'), ]
        )
        keyboard.append(
            [InlineKeyboardButton('Оплата', callback_data='pay'), ]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)
        total_formatted = (
            products
            .get('meta')
            .get('display_price')
            .get('with_tax')
            .get('formatted')
        )
        response += f"Total: {total_formatted}"
        query.message.reply_text(text=response, reply_markup=reply_markup)
        logger.debug(f'elseseee2 {products}')
    return 'HANDLE_CART'


def handle_cart(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    logger.debug(f'Handle CART {query.data}')
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')
    access_token = get_token(client_id).get('access_token', None)
    if query.data in ('menu', 'Back'):
        logger.debug('going to menu')
        goods = get_catalog('https://api.moltin.com/v2/products', access_token)
        logger.debug(f'goods: {goods}')
        keyboard = [[InlineKeyboardButton(
            good.get('name'), callback_data=good.get('id')
        )] for good in goods.get('data', None)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text('Please choose: ', reply_markup=reply_markup)
        return 'HANDLE_MENU'
    elif query.data == 'Basket':
        return 'HANDLE_CART'
    elif query.data == 'pay':
        query.message.reply_text('Mail to send?')
        return 'WAITING_EMAIL'
    else:
        remove_products_from_cart(
            'https://api.moltin.com/v2/carts/',
            query.data,
            access_token,
            str(update.effective_user.id)
        )
        products = get_cart_products(
            'https://api.moltin.com/v2/carts/',
            access_token,
            str(update.effective_user.id)
        )
        response = ''
        keyboard = []
        for fish in products.get('data'):
            response += fish.get('name') + '\n'
            response += fish.get('description') + '\n'
            price = fish.get('meta').get('display_price').get('with_tax')
            response += f"{price.get('unit').get('formatted')} per kg\n"
            response += (f"{fish.get('quantity')}kg in cart for "
                         f"{price.get('value').get('formatted')}\n\n")

            logger.debug(fish)
            keyboard.append([InlineKeyboardButton(
                f"Убрать из корзины {fish.get('name')}",
                callback_data=fish.get('id')
            )])
        keyboard.append(
            [InlineKeyboardButton('В меню', callback_data='menu'), ]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)
        price_formatted = (
            products
            .get('meta')
            .get('display_price')
            .get('with_tax')
            .get('formatted')
        )
        response += f"Total: {price_formatted}"
        query.message.reply_text(text=response, reply_markup=reply_markup)
        return 'HANDLE_CART'


def waiting_email(update: Update, context: CallbackContext) -> None:
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')
    access_token = get_token(client_id).get('access_token', None)
    user_to_order = (
        f'{update.effective_user.last_name} {update.effective_user.first_name}'
    )
    logger.debug(user_to_order)
    create_customer_record(
        'https://api.moltin.com/v2/customers',
        access_token,
        user_to_order,
        users_reply
    )
    return "START"


def handle_users_reply(update: Update, context: CallbackContext) -> None:
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': waiting_email,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.error(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv("FISH_SHOP_DATABASE_PASSWORD")
        database_host = os.getenv("FISH_SHOP_DATABASE_HOST")
        database_port = os.getenv("FISH_SHOP_DATABASE_PORT")
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password
        )
    return _database


def main():
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    token = os.getenv("FISH_SHOP_TG_BOTID")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()


if __name__ == '__main__':
    main()
