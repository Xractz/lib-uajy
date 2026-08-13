# OOP Refactor + Scrapling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor API booking ruang UAJY ke arsitektur OOP berbasis composition, ganti `requests`+`re` dengan Scrapling, dan hapus fitur plagiarisme.

**Architecture:** Modular per domain — `app/config.py` (konstanta), `app/booking/scraper.py` (`BookingScraper`, HTTP + parsing), `app/booking/service.py` (`RoomService`, logika bisnis), `app/booking/routes.py` (FastAPI). Scraper di-inject ke service (dependency injection), bukan di-inherit.

**Tech Stack:** FastAPI, Scrapling (`FetcherSession` async + `Selector`), Python 3.9+ (`zoneinfo`, `datetime`).

## Global Constraints

- Semua scraping lewat Scrapling `FetcherSession` (`async with ... as session`, `await session.get/post`). Tidak ada `requests`.
- Parsing HTML lewat `Selector.css()` / `.get()` / `.getall()`. Regex hanya dipakai untuk ekstrak pesan `alert('...')` (itu JS string, bukan HTML).
- Semua konstanta (URL, ruang, slot waktu, timezone) hidup di `app/config.py`.
- Return convention service: `(dict, int)` — `(body, status_code)`.
- Class plagiarisme dan endpoint `/turnitin*` **dihapus**.
- Waktu pakai `datetime` + `zoneinfo` (`config.TZ`), bukan `pytz`.
- Jalankan Python dengan `python3`, install paket dengan `pip3`.
- README berbahasa Indonesia.
- Target website memakai `http://` (tanpa TLS) — `FetcherSession` dipakai tanpa `verify=False` (default `verify=True`, diabaikan untuk http). Jangan matikan verifikasi TLS.

---

## Fakta HTML (diverifikasi lewat DevTools)

**`default.aspx`** (form booking) punya hidden input: `__EVENTTARGET`, `__EVENTARGUMENT`, `__LASTFOCUS`, `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION`. Field form: `ctl00$MainContent$txtNPM` (id `MainContent_txtNPM`), `txtNama` (`MainContent_txtNama`), `txtEmail` (`MainContent_txtEmail`), `DdlRuang`, `txtTanggal`, `DdlJam`, `btnDaftar`.

**`CekJadwal.aspx`** (jadwal) punya `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__VIEWSTATEENCRYPTED` — **TIDAK punya `__EVENTVALIDATION`**. Tabel: `<table class="GridViewStyle" id="MainContent_gvTransaksi">`, baris data pakai class **`RowStyle` DAN `AltRowStyle`** (bergantian). Kolom: No, RUANG, TANGGAL, JAM, PEMESAN (5 `<td>`, `td` pertama = index).

**Dua bug original yang diperbaiki oleh refactor ini:**
1. `fetch_token()` asumsi `__EVENTVALIDATION` selalu ada → `.group(1)` akan crash di `CekJadwal.aspx`.
2. Regex jadwal hanya cocok `tr class="RowStyle"` → baris `AltRowStyle` (setiap baris genap) hilang.
3. `is_valid_time()` pakai `time.split(" ")[2]` (="09.30", jam *akhir*) padahal harusnya `[0]` (="08.00", jam *mulai*).

---

### Task 1: `config.py` + `requirements.txt`

**Files:**
- Create: `app/config.py`
- Modify: `requirements.txt`
- Create: `app/booking/__init__.py` (kosong)

**Interfaces:**
- Produces: `config.BASE_URL`, `config.URL_DEFAULT`, `config.URL_JADWAL`, `config.ROOMS`, `config.TIME_SLOTS`, `config.TZ`

- [ ] **Step 1: Tulis `app/config.py`**

