import requests


class SentenceTranslation:
    def __init__(self, translated_text="N/A", key_points=None, target_language="N/A"):
        if key_points is None:
            key_points = []
        self.translated_text = translated_text
        self.key_points = key_points
        self.target_language = target_language

    @classmethod
    def from_json(cls, json_data):
        translated_text = json_data.get('json', {}).get('translated_text', "N/A")
        key_points = json_data.get('json', {}).get('key_points', [])
        target_language = json_data.get('target_language', "N/A")
        return cls(translated_text, key_points, target_language)

    def __repr__(self):
        return f"SentenceTranslation(translated_text={self.translated_text}, key_points={self.key_points}, target_language={self.target_language})"

    def __str__(self):
        return f"Translated Text: {self.translated_text}\nKey Points: {self.key_points}\nTarget Language: {self.target_language}"

    def to_html(self):
        key_points_html = "".join(
            f"<li><strong>{kp['key']}:</strong> {kp['explanation']}</li>" for kp in self.key_points
        )
        return f"""
        <html>
            <body>
                <h3>{self.translated_text}</h3>
                <h3>Key Points</h3>
                <ul>
                    {key_points_html}
                </ul>
            </body>
        </html>
        """

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
        try:
            print(f"Looking up {text} online...")
            # todo lookup, add timeout, handle exception
            ret_json = self.translate_text(text)
            sentence_translation = SentenceTranslation.from_json(ret_json)
            if sentence_translation:
                return sentence_translation.to_html()
            return "translation failed"
        except Exception as e:
            return f"Error: {e}"


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
            raise Exception('Translation failed, response code:', response.status_code)

        return response.json()