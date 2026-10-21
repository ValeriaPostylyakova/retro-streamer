class ApplicationError(Exception):
    def __init__(
        self, detail: str, status_code: int = 400, headers: dict | None = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.headers = headers or {}
        super().__init__(detail)