```python
"""Konstanta global untuk booking ruang UAJY."""

from zoneinfo import ZoneInfo

BASE_URL = "http://form.lib.uajy.ac.id/booking/"
URL_DEFAULT = BASE_URL + "default.aspx"
URL_JADWAL = BASE_URL + "CekJadwal.aspx"

ROOMS = [
    "Discussion Room 1",
    "Discussion Room 2",
    "Discussion Room 3",
    "Leisure Room 1",
]

TIME_SLOTS = [
    "08.00 - 09.30 WIB",
    "09.30 - 11.00 WIB",
    "11.00 - 12.30 WIB",
    "12.30 - 14.00 WIB",
    "14.00 - 15.30 WIB",
    "15.30 - 17.00 WIB",
    "17.00 - 18.30 WIB",
]

TZ = ZoneInfo("Asia/Jakarta")
```

- [ ] **Step 2: Buat `app/booking/__init__.py` kosong**

```bash
mkdir -p app/booking && touch app/booking/__init__.py
```

- [ ] **Step 3: Update `requirements.txt`**

```text
fastapi==0.110.2
uvicorn==0.29.0
python-multipart==0.0.9
scrapling[fetchers]
```

- [ ] **Step 4: Verifikasi config bisa di-import**

```bash
python3 -c "from app import config; print(config.URL_JADWAL, len(config.ROOMS))"
```

Expected: `http://form.lib.uajy.ac.id/booking/CekJadwal.aspx 4`

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/booking/__init__.py requirements.txt
git commit -m "feat: add config module and update dependencies for Scrapling"
```

---

### Task 2: `BookingScraper` (scraping + parsing)

**Files:**
- Create: `app/booking/scraper.py`
- Test: `tests/test_scraper.py`

**Interfaces:**
- Consumes: `config.URL_DEFAULT`, `config.URL_JADWAL`
- Produces:
  - `class BookingScraper` dengan method publik: `fetch_all_schedule() -> list[dict]`, `get_student_info(npm) -> dict`, `submit_booking(npm, name, email, token, room, date, time) -> str`
  - Parse helper statis: `parse_token(page) -> dict`, `parse_schedule_rows(page) -> list[dict]`, `parse_max_page(page) -> int`
  - Exception: `ScraperError`, `StudentNotFoundError`

- [ ] **Step 1: Tulis test yang fail dulu** — `tests/test_scraper.py`

```python
from scrapling.parser import Selector

from app.booking.scraper import BookingScraper, ScraperError

HTML_JADWAL = """
<table class="GridViewStyle" id="MainContent_gvTransaksi">
  <tr class="HeaderStyle"><th>No</th><th>RUANG</th><th>TANGGAL</th><th>JAM</th><th>PEMESAN</th></tr>
  <tr class="RowStyle">
    <td class="grid_cell">1</td><td>Discussion Room 1</td><td>13/08/2026</td><td>08.00 - 09.30 WIB</td><td>EDHI HERI</td>
  </tr>
  <tr class="AltRowStyle">
    <td class="grid_cell">2</td><td>Discussion Room 2</td><td>13/08/2026</td><td>09.30 - 11.00 WIB</td><td>Legio Novelni</td>
  </tr>
  <tr class="PagerStyle"><td colspan="5"><a>1</a> <a>2</a> <a>3</a></td></tr>
</table>
"""

HTML_TOKEN_DEFAULT = """
<form>
<input type="hidden" id="__VIEWSTATE" value="ABC123">
<input type="hidden" id="__VIEWSTATEGENERATOR" value="GEN1">
<input type="hidden" id="__EVENTVALIDATION" value="EV1">
</form>
"""

HTML_TOKEN_JADWAL = """
<form>
<input type="hidden" id="__VIEWSTATE" value="ABC123">
<input type="hidden" id="__VIEWSTATEGENERATOR" value="GEN1">
</form>
"""


def test_parse_schedule_rows_captures_both_row_styles():
    page = Selector(HTML_JADWAL)
    rows = BookingScraper.parse_schedule_rows(page)
    assert len(rows) == 2
    assert rows[0] == {"room": "Discussion Room 1", "date": "13/08/2026", "time": "08.00 - 09.30 WIB", "name": "EDHI HERI"}
    assert rows[1]["room"] == "Discussion Room 2"


def test_parse_max_page():
    page = Selector(HTML_JADWAL)
    assert BookingScraper.parse_max_page(page) == 3


