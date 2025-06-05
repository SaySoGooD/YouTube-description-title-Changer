import re
import asyncio
from typing import Optional
from loguru import logger
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

ORANGE = "\033[38;5;214m"
RESET = "\033[0m"
CYAN = "\033[96m"
BLUE = "\033[94m"

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "client_secret.json"

languages = [
    'ab', 'aa', 'af', 'ak', 'akk', 'sq', 'ase', 'am', 'ar', 'arc', 'hy', 'as', 'ay', 'az', 'bm', 'bn', 'bn-IN',
    'ba', 'eu', 'be', 'bh', 'bi', 'brx', 'bs', 'br', 'bg', 'my', 'yue', 'yue-HK', 'ca', 'chr', 'zh', 'zh-CN',
    'zh-HK', 'zh-Hans', 'zh-SG', 'zh-TW', 'zh-Hant', 'cho', 'cop', 'co', 'cr', 'hr', 'cs', 'da', 'doi', 'nl',
    'nl-BE', 'nl-NL', 'dz', 'en', 'en-AU', 'en-CA', 'en-IN', 'en-IE', 'en-GB', 'en-US', 'eo', 'et', 'ee', 'fo',
    'fj', 'fil', 'fi', 'fr', 'fr-BE', 'fr-CA', 'fr-FR', 'fr-CH', 'ff', 'gl', 'lg', 'ka', 'de', 'de-AT', 'de-DE',
    'de-CH', 'el', 'gn', 'gu', 'guz', 'ht', 'hak', 'hak-TW', 'bgc', 'ha', 'haw', 'iw', 'hi', 'hi-Latn', 'ho',
    'hu', 'is', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kl', 'kln', 'kam', 'kn', 'ks', 'kk',
    'km', 'ki', 'rw', 'tlh', 'kok', 'ko', 'ku', 'ky', 'lad', 'lo', 'la', 'lv', 'ln', 'lt', 'dsb', 'lu', 'luo',
    'lb', 'luy', 'mk', 'mai', 'mg', 'ms', 'ms-SG', 'ml', 'mt', 'mni', 'mi', 'mr', 'mas', 'mer', 'nan', 'nan-TW',
    'mxp', 'lus', 'mn', 'mn-Mong', 'na', 'nv', 'ne', 'pcm', 'nd', 'nso', 'no', 'oc', 'or', 'om', 'pap', 'ps',
    'fa', 'fa-AF', 'fa-IR', 'pl', 'pt', 'pt-BR', 'pt-PT', 'pa', 'qu', 'ro', 'mo', 'rm', 'rn', 'ru', 'ru-Latn',
    'sm', 'sg', 'sa', 'sat', 'sc', 'gd', 'sr', 'sr-Cyrl', 'sr-Latn', 'sh', 'sdp', 'sn', 'scn', 'sd', 'si', 'sk',
    'sl', 'so', 'nr', 'st', 'es', 'es-419', 'es-MX', 'es-ES', 'es-US', 'su', 'sw', 'ss', 'sv', 'tl', 'tg', 'ta',
    'tt', 'te', 'th', 'bo', 'ti', 'tpi', 'tok', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'hsb', 'ur', 'ug',
    'uz', 've', 'vi', 'vo', 'vro', 'cy', 'fy', 'wal', 'wo', 'xh', 'yi', 'yo', 'zu'
]


class YouTubeVideoIDExtractor:
    """Класс для извлечения ID видео из URL YouTube Studio."""

    @staticmethod
    def extract(url: str) -> Optional[str]:
        pattern = r"https://studio\.youtube\.com/video/([a-zA-Z0-9_-]+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None


class ConsoleInput:
    """Асинхронный ввод данных с консоли."""

    @staticmethod
    async def async_input(prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)


class YouTubeServiceAuthenticator:
    """Класс, отвечающий за аутентификацию и создание YouTube API клиента."""
    @staticmethod
    def get_authenticated_service():
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        auth_url, _ = flow.authorization_url(prompt='consent')

        logger.info(f"{CYAN}Перейди по ссылке и авторизуйся:{RESET} {BLUE}{auth_url}{RESET}")
        code = input(f"{ORANGE}Вставь код авторизации:{RESET} ")
        flow.fetch_token(code=code)

        credentials = flow.credentials
        return build('youtube', 'v3', credentials=credentials)


class VideoUpdater:
    """Класс для обновления видео на YouTube."""

    def __init__(self, youtube_client):
        self.youtube = youtube_client

    def update_video(self, video_id: str, title: str, description: str):
        localizations = {lang: {"title": title, "description": description} for lang in languages}

        request_body = {
            "id": video_id,
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22",
                "defaultLanguage": "en"
            },
            "localizations": localizations
        }

        response = self.youtube.videos().update(
            part="snippet,status,localizations",
            body=request_body
        ).execute()

        logger.success(f"Видео обновлено: {response['id']}")


class FileLoader:
    """Класс для загрузки текста из файлов."""

    @staticmethod
    def load_text_file(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            raise ValueError(f"Файл {path} пуст или отсутствует текст.")
        return content


async def main():
    while True:
        logger.info(
            "Введите ссылку на видео в YouTube Studio для извлечения ID.\n"
            "Пример: https://studio.youtube.com/video/krtVKlwt-1o\n"
        )
        url = (await ConsoleInput.async_input(f"{ORANGE}Ввод:{RESET} ")).strip()
        video_id = YouTubeVideoIDExtractor.extract(url)
        if video_id:
            logger.success(f"ID видео найден: {video_id}")
            break
        else:
            logger.error("Некорректная ссылка. Попробуйте ещё раз.")

    try:
        title = FileLoader.load_text_file("title.txt")
        description = FileLoader.load_text_file("description.txt")

        youtube_client = YouTubeServiceAuthenticator.get_authenticated_service()
        updater = VideoUpdater(youtube_client)
        updater.update_video(video_id, title, description)

    except Exception as e:
        logger.exception(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
