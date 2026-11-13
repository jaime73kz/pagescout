import json
from pathlib import Path

import pytest
import requests

from pagescout.config import ConfigError, parse_job
from pagescout.export import export
from pagescout.extract import extract_rows, parse_int, parse_price
from pagescout.fetch import FetchError, Fetcher

HTML = (Path(__file__).parent / "sample.html").read_text(encoding="utf-8")

JOB = {
    "urls": ["https://shop.test/catalogo"],
    "item_selector": ".product",
    "fields": {
        "title": "h2.name",
        "price": {"selector": ".price", "type": "price"},
        "stock": {"selector": ".stock", "type": "int"},
        "url": {"selector": "a", "type": "link"},
        "image": {"selector": "img", "type": "attr", "attr": "src"},
    },
}


@pytest.mark.parametrize("text,expected", [
    ("1.299,50 €", 1299.5), ("$1,299.50", 1299.5), ("24.99", 24.99),
    ("19,99", 19.99), ("1.299", 1299.0), ("gratis", None), ("", None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_parse_int():
    assert parse_int("12 uds") == 12
    assert parse_int("agotado") is None


def test_extract_rows():
    job = parse_job(JOB)
    rows = extract_rows(HTML, job.fields, job.item_selector, base_url="https://shop.test/catalogo")
    assert len(rows) == 3
    assert rows[0]["title"] == "Teclado mecánico"
    assert rows[0]["price"] == 1299.5
    assert rows[0]["stock"] == 12
    assert rows[0]["url"] == "https://shop.test/p/teclado"
    assert rows[1]["title"] == "Ratón inalámbrico"  # espacios limpiados
    assert rows[2]["price"] is None


def test_config_errors():
    with pytest.raises(ConfigError):
        parse_job({"fields": {"a": "b"}})
    with pytest.raises(ConfigError):
        parse_job({"urls": ["x"], "fields": {"a": {"selector": "p", "type": "raro"}}})
    with pytest.raises(ConfigError):
        parse_job({"urls": ["x"], "fields": {"a": {"selector": "p", "type": "attr"}}})


@pytest.mark.parametrize("name", ["out.csv", "out.json", "out.xlsx"])
def test_export_formats(tmp_path, name):
    rows = [{"title": "A", "price": 1.5}, {"title": "B", "price": None}]
    path = export(rows, tmp_path / name)
    assert path.exists() and path.stat().st_size > 0
    if name.endswith(".json"):
        assert json.loads(path.read_text(encoding="utf-8"))[0]["title"] == "A"


def test_export_bad_format(tmp_path):
    with pytest.raises(ValueError):
        export([{"a": 1}], tmp_path / "out.txt")


class FakeResponse:
    def __init__(self, status=200, text="ok"):
        self.status_code, self.text = status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.headers, self.calls = list(responses), {}, 0

    def get(self, url, timeout=None):
        if url.endswith("/robots.txt"):
            return FakeResponse(404)
        self.calls += 1
        return self.responses.pop(0)


def test_fetch_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("pagescout.fetch.time.sleep", lambda s: None)
    session = FakeSession([FakeResponse(503), FakeResponse(200, "hola")])
    fetcher = Fetcher("test", delay=0, retries=3, session=session)
    assert fetcher.get("https://shop.test/x") == "hola"
    assert session.calls == 2


def test_fetch_gives_up(monkeypatch):
    monkeypatch.setattr("pagescout.fetch.time.sleep", lambda s: None)
    session = FakeSession([FakeResponse(500)] * 3)
    fetcher = Fetcher("test", delay=0, retries=3, session=session)
    with pytest.raises(FetchError):
        fetcher.get("https://shop.test/x")


class RobotsSession(FakeSession):
    def get(self, url, timeout=None):
        if url.endswith("/robots.txt"):
            return FakeResponse(200, "User-agent: *\nDisallow: /privado")
        return super().get(url, timeout)


def test_respects_robots():
    fetcher = Fetcher("test", delay=0, session=RobotsSession([FakeResponse(200, "x")]))
    with pytest.raises(FetchError):
        fetcher.get("https://shop.test/privado/datos")
    assert fetcher.get("https://shop.test/publico") == "x"


def test_decodes_utf8_without_charset_header():
    class Resp:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        apparent_encoding = "utf-8"
        encoding = "ISO-8859-1"

        @property
        def text(self):
            return "teclado mecánico".encode("utf-8").decode(self.encoding)

        def raise_for_status(self):
            pass

    fetcher = Fetcher("test", delay=0, session=FakeSession([Resp()]))
    assert fetcher.get("https://shop.test/x") == "teclado mecánico"


def test_load_job_from_toml(tmp_path):
    from pagescout.config import load_job
    f = tmp_path / "job.toml"
    f.write_text('urls = ["https://a.test"]\n[fields]\ntitle = "h1"\nprice = { selector = ".p", type = "price" }\n',
                 encoding="utf-8")
    job = load_job(f)
    assert job.urls == ["https://a.test"]
    assert [x.name for x in job.fields] == ["title", "price"]
    assert job.fields[1].type == "price"


def test_load_job_bad_toml(tmp_path):
    from pagescout.config import load_job
    f = tmp_path / "bad.toml"
    f.write_text("urls = [", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_job(f)


def test_books_example_config_works_on_sample_page():
    from pagescout.config import load_job

    job = load_job(Path(__file__).parent.parent / "examples" / "books.toml")
    html = (Path(__file__).parent / "books_sample.html").read_text(encoding="utf-8")
    rows = extract_rows(html, job.fields, job.item_selector, base_url="https://books.toscrape.com/")
    assert len(rows) == 2
    assert rows[0]["title"] == "A Light in the Attic"   # título completo, sacado del atributo
    assert rows[0]["price"] == 51.77
    assert rows[0]["availability"] == "In stock"
    assert rows[0]["url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