def test_parse_max_page_defaults_to_one():
    page = Selector("<html><body>tidak ada pager</body></html>")
    assert BookingScraper.parse_max_page(page) == 1


def test_parse_token_with_eventvalidation():
    page = Selector(HTML_TOKEN_DEFAULT)
    token = BookingScraper.parse_token(page)
    assert token["__VIEWSTATE"] == "ABC123"
    assert token["__EVENTVALIDATION"] == "EV1"


def test_parse_token_without_eventvalidation():
    page = Selector(HTML_TOKEN_JADWAL)
    token = BookingScraper.parse_token(page)
    assert token["__EVENTVALIDATION"] == ""


def test_parse_token_raises_when_no_viewstate():
    page = Selector("<html><body></body></html>")
    try:
        BookingScraper.parse_token(page)
        assert False, "harusnya raise ScraperError"
    except ScraperError:
        pass
```

- [ ] **Step 2: Jalankan test, pastikan fail**

```bash
python3 -m pytest tests/test_scraper.py -q
```

Expected: FAIL (modul `app.booking.scraper` belum ada).

- [ ] **Step 3: Tulis `app/booking/scraper.py`**

```python
"""Akses HTTP dan parsing HTML website booking UAJY via Scrapling."""

import re

from scrapling.fetchers import FetcherSession
from scrapling.parser import Selector

from app import config


class ScraperError(Exception):
    """Error umum saat scraping (HTTP gagal / elemen tidak ditemukan)."""


class StudentNotFoundError(Exception):
    """NPM/NPP tidak terdaftar di sistem UAJY."""


class BookingScraper:
    """Satu-satunya class yang tahu cara berbicara dengan website UAJY.

    Stateless: tiap method membuka `FetcherSession` sendiri. State ASP.NET
    dibawa lewat `__VIEWSTATE` (hidden field), bukan cookie session server,
    jadi session baru per request aman.
    """

    # ---- HTTP entry points (dipanggil RoomService) ----

    async def fetch_all_schedule(self) -> list[dict]:
        """Ambil seluruh data pemesanan (semua halaman)."""
        async with FetcherSession() as session:
            page = await session.get(config.URL_JADWAL)
            max_page = self.parse_max_page(page)
            bookings = self.parse_schedule_rows(page)
            token = self.parse_token(page)

            for n in range(2, max_page + 1):
                resp = await session.post(config.URL_JADWAL, data={
                    "__EVENTTARGET": "ctl00$MainContent$gvTransaksi",
                    "__EVENTARGUMENT": f"Page${n}",
                    "__VIEWSTATEENCRYPTED": "",
                    **token,
                })
                bookings.extend(self.parse_schedule_rows(resp))
                token = self.parse_token(resp)  # viewstate berubah tiap postback

        return bookings

    async def get_student_info(self, npm: int) -> dict:
        """Cari nama & email mahasiswa dari NPM.

        Returns dict {"name", "email", "token"} dengan token hasil postback
        (untuk dipakai `submit_booking`). Raise `StudentNotFoundError` bila
        NPM tidak terdaftar.
        """
        async with FetcherSession() as session:
            page = await session.get(config.URL_DEFAULT)
            token = self.parse_token(page)
            resp = await session.post(config.URL_DEFAULT, data={
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "ctl00$MainContent$txtNPM": str(npm),
                "ctl00$MainContent$txtNama": "",
                "ctl00$MainContent$txtEmail": "",
                "ctl00$MainContent$DdlRuang": "Discussion Room 1",
                "ctl00$MainContent$txtTanggal": "",
                "ctl00$MainContent$DdlJam": "08.00 - 09.30 WIB",
                **token,
            })

        if "tidak terdaftar" in str(resp):
            raise StudentNotFoundError("NPM/NPP tidak terdaftar")

        return {
            "name": resp.css("#MainContent_txtNama::attr(value)").get() or "",
            "email": resp.css("#MainContent_txtEmail::attr(value)").get() or "",
            "token": self.parse_token(resp),
        }

    async def submit_booking(
        self,
        npm: int,
        name: str,
        email: str,
        token: dict,
        room: str,
        date: str,
        time: str,
    ) -> str:
        """Kirim form booking. `date` dalam format DD/MM/YYYY. Return pesan."""
        wire_date = f"{date[3:5]}/{date[:2]}/{date[6:]}"  # DD/MM/YYYY -> MM/DD/YYYY

        async with FetcherSession() as session:
            resp = await session.post(config.URL_DEFAULT, data={
                "__EVENTTARGET": "ctl00$MainContent$btnDaftar",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "ctl00$MainContent$txtNPM": str(npm),
                "ctl00$MainContent$txtNama": name,
                "ctl00$MainContent$txtEmail": email,
                "ctl00$MainContent$DdlRuang": room,
                "ctl00$MainContent$txtTanggal": wire_date,
                "ctl00$MainContent$DdlJam": time,
                **token,
            })

        text = str(resp)
        # ponytail: regex di sini untuk ekstrak JS alert(), bukan parsing HTML
        match = re.search(r"alert\('(.+?)'\)", text)
        return match.group(1) if match else "Booking room failed."

    # ---- Parse helper (murni, unit-testable) ----

    @staticmethod
    def parse_token(page) -> dict:
        token = {
            "__VIEWSTATE": page.css("#__VIEWSTATE::attr(value)").get() or "",
            "__VIEWSTATEGENERATOR": page.css("#__VIEWSTATEGENERATOR::attr(value)").get() or "",
            "__EVENTVALIDATION": page.css("#__EVENTVALIDATION::attr(value)").get() or "",
        }
        if not token["__VIEWSTATE"]:
            raise ScraperError("__VIEWSTATE tidak ditemukan di halaman")
        return token

    @staticmethod
    def parse_schedule_rows(page) -> list[dict]:
        bookings = []
        for row in page.css("tr.RowStyle, tr.AltRowStyle"):
            cells = [c.strip() for c in row.css("td::text").getall()]
            if len(cells) < 5:
                continue
            bookings.append({
                "room": cells[1],
                "date": cells[2],
                "time": cells[3],
                "name": cells[4],
            })
        return bookings

    @staticmethod
    def parse_max_page(page) -> int:
        nums = page.css("tr.PagerStyle a::text").getall()
        pages = [int(n) for n in nums if n.strip().isdigit()]
        return max(pages) if pages else 1
