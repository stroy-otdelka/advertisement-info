import os
from dataclasses import field, dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    COLUMNS_HEADINGS = (
        "Заметка",
        "Ю.р лицо Озон",
        "Артикул ВБ",
        "Артикул Озон",
        "Артикул Яндекс",
        "Название Озон",
        "Наша Цена вб",
        "Цена с вб Кошельком",
        "Наша Цена Озон",
        "Цена с озон картой",
        "Мин. цена озон",
        "Цена Яндекс",
        "Цена ВБ - Цена Озон",
        "Остаток ВБ",
        "Остаток Озон",
        "Остаток Яндекс",
        "Продажи ВБ",
        "Продажи Озон",
        "Продажи Яндекс",
        "Ctok",
        "Реклама Ozon",
        "Кол-во товара в поставках Озон",
        "Акции Озон",
    )
    API_KEYS = {
        "amodecor": {
            "ozon": {
                "api_key": "12939537-c0ff-4427-a43d-8a804463416f",
                "client_id": "307257",
                "client_adv_id": "44928831-1735283266726@advertising.performance.ozon.ru",
                "client_adv_secret": "z1mm78mLDFr8hcKWuTQzyACRQpl-MsSWDZljiY_kL7jfO1MocpY3gVI4o_q1JDQy1LI_4dF-XhS6i8iRqQ",
            },
            "wb": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MTA1MTA0NywiaWQiOiIwMTk0MDZlZC1mYjBhLTc2ZmUtODBkZC1mMGJlNDM1MzljZmEiLCJpaWQiOjY1OTY2MDc2LCJvaWQiOjUwNjg5MywicyI6MTI3OCwic2lkIjoiYmMzZGNkZjYtMDdhOC00NDliLWJiM2UtNWQ2NjcxZWY3NGY5IiwidCI6ZmFsc2UsInVpZCI6NjU5NjYwNzZ9.wudRdfHDnIBNiKzarNB56o7xkmISIR3HQ9c8NTCDPjSOUi78iZspOJ3HJgA_EGybT5d6mJq4UsRdTEECtnzzcg",
            "yandex": {
                "api_key": "ACMA:hryyVpztwf7PVwwzd7nLtEpbzNgHAok1n0oWBFsz:0beb7a02",
                "business_id": "179125293",
                "campaign_id": "132733414",
            }
        },
        "drive": {
            "wb": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MTA1MDAwMywiaWQiOiIwMTk0MDZkZS0wZjAyLTc1YjgtOTE3OS1iMTJmMzhjZWJkMWYiLCJpaWQiOjY2NDY1MzU3LCJvaWQiOjUwMTM4MiwicyI6MTI3OCwic2lkIjoiYjMxY2YyZjMtNGZlNC00MWIzLTk5ZWYtMjA4OWM2YzFkZGZiIiwidCI6ZmFsc2UsInVpZCI6NjY0NjUzNTd9.HR0_ebC6QLr5GvpSb8jLI-jX78U7NZ0fV3xf9FKydDCjgmGIkPjfuz5R5CtoJ4bWrHGBpiIbvUP-4cwZUh_CbQ",
        },
        "centurion": {
            "wb": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MTA1MDM2NiwiaWQiOiIwMTk0MDZlMy05ODkxLTdlMWEtOWJkMi1kODc3NTc0NDBiMTkiLCJpaWQiOjUxMDU3Mzg5LCJvaWQiOjE3NzU4MSwicyI6MTI3OCwic2lkIjoiOGZmNWM1ZjYtNjU0Zi00Yjc3LTg3ZDYtZjNlMmFiOGIyYWQ2IiwidCI6ZmFsc2UsInVpZCI6NTEwNTczODl9.hwm3xd_kw0Pq4m7J6_QeQObwwL5BOkCyTgxRTeDto4mGbXJ0k-rhR5AOYxlCX8azVE-Mm8BAD0hZXD48wWgFlQ",
        },
        "stroy_otdelka": {
            "ozon": {
                "api_key": "da31a290-4bbe-4878-9670-ece1582b895a",
                "client_id": "82743",
                "client_adv_id": "45182394-1735283813311@advertising.performance.ozon.ru",
                "client_adv_secret": "mVs6hRvEfsVFEa2hi9I9mLSrYT-MohxaA2g3WbBHyGkBWsQ47AmdMFTn7Ztnyce0HIo43GntpPhAou6GrA",
            },
            "wb": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1MTA1MDMwMCwiaWQiOiIwMTk0MDZlMi05Njk4LTc0OTYtYmU2OC0zM2RhMzNkYjgyNmMiLCJpaWQiOjQ0NDU4NjU1LCJvaWQiOjgyNzk5LCJzIjoxMjc4LCJzaWQiOiI0YTFjZjAxYi1hNTQ1LTVjMjktYjQ2MS04Y2RiNTgyMTU0MWYiLCJ0IjpmYWxzZSwidWlkIjo0NDQ1ODY1NX0.Yx0lCO7e8p78b4umF29RT_0bey_CpiGubHjwVY4aVFIF98G2QmTTNd5qnu5_4usN5iNWn4am7wI18xjHKCNzuQ",
            "yandex": {
                "api_key": "ACMA:4JGW1NIrpGO8ulOqnaFc3muIwWmbXDq4naeNFDED:5336a0e2",
                "business_id": "991134",
                "campaign_id": "23749474",
            }
        },
        "orion": {
            "ozon": {
                "api_key": "9b17fc68-7d1f-4842-a2b2-5f0ef2d35add",
                "client_id": "1682238",
                "client_adv_id": "45182483-1735283568212@advertising.performance.ozon.ru",
                "client_adv_secret": "0k30P6ha7_twNcgYeXPYruuQMdosIL04IymzY5L76Mxey9hkHHHMD2sZ8NIgVy2sqeRdskgf3zxMCH1Mxw",
            },
         },
    }
    PATH_TO_EXPORT = os.getenv("PATH_TO_EXPORT")
    SHEET_SECRET = os.getenv("SHEET_SECRET")
    SCOPES_DRIVE: list[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/drive.file"  # Доступ к файлам, созданным вашим приложением
            "https://www.googleapis.com/auth/drive",  # Полный доступ к Google Drive (опционально)
        ]
    )
    SCOPES_SHEETS: list[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    DRIVE_SECRET = os.getenv("DRIVE_SECRET")

    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")

    PATH_TO_SCREENSHOTS = './screenshots/'

    DRIVER_VERSION = 131

    PROJECT_ID: str = "yellduck"
    LOG_TOPIC: str = "error_logs"
    SERVICE_NAME: str = "price-comparison"

    @property
    def get_db_url(self):
        """Возвращает URL для подключения к базе данных."""
        url = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return url


CONFIG = Config()
