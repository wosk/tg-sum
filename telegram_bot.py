import logging

import requests
from telethon import TelegramClient
from config import Config

logger = logging.getLogger("bot")
# logger.setLevel("DEBUG")
logging.basicConfig(level=logging.DEBUG,
                    force = True)

MAX_MSG_LEN=4096

class TelegramBotBuilder:
    def __init__(self, token):
        logger.info("Building a new bot.")
        self.bot = TelegramBot(token)

    def with_webhook(self, host):
        self.bot.set_webhook(host)
        return self

    def with_core_api(self, api_id, api_hash):
        client = TelegramClient('test', api_id, api_hash)
        self.bot.core_api_client = client
        return self

    def get_bot(self):
        return self.bot


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.bot_api_url = f"{Config.TELEGRAM_API}/bot{self.token}"
        self.core_api_client = None

    def set_webhook(self, host):
        try:
            # host = host.replace("http", "https")
            logger.info(f"Setting webhook for url: {host}")
            set_webhook_url = f"{self.bot_api_url}/setWebhook?url={host}"

            response = requests.get(set_webhook_url)
            response.raise_for_status()
            logger.info(f"Got response: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")

    def send_message(self, chat_id, message):
        try:
            logger.info(f"Sending message to chat #{chat_id}")
            send_message_url = f"{self.bot_api_url}/sendMessage"
            while message:
                chunk = message[:MAX_MSG_LEN]
                message = message[MAX_MSG_LEN:]
                response = requests.post(send_message_url, json={"chat_id": chat_id,
                                                                "text": chunk})
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def extract_name(self, msg):
        # No first_name field for admin of channel
        options = ["username"]
        options += ["title"]
        options += ["first_name"]
        sender = None
        i = 0
        while (not sender):
            opt = options[i]
            i += 1
            try:
                return getattr(msg.sender, opt)
            except AttributeError:
                continue
        return "admin"

    async def get_chat_history(self, chat_id, start_msg_id=0, topic_id=0, limit=30):
        try:
            if not self.core_api_client:
                return []
            logger.info(f"Getting conversation history for chat: {chat_id}")
            # entity = await self.core_api_client.get_entity(chat_id)
            kwargs = {}
            kwargs['entity'] = chat_id
            kwargs['limit'] = limit
            kwargs['reverse'] = True
            if start_msg_id != 0:
                kwargs['min_id'] = int(start_msg_id) - 1
            if topic_id != 0:
                kwargs['reply_to'] = int(topic_id)
            history = await self.core_api_client.get_messages(**kwargs)
            result = []
            for message in history:
                if message.message:
                    sender = self.extract_name(message)
                    result.append(f"{message.date} {sender}:\n {message.message}")
            return result
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            raise
