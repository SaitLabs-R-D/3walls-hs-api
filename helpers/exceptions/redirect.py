class RedirectException(Exception):
    def __init__(
        self,
        url: str,
        status_code: int = 302,
        remove_cookies: list[str] = [],
        data: dict = {},
    ):
        self.url = url
        self.status_code = status_code
        self.remove_cookies = remove_cookies
        self.data = data
