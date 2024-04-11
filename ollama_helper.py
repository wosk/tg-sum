import logging
import ollama

client = None

logger = logging.getLogger("bot")
# logger.setLevel("DEBUG")
logging.basicConfig(level=logging.DEBUG,
                    force = True)

class ollamaAI:
    def __init__(self, model="zephyr"):
        global client
        logging.info(f"Initializing ollama helper. Selected model: {model}")
        self.model = model
        # try:
        #     client = ollama.pull(model)
        #     
        # finally:
        #     list = ollama.list()
        #     logging.error(f"Failed to get response from OpenAI: {e}")

    def ns_to_floats(self, ns):
        ns_in_ms = 1000 * 1000
        return (ns // ns_in_ms) / 1000

    def get_response(self, message_text):
        try:
            logging.info(f"Getting response from ollama...")
            response = ollama.generate(model=self.model, prompt=message_text)
            # logging.info(f"Prompt tokens: {response['prompt_eval_count']}")
            logging.info(f"Answer tokens: {response['eval_count']}")
            logging.info(f"Time to load LLM: {self.ns_to_floats(response['load_duration'])}")
            logging.info(f"Time to eval prompt: {self.ns_to_floats(response['prompt_eval_duration'])}")
            logging.info(f"Time to gen answer: {self.ns_to_floats(response['eval_duration'])}")
            logging.info(f"Time sum: {self.ns_to_floats(response['total_duration'])}")
            return response['response']
        except Exception as e:
            logging.error(f"Failed to get response from ollama: {e}")
            raise
