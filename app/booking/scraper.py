"""Akses HTTP dan parsing HTML website booking UAJY via Scrapling."""

import re

from scrapling.fetchers import FetcherSession

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
