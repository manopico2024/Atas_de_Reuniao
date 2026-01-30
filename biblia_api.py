import requests

class BibliaDigitalAPI:
    BASE_URL = "https://www.abibliadigital.com.br/api"

    def __init__(self, token: str | None = None):
        self.token = token

    def _headers(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ==========================
    # 📚 BOOKS
    # ==========================
    def get_books(self):
        return requests.get(
            f"{self.BASE_URL}/books",
            headers=self._headers()
        ).json()

    def get_book(self, abbrev: str):
        return requests.get(
            f"{self.BASE_URL}/books/{abbrev}",
            headers=self._headers()
        ).json()

    # ==========================
    # 📖 VERSES
    # ==========================
    def get_chapter(self, version: str, abbrev: str, chapter: int):
        return requests.get(
            f"{self.BASE_URL}/verses/{version}/{abbrev}/{chapter}",
            headers=self._headers()
        ).json()

    def get_verse(self, version: str, abbrev: str, chapter: int, number: int):
        return requests.get(
            f"{self.BASE_URL}/verses/{version}/{abbrev}/{chapter}/{number}",
            headers=self._headers()
        ).json()

    def get_random_verse(self, version: str):
        return requests.get(
            f"{self.BASE_URL}/verses/{version}/random",
            headers=self._headers()
        ).json()

    def get_random_verse_book(self, version: str, abbrev: str):
        return requests.get(
            f"{self.BASE_URL}/verses/{version}/{abbrev}/random",
            headers=self._headers()
        ).json()

    def search_word(self, version: str, word: str):
        payload = {
            "version": version,
            "search": word
        }
        return requests.post(
            f"{self.BASE_URL}/verses/search",
            json=payload,
            headers=self._headers()
        ).json()

    # ==========================
    # 📜 VERSIONS
    # ==========================
    def get_versions(self):
        return requests.get(
            f"{self.BASE_URL}/versions",
            headers=self._headers()
        ).json()

    # ==========================
    # 👤 USERS
    # ==========================
    def create_user(self, name, email, password, notifications=True):
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "notifications": notifications
        }
        return requests.post(
            f"{self.BASE_URL}/users",
            json=payload,
            headers=self._headers()
        ).json()

    def get_user(self, email):
        return requests.get(
            f"{self.BASE_URL}/users/{email}",
            headers=self._headers()
        ).json()

    def update_token(self, email, password):
        payload = {
            "email": email,
            "password": password
        }
        return requests.put(
            f"{self.BASE_URL}/users/token",
            json=payload,
            headers=self._headers()
        ).json()

    def delete_user(self, email, password):
        payload = {
            "email": email,
            "password": password
        }
        return requests.delete(
            f"{self.BASE_URL}/users",
            json=payload,
            headers=self._headers()
        ).json()

    # ==========================
    # 📊 REQUESTS / STATS
    # ==========================
    def get_requests(self, range_: str):
        return requests.get(
            f"{self.BASE_URL}/requests/{range_}",
            headers=self._headers()
        ).json()

    def get_requests_amount(self, range_: str):
        return requests.get(
            f"{self.BASE_URL}/requests/amount/{range_}",
            headers=self._headers()
        ).json()