```

- [ ] **Step 4: Jalankan test, pastikan pass**

```bash
python3 -m pytest tests/test_scraper.py -q
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add app/booking/scraper.py tests/test_scraper.py
git commit -m "feat: add BookingScraper using Scrapling"
```

---

### Task 3: `RoomService` (logika bisnis)

**Files:**
- Create: `app/booking/service.py`
- Test: `tests/test_service.py`

**Interfaces:**
- Consumes: `BookingScraper` (di-inject), `config.ROOMS`, `config.TIME_SLOTS`, `config.TZ`
- Produces: `class RoomService(scraper)` dengan method: `get_booked_rooms()`, `get_booked_by_date(date_str)`, `get_available_rooms()`, `get_available_by_date(date_str)`, `book_room(npm, room, date, time)` — semuanya `async`, return `(dict, int)`.

- [ ] **Step 1: Tulis test yang fail** — `tests/test_service.py`

```python
import pytest

from app.booking.service import RoomService


class FakeScraper:
    """Scraper palsu: return data booking tetap, tanpa HTTP."""

    def __init__(self, bookings):
        self.bookings = bookings

    async def fetch_all_schedule(self):
        return self.bookings

    async def get_student_info(self, npm):
        if npm == 999:
            from app.booking.scraper import StudentNotFoundError
            raise StudentNotFoundError("tidak terdaftar")
        return {"name": "Jhon Doe", "email": "jhon@mail.com", "token": {"__VIEWSTATE": "x"}}

    async def submit_booking(self, npm, name, email, token, room, date, time):
        return "Booking Success"


# hari ini dalam zona WIB, format DD/MM/YYYY
from datetime import datetime
from app import config
TODAY = datetime.now(config.TZ).strftime("%d/%m/%Y")

