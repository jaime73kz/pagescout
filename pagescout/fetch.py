"""Descarga de páginas con reintentos, espera entre peticiones y respeto a robots.txt."""
import logging
import time
from urllib import robotparser
from urllib.parse import urlparse

import requests

log = logging.getLogger("pagescout")


class FetchError(RuntimeError):
    """No se pudo descargar la página."""


class Fetcher:
    def __init__(self, user_agent: str, delay: float = 1.0, retries: int = 3,
                 timeout: float = 15.0, respect_robots: bool = True, session=None):
        self.user_agent = user_agent
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._last_request = 0.0

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                resp = self.session.get(origin + "/robots.txt", timeout=self.timeout)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                    self._robots[origin] = rp
                else:
                    self._robots[origin] = None  # sin robots.txt: todo permitido
            except requests.RequestException:
                self._robots[origin] = None
        rp = self._robots[origin]
        return True if rp is None else rp.can_fetch(self.user_agent, url)

    def _wait(self):
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    @staticmethod
    def _decode(resp) -> str:
        """Si la web no indica charset, requests supone latin-1 y rompe las tildes.
        En ese caso se detecta la codificación real a partir del contenido."""
        headers = getattr(resp, "headers", None) or {}
        if "charset" not in headers.get("Content-Type", "").lower():
            apparent = getattr(resp, "apparent_encoding", None)
            if apparent:
                resp.encoding = apparent
        return resp.text

    def get(self, url: str) -> str:
        if not self._allowed(url):
            raise FetchError(f"robots.txt no permite acceder a {url}")
        last_error = None
        for attempt in range(1, self.retries + 1):
            self._wait()
            self._last_request = time.monotonic()
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                return self._decode(resp)
            except requests.RequestException as exc:
                last_error = exc
                wait = 2 ** attempt
                log.warning("Intento %d/%d falló para %s: %s", attempt, self.retries, url, exc)
                if attempt < self.retries:
                    time.sleep(wait)
        raise FetchError(f"No se pudo descargar {url}: {last_error}")
