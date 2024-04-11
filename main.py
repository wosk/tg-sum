import asyncio
import logging
from urllib.parse import urlparse

import hypercorn.asyncio
from pyngrok import ngrok
from quart import Quart, request

from config import Config
from models import Update
from openai_helper import OpenAiHelper
from ollama_helper import ollamaAI
from telegram_bot import TelegramBotBuilder

logger = logging.getLogger("bot")
# logger.setLevel("DEBUG")
logging.basicConfig(level=logging.DEBUG,
                    force = True)

app = Quart(__name__)

help = (
    "/summarize - make small rephrase\n"
    "/ai - direct question to OpenAI\n"
)

async def send_ai_request(prompt, chat_id):
    resp = app.brain.get_response(prompt)
    app.bot.send_message(chat_id, resp)
    
@app.route('/', methods=["GET", "POST"])
async def handle_webhook():
    try:
        json_data = await request.json
        logger.info(f"Handling a webhook: {json_data}")
        update = Update(**json_data)
        chat_id = update.message.chat.id

        logger.info('process Request ' + update.message.text)

        # if update.message.text.startswith("/summarize"):
        #     history = await app.bot.get_chat_history(chat_id)
        #     response = app.brain.get_response("Кратко опиши диалог:\n" + history)
        if update.message.text.startswith("/ai"):
            response = "In progress..."
            # response = app.brain.get_response(update.message.text.replace("/ai ", ''))
            prompt = update.message.text.replace("/ai ", '')
            asyncio.create_task(send_ai_request(prompt, chat_id))
        elif update.message.text.startswith("https://t.me"):
            parsed_url = urlparse(update.message.text)
            path = parsed_url.path
            subdirectories = [directory for directory in path.split('/') if directory]

            subdirectories_with_topic = 3
            msg_id = subdirectories[-1]

            if subdirectories[0]=="c":
                channel = "/".join(subdirectories[:2])
                subdirectories_with_topic += 1
            else:
                channel = subdirectories[0]

            topic_id = 0
            if (len(subdirectories) == subdirectories_with_topic):
                topic_id = subdirectories[subdirectories_with_topic - 2]

            channel = 't.me/' + channel
            history = await app.bot.get_chat_history(channel, start_msg_id=msg_id, topic_id=topic_id)
            prompt = "Кратко перескажи на русском языке обсуждение:\n" + "\n\n".join(history)

            response = "Summarizing in progress..."
            # response = app.brain.get_response(prompt)
            # await app.bot.send_message(chat_id, app.brain.get_response(prompt))
            asyncio.create_task(send_ai_request(prompt, chat_id))
        else:
            response = help

        app.bot.send_message(chat_id, response)

        return "OK", 200
    except Exception as e:
        err_msg = f"Something went wrong while handling a request: {e}"
        logger.error(err_msg)
        app.bot.send_message(chat_id, err_msg)
        return "OK", 200    # To avoid re-request loop
        # return "Something went wrong", 500


def run_ngrok(port=8000):
    logger.info(f"Starting ngrok tunnel at port {port}")
    http_tunnel = ngrok.connect(port)
    return http_tunnel.public_url


@app.before_serving
async def startup():
    Config.TELEGRAM_TOKEN="FILL"
    Config.OPENAI_TOKEN="FILL"
    Config.TELEGRAM_CORE_API_ID="FILL"
    Config.TELEGRAM_CORE_API_HASH="FILL"
    phone_number="FILL"

    host = run_ngrok(Config.PORT)
    bot_builder = TelegramBotBuilder(Config.TELEGRAM_TOKEN) \
        .with_webhook(host) \
        .with_core_api(Config.TELEGRAM_CORE_API_ID, Config.TELEGRAM_CORE_API_HASH)

    app.bot = bot_builder.get_bot()
    app.brain = ollamaAI()
    # app.openai_helper = OpenAiHelper(Config.OPENAI_TOKEN)

    if app.bot.core_api_client:
        await app.bot.core_api_client.connect()
        await app.bot.core_api_client.start()
        client = app.bot.core_api_client
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number, input('Enter the code: '))


async def main():
    quart_cfg = hypercorn.Config()
    quart_cfg.bind = [f"127.0.0.1:{Config.PORT}"]
    logger.info("Starting the application")
    await hypercorn.asyncio.serve(app, quart_cfg)


if __name__ == "__main__":
    asyncio.run(main())
