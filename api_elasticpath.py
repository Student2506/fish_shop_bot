import logging
import os

import requests

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_token(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit'
    }
    url = 'https://api.moltin.com/oauth/access_token'
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()


def get_catalog(url, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product_detail(url, product_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'{url}{product_id}/', headers=headers)
    response.raise_for_status()
    return response.json().get('data')


def get_fish_picture_url(id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(
        f'https://api.moltin.com/v2/files/{id}', headers=headers
    )
    response.raise_for_status()
    return response.json().get('data').get('link').get('href')


def get_cart(url, access_token, client_id='525727537'):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'{url}{client_id}', headers=headers)
    response.raise_for_status()
    return response.json()


def add_proudct_to_cart(url, product_id, quantity, access_token, client_id):
    logger.debug(
        f'{url}, {product_id}, {quantity}, {access_token}, {client_id}'
    )
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }
    logger.debug(json_data)
    response = requests.post(
        f'{url}{client_id}/items', headers=headers, json=json_data
    )
    response.raise_for_status()
    return response.json()


def remove_products_from_cart(url, cart_product_id, access_token, client_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(
        f'{url}{client_id}/items/{cart_product_id}', headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cart_products(url, access_token, client_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'{url}{client_id}/items', headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer_record(url, access_token, id, email):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'customer',
            'name': id,
            'email': email,
        }
    }
    logger.debug(json_data)
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def main():
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    client_id = os.getenv('FISH_SHOP_CLIENT_ID')

    access_token = get_token(client_id).get('access_token', None)
    logger.debug(f'access_token: {access_token}')
    goods = get_catalog('https://api.moltin.com/v2/products', access_token)
    logger.debug(f'goods: {goods}')
    cart = get_cart('https://api.moltin.com/v2/carts/', access_token)
    logger.debug(f"it's cart: {cart.get('data', None).get('id', None)}")
    cart = add_proudct_to_cart(
        'https://api.moltin.com/v2/carts/',
        'ed8f8b07-ceca-4983-bc0c-c6b5a36f1967',
        4,
        access_token
    )
    logger.debug(f'added products: {cart}')
    cart = get_cart_products('https://api.moltin.com/v2/carts/', access_token)
    logger.debug(f'cart_details: {cart}')
    product_id = cart.get('data', None)[0].get('id', None)
    cart = remove_products_from_cart(
        'https://api.moltin.com/v2/carts/', product_id, access_token
    )
    logger.debug(f'removing {cart}')


if __name__ == '__main__':
    main()
