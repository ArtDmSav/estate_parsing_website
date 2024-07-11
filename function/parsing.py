import asyncio
import re
from functools import partial

from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException


async def city_parsing(msg: str) -> str:
    # Write city name on 3 language (En, Gr[en transcription], Ru)
    limassol = r"(л[ие]м[ао]сс?ол[ае]?)|(l[ie]m[ae]ss?o[ls])|(n[ei]ap[oa]lis)|(lim)|(лим)"   # germasogeia
    larnaka = r"(л[ао]рнак[ае])|(l[ae]r[nv]aka)"
    pafos = r"(паф[ао]сс?е?)|(paf[ao]ss?)"
    nikosiya = r"(н[ие]к[оа]сс?и[яи])|(n[ie]k[oa]ss?ia)|(lefkosa)"

    if re.search(limassol, msg, re.IGNORECASE):
        return "limassol"
    if re.search(larnaka, msg, re.IGNORECASE):
        return "larnaka"
    if re.search(pafos, msg, re.IGNORECASE):
        return "paphos"
    if re.search(nikosiya, msg, re.IGNORECASE):
        return "nicosia"

    return "cyprus"


# tupe[language_code, msg_ru, msg_en, msg_el]
async def translate_language(msg: str) -> tuple[str, str, str, str]:
    DetectorFactory.seed = 0

    async def detect_language(msg: str) -> str:
        try:
            # Определяем язык
            lang_code = detect(msg)
            return lang_code
        except LangDetectException as e:
            print(e)
            return ''

    async def translate_ru(src: str, msg: str = msg, dest: str = 'ru') -> str:
        loop = asyncio.get_event_loop()
        translate_partial = partial(GoogleTranslator(src, dest).translate, msg)
        msg_ru = await loop.run_in_executor(None, translate_partial)
        return f'{msg_ru}\n\n____________________________\nПереведено с помощью Гугл Переводчика'

    async def translate_en(src: str, msg: str = msg, dest: str = 'en') -> str:
        loop = asyncio.get_event_loop()
        translate_partial = partial(GoogleTranslator(src, dest).translate, msg)
        msg_en = await loop.run_in_executor(None, translate_partial)
        return f'{msg_en}\n\n____________________________\nTranslated using Google Translator'

    async def translate_el(src: str, msg: str = msg, dest: str = 'el') -> str:
        loop = asyncio.get_event_loop()
        translate_partial = partial(GoogleTranslator(src, dest).translate, msg)
        msg_el = await loop.run_in_executor(None, translate_partial)
        return f'{msg_el}\n\n____________________________\nΜεταφράστηκε χρησιμοποιώντας το Google Translator'

    msg_language = await detect_language(msg)

    try:
        match msg_language:
            case 'ru':
                msg_en = await translate_en('ru')
                msg_el = await translate_el('ru')
                return msg_language, msg, msg_en, msg_el
            case 'en':
                msg_ru = await translate_ru('en')
                msg_el = await translate_el('en')
                return msg_language, msg_ru, msg, msg_el
            case 'el':
                msg_en = await translate_en('el')
                msg_ru = await translate_ru('el')
                return msg_language, msg_ru, msg_en, msg
            case _:
                return '', '', '', ''
    except RequestError:
        pass
