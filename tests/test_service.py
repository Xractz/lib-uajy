from datetime import datetime

import pytest

from app import config
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