BOOKINGS = [
    {"room": "Discussion Room 1", "date": TODAY, "time": "08.00 - 09.30 WIB", "name": "A"},
    {"room": "Discussion Room 2", "date": TODAY, "time": "09.30 - 11.00 WIB", "name": "B"},
]


@pytest.fixture
def service():
    return RoomService(FakeScraper(BOOKINGS))


@pytest.mark.asyncio
async def test_get_booked_rooms_groups_by_room(service):
    body, status = await service.get_booked_rooms()
    assert status == 200
    assert TODAY in body["bookedRoom"]
    assert body["bookedRoom"][TODAY]["Discussion Room 1"][0]["name"] == "A"


@pytest.mark.asyncio
async def test_get_booked_by_date_returns_empty_when_none(service):
    body, status = await service.get_booked_by_date("01012000")
    assert status == 404
    assert body["bookedRoom"] == {}


@pytest.mark.asyncio
async def test_available_rooms_removes_booked_slot(service):
    body, status = await service.get_available_rooms()
    assert status == 200
    slots = body["roomAvailable"][TODAY]["Discussion Room 1"]
    assert "08.00 - 09.30 WIB" not in slots
    assert "17.00 - 18.30 WIB" in slots


@pytest.mark.asyncio
async def test_book_room_lookup_only(service):
    body, status = await service.book_room(123, None, None, None)
    assert status == 200
    assert body["name"] == "Jhon Doe"


@pytest.mark.asyncio
async def test_book_room_invalid_room(service):
    body, status = await service.book_room(123, "Ruang Salah", TODAY, "08.00 - 09.30 WIB")
    assert status == 400


@pytest.mark.asyncio
async def test_book_room_npm_not_found(service):
    body, status = await service.book_room(999, None, None, None)
    assert status == 404
```

- [ ] **Step 2: Jalankan test, pastikan fail**

```bash
python3 -m pytest tests/test_service.py -q
```

Expected: FAIL (modul belum ada).

- [ ] **Step 3: Tulis `app/booking/service.py`**

```python
"""Logika bisnis pemesanan ruang. Tidak tahu soal HTTP."""

from datetime import datetime, date

from app import config
from app.booking.scraper import BookingScraper, StudentNotFoundError


