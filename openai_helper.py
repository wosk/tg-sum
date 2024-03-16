import logging

from openai import OpenAI

client = None

logger = logging.getLogger("bot")
# logger.setLevel("DEBUG")
logging.basicConfig(level=logging.DEBUG,
                    force = True)

class OpenAiHelper:
    def __init__(self, token, model="gpt-3.5-turbo"):
        global client
        logging.info(f"Initializing OpenAI helper. Selected model: {model}")
        client = OpenAI(api_key=token)
        self.model = model

    def get_response(self, message_text):
        try:
            logging.info(f"Getting response from OpenAI. Message: {message_text}")
            response = client.chat.completions.create(model=self.model,
                                                    messages=[{"role": "user", "content": message_text}])
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Failed to get response from OpenAI: {e}")
            raise
