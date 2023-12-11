from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import logging
import requests
from bs4 import BeautifulSoup
import re

API_TOKEN = '6607950034:AAH1Uqqj6XIxCvkmuPtX7dVfRWmlHIinGbs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

url_man = 'https://lacoste.ru/catalog/obuv-muzhchiny/'
url_woman = 'https://lacoste.ru/catalog/obuv-zhensh/'

response_man = requests.get(url_man)
response_woman = requests.get(url_woman)

if response_man.status_code == 200:

    soup = BeautifulSoup(response_man.text, 'html.parser')
    pattern_images = re.compile(r'//lacoste\.ru/upload/resize_cache/catalog/\d+_\d+_\d+/(\w+)(?:\.\d+)?\.jpg')
    images = soup.find_all('img', attrs={'src': pattern_images})
    names = soup.find_all('a', attrs={'class': 'nl-product__name'})
    prices = soup.find_all('span', attrs={'class': 'nl-product__price'})
    urls = soup.find_all('a', attrs={'class': 'nl-product__img'})
    product_urls = [f"https://lacoste.ru{url['href']}" for url in urls]
    product_names = [name.get_text(strip=True) for name in names]
    image_src_list = [f"https:{img['src']}" for img in images]
    product_images = image_src_list[0::6]
    product_prices = [price.get_text(strip=True) for price in prices]
    man_catalog = []

    for name, image, price, url in zip(product_names, product_images, product_prices, product_urls):
        product_info = {'name': name, 'image': image, 'price': price, 'url': url}
        man_catalog.append(product_info)

else:
    print(f"Failed to retrieve the page. Status code: {response_man.status_code}")

if response_woman.status_code == 200:
    soup = BeautifulSoup(response_woman.text, 'html.parser')
    pattern_images = re.compile(r'//lacoste\.ru/upload/resize_cache/catalog/\d+_\d+_\d+/(\w+)(?:\.\d+)?\.jpg')
    images = soup.find_all('img', attrs={'src': pattern_images})
    names = soup.find_all('a', attrs={'class': 'nl-product__name'})
    prices = soup.find_all('span', attrs={'class': 'nl-product__price'})
    urls = soup.find_all('a', attrs={'class': 'nl-product__img'})
    product_urls = [f"https://lacoste.ru{url['href']}" for url in urls]
    product_names = [name.get_text(strip=True) for name in names]
    image_src_list = [f"https:{img['src']}" for img in images]
    product_images = image_src_list[0::6]
    product_prices = [price.get_text(strip=True) for price in prices]
    woman_catalog = []

    for name, image, price, url in zip(product_names, product_images, product_prices, product_urls):
        product_info = {'name': name, 'image': image, 'price': price, 'url': url}
        woman_catalog.append(product_info)

else:
    print(f"Failed to retrieve the page. Status code: {response_woman.status_code}")

current_man_product_index = 0
current_woman_product_index = 0

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    button_man_shoes = types.InlineKeyboardButton(text="Мужская обувь", callback_data='man_shoes')
    button_woman_shoes = types.InlineKeyboardButton(text="Женская обувь", callback_data='woman_shoes')
    keyboard.add(button_man_shoes, button_woman_shoes)
    await message.answer(f"Добрый день! \nВыберите категорию товара", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'man_shoes')
async def show_man_first_product(callback_query: types.CallbackQuery):
    global current_man_product_index
    await show_product(callback_query, man_catalog, current_man_product_index)
    current_man_product_index = 0

@dp.callback_query_handler(lambda c: c.data == 'woman_shoes')
async def show_woman_first_product(callback_query: types.CallbackQuery):
    global current_woman_product_index
    await show_product(callback_query, woman_catalog, current_woman_product_index)
    current_woman_product_index = 0

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def return_to_main_menu(callback_query: types.CallbackQuery):
    await start(callback_query.message)

@dp.callback_query_handler(lambda c: c.data in ['back', 'next'])
async def handle_navigation_buttons(callback_query: types.CallbackQuery):
    global current_man_product_index, current_woman_product_index

    catalog = man_catalog if 'man' in callback_query.data else woman_catalog

    if callback_query.data == 'back':
        current_index = (
            current_man_product_index if 'man' in callback_query.data else current_woman_product_index
        )
        current_index = max(0, current_index - 1)
    elif callback_query.data == 'next':
        current_index = (
            current_man_product_index if 'man' in callback_query.data else current_woman_product_index
        )
        current_index = min(len(catalog) - 1, current_index + 1)

    if 'man' in callback_query.data:
        current_man_product_index = current_index
    else:
        current_woman_product_index = current_index

    await show_product(callback_query, catalog, current_index)

async def show_product(callback_query: types.CallbackQuery, catalog, current_index):
    product = catalog[current_index]

    markup = InlineKeyboardMarkup(row_width=3)
    button_url = types.InlineKeyboardButton("Перейти к товару", url=product['url'])
    button_main_menu = types.InlineKeyboardButton("Главное меню", callback_data='main_menu')
    button_back = types.InlineKeyboardButton("Назад", callback_data='back')
    button_next = types.InlineKeyboardButton("Далее", callback_data='next')

    markup.add(button_url)
    markup.row(button_main_menu)
    markup.row(button_back, button_next)

    await bot.send_photo(
        callback_query.from_user.id, photo=product['image'], caption=f"{product['name']}\n{product['price']}", reply_markup=markup
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)