class RoomService:
    def __init__(self, scraper: BookingScraper):
        self.scraper = scraper

    # ---- internal helper ----

    @staticmethod
    def _format_date(date_str: str) -> str:
        """'29042024' -> '29/04/2024'."""
        return f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"

    @staticmethod
    def _parse_date(d: str) -> date:
        return datetime.strptime(d, "%d/%m/%Y").date()

    @staticmethod
    def _today() -> date:
        return datetime.now(config.TZ).date()

    @staticmethod
    def _now_hm() -> str:
        """Jam sekarang 'HH.MM' (string compare aman untuk jam 0-padded)."""
        return datetime.now(config.TZ).strftime("%H.%M")

    def _group_by_date(self, bookings: list[dict]) -> dict:
        """Flat list -> {date: {room: [{'time','name'}, ...]}}."""
        grouped: dict = {}
        for b in bookings:
            grouped.setdefault(b["date"], {}).setdefault(b["room"], []).append(
                {"time": b["time"], "name": b["name"]}
            )
        return grouped

    def _available_for_date(self, rooms_booked: dict, filter_past: bool) -> dict:
        """Hitung slot kosong untuk satu tanggal."""
        booked_times = {room: {b["time"] for b in lst} for room, lst in rooms_booked.items()}
        result = {}
        for room in config.ROOMS:
            slots = [t for t in config.TIME_SLOTS if t not in booked_times.get(room, set())]
            if filter_past:
                now = self._now_hm()
                slots = [t for t in slots if t.split(" ")[0] > now]
            result[room] = sorted(slots)
        return result

    def _is_valid_date(self, d: str) -> bool:
        try:
            return self._parse_date(d) >= self._today()
        except ValueError:
            return False

    def _is_valid_time(self, d: str, t: str) -> bool:
        if d != self._today().strftime("%d/%m/%Y"):
            return True
        # t.split(" ")[0] = jam MULAI ("08.00"), bukan jam akhir
        return t.split(" ")[0] >= self._now_hm()

    # ---- endpoint logic ----

    async def get_booked_rooms(self) -> tuple[dict, int]:
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        today = self._today()
        future = {d: r for d, r in grouped.items() if self._parse_date(d) >= today}
        if future:
            return {"bookedRoom": future, "message": "Successfully retrieved the booked room."}, 200
        return {"bookedRoom": {}, "message": "Booked room not found"}, 404

    async def get_booked_by_date(self, date_str: str) -> tuple[dict, int]:
        formatted = self._format_date(date_str)
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        if formatted in grouped:
            return {"bookedRoom": grouped[formatted], "message": "Successfully retrieved the booked room by date."}, 200
        return {"bookedRoom": {}, "message": "There's no booked room right now"}, 404

    async def get_available_rooms(self) -> tuple[dict, int]:
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        today = self._today()
        dates = sorted(d for d in grouped if self._parse_date(d) >= today)
        if not dates:
            return {"roomAvailable": {}, "message": "There's no available room right now"}, 404
        output = {}
        for d in dates:
            is_today = d == today.strftime("%d/%m/%Y")
            output[d] = self._available_for_date(grouped.get(d, {}), is_today)
        return {"roomAvailable": output, "message": "Successfully retrieved the available room."}, 200

    async def get_available_by_date(self, date_str: str) -> tuple[dict, int]:
        formatted = self._format_date(date_str)
        if self._parse_date(formatted) < self._today():
            return {"roomAvailable": {}, "message": "There's no available room right now"}, 404
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        is_today = formatted == self._today().strftime("%d/%m/%Y")
        avail = self._available_for_date(grouped.get(formatted, {}), is_today)
        return {"roomAvailable": avail, "message": "Successfully retrieved the available room by date."}, 200

    async def book_room(self, npm: int, room: str, date: str, time: str) -> tuple[dict, int]:
        # Hanya cek data mahasiswa (room/date/time kosong)
        if room is None and date is None and time is None:
            try:
                student = await self.scraper.get_student_info(npm)
            except StudentNotFoundError:
                return {"message": "Oooops...  Your NPM/NPP is not registered."}, 404
            return {"npm": npm, "name": student["name"]}, 200

        if room not in config.ROOMS:
            return {"message": "Valid rooms field are Discussion Room 1, Discussion Room 2, Discussion Room 3, or Leisure Room 1"}, 400
        if not self._is_valid_date(date):
            return {"message": "Please use DD/MM/YYYY format for 'date' field"}, 400
        if time not in config.TIME_SLOTS:
            return {"message": "Valid time slots are 08.00 - 09.30 WIB, 09.30 - 11.00 WIB, 11.00 - 12.30 WIB, 12.30 - 14.00 WIB, 14.00 - 15.30 WIB, 15.30 - 17.00 WIB, or 17.00 - 18.30 WIB"}, 400
        if not self._is_valid_time(date, time):
            return {"message": "Cannot book room at this time"}, 400

        try:
            student = await self.scraper.get_student_info(npm)
        except StudentNotFoundError:
            return {"message": "Oooops...  Your NPM/NPP is not registered."}, 404

        message = await self.scraper.submit_booking(
            npm, student["name"], student["email"], student["token"], room, date, time
        )
        status = 400 if message == "Booking room failed." else 200
        return {"npm": npm, "name": student["name"], "message": message}, status
```

- [ ] **Step 4: Jalankan test, pastikan pass**

```bash
python3 -m pytest tests/test_service.py -q
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add app/booking/service.py tests/test_service.py
git commit -m "feat: add RoomService business logic"
```

---

### Task 4: Routes + app wiring (hapus plagiarisme)

**Files:**
- Create: `app/booking/routes.py`
- Modify: `app/__init__.py`
- Delete: `app/main.py`, `app/routes.py`

**Interfaces:**
- Consumes: `RoomService`, `BookingScraper`, `config`
- Produces: `router` (APIRouter) yang di-import `app/__init__.py`

- [ ] **Step 1: Tulis `app/booking/routes.py`**

```python
"""FastAPI router: wiring HTTP ke RoomService. Tanpa logika bisnis."""

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.booking.scraper import BookingScraper
from app.booking.service import RoomService

