import asyncio

from bazaraki_com import bazaraki_start
from dom_com_cy import dom_start


async def main():
    # Запускаем обе функции параллельно
    await asyncio.gather(
        dom_start(),
        bazaraki_start()
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот был остановлен вручную")
