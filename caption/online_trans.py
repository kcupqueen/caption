import requests


class OnlineTranslator:
    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    def login(self, username, password):
        self.username = username
        self.password = password
        print(f"Logged in as {self.username}")
        # todo login
        pass

    def lookup(self, text):
        print(f"Looking up {text} online...")
        # todo lookup, add timeout, handle exception
        ret_json = self.translate_text(text)
        sentence_translation = SentenceTranslation.from_json(ret_json)
        return sentence_translation


    def translate_text(self, text: str, target_lang: str = 'zh') -> dict:

        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            'text': text,
            'targetLang': target_lang,
        }

        response = requests.post(self.url, json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception('Translation failed')

        return response.json()