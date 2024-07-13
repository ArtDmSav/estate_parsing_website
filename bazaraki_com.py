import asyncio
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
            print(f'Connection bazaraki_com error: {e}')
            print('Retrying in 5 minutes...')
            await asyncio.sleep(300)  # Задержка в 5 минут


async def fetch_listing(session, url, msg_id, ssl_context):
    while True:
        try:
            async with session.get(f'{url}{msg_id}', ssl=ssl_context) as response:
                return await response.text(), response.status
        except ClientConnectorError as e:
            print(f'Connection bazaraki_com error: {e}')
            print('Retrying in 5 minutes...')
            await asyncio.sleep(300)  # Задержка в 5 минут


async def bazaraki_start():
    while True:
        group_id = 'bazaraki.com'
        estate_to_rent = '/real-estate-to-rent/'
        url = f'https://{group_id}'
        # short-term/    - ? need or not ?
        types_estate = ('houses/', 'apartments-flats/', 'rooms-flatmates/')

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        for type_estate in types_estate:
            async with aiohttp.ClientSession() as session:
                response_text, status_code = await fetch(session, f'{url}{estate_to_rent}{type_estate}', ssl_context)

                last_msg_id = await get_last_msg_id(f'{group_id}/{type_estate}')
                estates = []
                if status_code == 200:
                    soup = BeautifulSoup(response_text, 'html.parser')

                    listings = soup.find_all('div', class_='advert js-item-listing')

                    for listing in listings:
                        estate_data = {}

                        # Извлечение значения атрибута id
                        msg_id = int(listing.get('id')) if listing else 0

                        print(f'msg_id: {msg_id}')
                        print(f'last_msg_id: {last_msg_id}\nGroup id: {group_id}/{type_estate}')

                        if last_msg_id >= msg_id:
                            print("------- break bazaraki_com msg_id -------")
                            break

                        tag = listing.select('div.swiper-wrapper > a')
                        href = tag[0].get('href')
                        print(href)

                        msg_id_text, response_msg_id_status = await fetch_listing(session, url, href, ssl_context)

                        if response_msg_id_status != 200:
                            print("------- break status_code bazaraki_com -------", msg_id)
                            break

                        estate_data['resource'] = 2
                        # каждый тип недвижимости создаем как отдельную группу, тк иначе будет путаница с ИД объявлений
                        estate_data['group_id'] = f'{group_id}/{type_estate}'
                        estate_data['msg_id'] = msg_id
                        estate_data['url'] = f'{url}{href}'

                        soup_msg_id = BeautifulSoup(msg_id_text, 'html.parser')

                        address_span = soup_msg_id.find('span', itemprop='address')
                        address = address_span.text if address_span else 'Город не найден bazaraki_com'
                        estate_data['city'] = await city_parsing(address)

                        price_meta = soup_msg_id.find('meta', itemprop='price')
                        estate_data['price'] = int(float(price_meta.get('content'))) if price_meta else ''

                        # Find the <div> with class "js-description"
                        description_div = soup_msg_id.find('div', class_='js-description')
                        # Extract all text
                        estate_data['msg'] = description_div.get_text(separator=' ',
                                                                      strip=True) if description_div else ''

                        language_code, msg_ru, msg_en, msg_el = await translate_language(estate_data['msg'],
                                                                                         estate_data['price'])
                        estate_data['language'] = language_code
                        estate_data['msg_ru'] = msg_ru
                        estate_data['msg_en'] = msg_en
                        estate_data['msg_el'] = msg_el

                        print(f"ID: {msg_id}\nPrice: {estate_data['price']}\n"
                              f"City: {estate_data['city']}\nlanguage: {language_code}\nmsg: {estate_data['msg']}\n"
                              f"url: {estate_data['url']}\n{'-' * 20}")

                        estates.append(estate_data)
                        await asyncio.sleep(2)
                    await insert_estates_web(estates) if estates else print(f"Список пуст bazaraki_com")

                else:
                    print(f'Failed to retrieve the page bazaraki_com. Status code: {status_code}')

        print(f'---------------- pause {SLEEP / 60} min to bazaraki_com ----------------')
        await asyncio.sleep(SLEEP)
