from handlers import commands
from config_data.client import client, phone_number
from config_data.config import Config, load_config

config: Config = load_config()


async def main():
    # Авторизуемся как пользователь
    await client.start(phone=config.tg_bot.phone)
    print(f"{config.tg_bot.bot_name} запущен...")

    # Добавляем обработчики
    client.add_event_handler(commands.start_command)
    client.add_event_handler(commands.history_command)

    # Оставляем клиент работать
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())