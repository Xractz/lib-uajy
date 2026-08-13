"""Logika bisnis pemesanan ruang. Tidak tahu soal HTTP."""

from datetime import datetime, date

from app import config
from app.booking.scraper import BOOKING_FAILED_MESSAGE, BookingScraper, StudentNotFoundError


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
            return {"bookedRoom": future, "message": "Berhasil mengambil data ruang yang dipesan."}, 200
        return {"bookedRoom": {}, "message": "Ruang yang dipesan tidak ditemukan."}, 404

    async def get_booked_by_date(self, date_str: str) -> tuple[dict, int]:
        formatted = self._format_date(date_str)
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        if formatted in grouped:
            return {"bookedRoom": grouped[formatted], "message": "Berhasil mengambil data ruang yang dipesan berdasarkan tanggal."}, 200
        return {"bookedRoom": {}, "message": "Tidak ada ruang yang dipesan saat ini."}, 404

    async def get_available_rooms(self) -> tuple[dict, int]:
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        today = self._today()
        dates = sorted(d for d in grouped if self._parse_date(d) >= today)
        if not dates:
            return {"roomAvailable": {}, "message": "Tidak ada ruang yang tersedia saat ini."}, 404
        output = {}
        for d in dates:
            is_today = d == today.strftime("%d/%m/%Y")
            output[d] = self._available_for_date(grouped.get(d, {}), is_today)
        return {"roomAvailable": output, "message": "Berhasil mengambil data ruang yang tersedia."}, 200

    async def get_available_by_date(self, date_str: str) -> tuple[dict, int]:
        formatted = self._format_date(date_str)
        if self._parse_date(formatted) < self._today():
            return {"roomAvailable": {}, "message": "Tidak ada ruang yang tersedia saat ini."}, 404
        bookings = await self.scraper.fetch_all_schedule()
        grouped = self._group_by_date(bookings)
        is_today = formatted == self._today().strftime("%d/%m/%Y")
        avail = self._available_for_date(grouped.get(formatted, {}), is_today)
        return {"roomAvailable": avail, "message": "Berhasil mengambil data ruang yang tersedia berdasarkan tanggal."}, 200

    async def book_room(self, npm: int, room: str, date: str, time: str) -> tuple[dict, int]:
        # Hanya cek data mahasiswa (room/date/time kosong)
        if room is None and date is None and time is None:
            try:
                student = await self.scraper.get_student_info(npm)
            except StudentNotFoundError:
                return {"message": "Oooops... NPM/NPP Anda tidak terdaftar."}, 404
            return {"npm": npm, "name": student["name"]}, 200

        if room not in config.ROOMS:
            return {"message": "Ruang yang valid: Discussion Room 1, Discussion Room 2, Discussion Room 3, atau Leisure Room 1"}, 400
        if not self._is_valid_date(date):
            return {"message": "Gunakan format DD/MM/YYYY untuk kolom 'date'"}, 400
        if time not in config.TIME_SLOTS:
            return {"message": "Slot waktu yang valid: 08.00 - 09.30 WIB, 09.30 - 11.00 WIB, 11.00 - 12.30 WIB, 12.30 - 14.00 WIB, 14.00 - 15.30 WIB, 15.30 - 17.00 WIB, atau 17.00 - 18.30 WIB"}, 400
        if not self._is_valid_time(date, time):
            return {"message": "Tidak dapat memesan ruang pada waktu ini"}, 400

        try:
            student = await self.scraper.get_student_info(npm)
        except StudentNotFoundError:
            return {"message": "Oooops... NPM/NPP Anda tidak terdaftar."}, 404

        message = await self.scraper.submit_booking(
            npm, student["name"], student["email"], student["token"], room, date, time
        )
        status = 400 if message == BOOKING_FAILED_MESSAGE else 200
        return {"npm": npm, "name": student["name"], "message": message}, status
