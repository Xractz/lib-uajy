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
