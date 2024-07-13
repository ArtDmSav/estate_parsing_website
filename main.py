import asyncio
import re
import ssl

import aiohttp
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup

from config.data import SLEEP
from db.connect import get_last_msg_id, insert_estates_web
from function.parsing import city_parsing, translate_language


async def fetch(session, url, ssl_context):
    while True:
        try:
            async with session.get(url, ssl=ssl_context) as response:
                return await response.text(), response.status
        except ClientConnectorError as e:
            print(f'Connection error: {e}')
            print('Retrying in 5 minutes...')
            await asyncio.sleep(300)  # Задержка в 5 минут


async def fetch_listing(session, url, msg_id, ssl_context):
    while True:
        try:
            async with session.get(f'{url}{msg_id}', ssl=ssl_context) as response:
                return await response.text(), response.status
        except ClientConnectorError as e:
            print(f'Connection error: {e}')
            print('Retrying in 5 minutes...')
            await asyncio.sleep(300)  # Задержка в 5 минут


async def main():
    while True:
        group_id = 'dom.com.cy'
        type_estate = 'type-apartment-house/'
        url = f'https://{group_id}/catalog/rent/'

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            response_text, status_code = await fetch(session, f'{url}{type_estate}', ssl_context)

            last_msg_id = await get_last_msg_id(group_id)
            estates = []
            if status_code == 200:
                soup = BeautifulSoup(response_text, 'html.parser')
                listings = soup.find_all('div', class_='search-item js-filter-search')

                for listing in listings:
                    estate_data = {}

                    msg_id_str = listing.find('span', class_='article').text
                    msg_id = int(re.search(r'\d+', msg_id_str).group())

                    print(f'msg_id: {msg_id}')
                    print(f'last_msg_id: {last_msg_id}')

                    if last_msg_id >= msg_id:
                        print("------- break msg_id -------")
                        break

                    response_msg_id_text, response_msg_id_status = await fetch_listing(session, url, msg_id,
                                                                                       ssl_context)

                    if response_msg_id_status != 200:
                        print("------- break status_code -------", response_msg_id_status)
                        print(msg_id)
                        break
                    estate_data['resource'] = 2
                    estate_data['group_id'] = group_id
                    estate_data['msg_id'] = msg_id
                    soup_msg_id = BeautifulSoup(response_msg_id_text, 'html.parser')

                    city_div = soup_msg_id.find('div', class_='col-md-5 info_block_main')
                    city_name = city_div.find('a').text if city_div else 'Город не найден'
                    estate_data['city'] = await city_parsing(city_name)

                    price_div = soup_msg_id.find('div', itemprop='offers')
                    price_span = price_div.find_all('span')[1]  # Второй <span> содержит видимую цену
                    price = int(price_span.text.replace(' ', '')) if price_span else ''
                    estate_data['price'] = price

                    description_div = soup_msg_id.find('div', itemprop='description')
                    description = description_div.find('p').text if price_span else ''
                    estate_data['msg'] = description
                    language_code, msg_ru, msg_en, msg_el = await translate_language(estate_data['msg'],
                                                                                     estate_data['price'])
                    estate_data['language'] = language_code
                    estate_data['msg_ru'] = msg_ru
                    estate_data['msg_en'] = msg_en
                    estate_data['msg_el'] = msg_el

                    estate_data['url'] = f'{url}{msg_id}'

                    print(f'Price: {price}')
                    print(f'City: {city_name}')
                    print(f'language: {language_code}')
                    print(f'msg: {description}')
                    print(f'url: {url}{msg_id}')

                    print('-' * 20)

                    estates.append(estate_data)
                    await asyncio.sleep(2)
                await insert_estates_web(estates) if estates else print(f"Список пуст = {estates}")
                print('---------------- pause 5 min ----------------')

            else:
                print(f'Failed to retrieve the page. Status code: {status_code}')

        await asyncio.sleep(SLEEP)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот был остановлен вручную")