router = APIRouter()
service = RoomService(BookingScraper())


@router.get(
    "/booked",
    tags=["BOOKED ROOM"],
    summary="Lihat semua ruang yang sudah dipesan",
    description="Mengembalikan data pemesanan ruang, dikelompokkan per tanggal dan ruang.",
)
async def all_booked():
    data, status = await service.get_booked_rooms()
    return JSONResponse(content=data, status_code=status)


@router.get(
    "/booked/{date}",
    tags=["BOOKED ROOM"],
    summary="Lihat ruang yang dipesan pada tanggal tertentu",
    description="`date` format DDMmYYYY, contoh `29042024` untuk 29/04/2024.",
)
async def booked_by_date(date: str):
    data, status = await service.get_booked_by_date(date)
    return JSONResponse(content=data, status_code=status)


@router.get(
    "/available",
    tags=["AVAILABLE ROOM"],
    summary="Lihat semua ruang yang tersedia",
    description="Mengembalikan slot waktu kosong per ruang, per tanggal (mulai hari ini).",
)
async def available_rooms():
    data, status = await service.get_available_rooms()
    return JSONResponse(content=data, status_code=status)


@router.get(
    "/available/{date}",
    tags=["AVAILABLE ROOM"],
    summary="Lihat ruang yang tersedia pada tanggal tertentu",
    description="`date` format DDMmYYYY, contoh `29042024` untuk 29/04/2024.",
)
async def available_rooms_by_date(date: str):
    data, status = await service.get_available_by_date(date)
    return JSONResponse(content=data, status_code=status)


class BookingRequest(BaseModel):
    npm: int
    room: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None


@router.post(
    "/booking",
    tags=["BOOKING ROOM"],
    summary="Pesan ruang (atau cek data mahasiswa)",
    description=(
        "Jika `room`, `date`, `time` dikosongkan, endpoint hanya mengembalikan "
        "nama & NPM. Jika diisi, endpoint memproses pemesanan ruang."
    ),
)
async def booking_room(data: BookingRequest):
    body, status = await service.book_room(data.npm, data.room, data.date, data.time)
    return JSONResponse(content=body, status_code=status)
```

- [ ] **Step 2: Update `app/__init__.py`**

```python
from fastapi import FastAPI

from app.booking.routes import router

app = FastAPI(
    title="Library Universitas Atma Jaya Yogyakarta",
    version="0.2.0",
    description="API tidak resmi untuk pemesanan ruang perpustakaan UAJY",
    docs_url="/",
    redoc_url="/redocs",
)

app.include_router(router)
```

- [ ] **Step 3: Hapus file lama**

```bash
rm app/main.py app/routes.py
```

- [ ] **Step 4: Verifikasi app bisa boot & router terdaftar**

```bash
python3 -c "from app import app; paths = sorted(r.path for r in app.routes); print(paths)"
```

Expected: list berisi `/booked`, `/booked/{date}`, `/available`, `/available/{date}`, `/booking` (dan route docs default). Tidak ada `/turnitin`.

- [ ] **Step 5: Commit**

```bash
git add app/booking/routes.py app/__init__.py
git rm app/main.py app/routes.py
git commit -m "refactor: wire routes, remove plagiarism endpoints"
```

---

### Task 5: README + vercel.json + smoke test

**Files:**
- Modify: `README.md`
- Modify: `vercel.json` (tinjau; sudah benar, biarkan bila tidak perlu)

- [ ] **Step 1: Tulis ulang `README.md` (Bahasa Indonesia)**

```markdown
# Library Atma Jaya Yogyakarta University (UAJY)

API tidak resmi untuk pemesanan ruang perpustakaan Universitas Atma Jaya Yogyakarta (UAJY).

API ini dibuat dengan melakukan web scraping pada:

- [FORM BOOKING DIGITAL LIBRARY ROOM](http://form.lib.uajy.ac.id/booking/default.aspx)
- [CEK PENGGUNAAN RUANG](http://form.lib.uajy.ac.id/booking/CekJadwal.aspx)

## Fitur

- Lihat daftar ruang yang sudah dipesan (semua / per tanggal)
- Lihat daftar ruang yang tersedia (semua / per tanggal)
- Pemesanan ruang

## Prasyarat

- Python 3.9 atau lebih baru
- `pip3`

## Instalasi

```bash
git clone https://github.com/Xractz/lib-uajy.git
cd lib-uajy
pip3 install -r requirements.txt
```

## Menjalankan (lokal)

```bash
python3 run.py
```

Aplikasi berjalan di `http://localhost:8000`. Dokumentasi Swagger tersedia di root (`/`).

## Dokumentasi API

API ini didokumentasikan menggunakan **Swagger**:

**[API DOCUMENTATION](https://lib-uajy.vercel.app/)**

## Endpoint

| Method | Endpoint           | Deskripsi                                  |
|--------|--------------------|--------------------------------------------|
| GET    | `/booked`          | Semua ruang yang sudah dipesan             |
| GET    | `/booked/{date}`   | Ruang dipesan pada tanggal tertentu        |
| GET    | `/available`       | Semua ruang yang tersedia                  |
| GET    | `/available/{date}`| Ruang tersedia pada tanggal tertentu       |
| POST   | `/booking`         | Pesan ruang / cek data mahasiswa           |

`{date}` menggunakan format `DDMMYYYY` (contoh `29042024` untuk 29/04/2024).

## Struktur Proyek

```
app/
├── __init__.py        # Setup aplikasi FastAPI
├── config.py          # Konstanta (URL, ruang, slot waktu)
└── booking/
    ├── scraper.py     # BookingScraper (HTTP + parsing)
    ├── service.py     # RoomService (logika bisnis)
    └── routes.py      # Router FastAPI
```

## Menjalankan Tes

```bash
pip3 install pytest pytest-asyncio
python3 -m pytest -q
```
```

- [ ] **Step 2: Tinjau `vercel.json`**

Struktur sekarang tetap memakai `run.py` sebagai entry point dan `@vercel/python`, jadi config yang ada sudah benar:

```json
{
  "version": 2,
  "builds": [
    { "src": "run.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "run.py" }
  ]
}
```

Tidak ada perubahan. (Jika build gagal karena `scrapling[fetchers]` butuh kompilasi `curl_cffi`, tambah `"buildCommand"` tidak diperlukan — `@vercel/python` otomatis `pip install -r requirements.txt`.)

- [ ] **Step 3: Smoke test — boot server & buka Swagger**

```bash
python3 -m uvicorn app:app --port 8123 &
sleep 3
curl -s http://localhost:8123/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['title']); print(sorted(d['paths'].keys()))"
kill %1
```

Expected: title tercetak, dan `paths` berisi endpoint booking saja (tanpa turnitin).

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README in Indonesian"
```

---

## Self-Review

**Spec coverage:**
- OOP composition (bukan inheritance) → Task 2 & 3 (scraper di-inject). ✅
- Scrapling ganti requests+re → Task 2. ✅
- Hapus plagiarisme → Task 4 (rm + tidak ada turnitin di routes). ✅
- Struktur modular per domain → Task 1 & 4. ✅
- README Bahasa Indonesia → Task 5. ✅
- Swagger diperbarui → Task 4 (summary/description baru, version 0.2.0). ✅
- `python3`/`pip3` → README & semua command. ✅
- vercel.json → Task 5 (ditinjau, tidak berubah). ✅

**Type consistency:** `parse_token`/`parse_schedule_rows`/`parse_max_page` dipanggil dengan nama yang sama di scraper (Task 2) dan test (Task 2). `RoomService` method name cocok antara service (Task 3), routes (Task 4), dan test (Task 3). ✅

**Catatan risiko:** `tests/test_service.py` memakai `pytest-asyncio` (marker `@pytest.mark.asyncio`). Dipasang di Task 5 langkah tes. `Selector` diimport dari `scrapling.parser` (diverifikasi via context7).
