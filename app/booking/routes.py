"""FastAPI router: wiring HTTP ke RoomService. Tanpa logika bisnis."""

from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.booking.scraper import BookingScraper
from app.booking.service import RoomService

router = APIRouter()
service = RoomService(BookingScraper())


# ---- Schema (dokumentasi Swagger) ----

class BookingSlot(BaseModel):
    """Satu slot terpakai: waktu + nama pemesan."""
    time: str
    name: str


class BookedRoomResponse(BaseModel):
    """Respons `/booked`: pemesanan dikelompokkan per tanggal lalu per ruang."""
    bookedRoom: Dict[str, Dict[str, List[BookingSlot]]]
    message: str


class BookedRoomByDateResponse(BaseModel):
    """Respons `/booked/{date}`: pemesanan dikelompokkan per ruang."""
    bookedRoom: Dict[str, List[BookingSlot]]
    message: str


class AvailableRoomResponse(BaseModel):
    """Respons `/available`: slot kosong per tanggal lalu per ruang."""
    roomAvailable: Dict[str, Dict[str, List[str]]]
    message: str


class AvailableRoomByDateResponse(BaseModel):
    """Respons `/available/{date}`: slot kosong per ruang."""
    roomAvailable: Dict[str, List[str]]
    message: str


class BookingRequest(BaseModel):
    npm: int
    room: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None


class BookingSuccess(BaseModel):
    npm: int
    name: str
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    message: str


BookingResponse = Union[BookingSuccess, ErrorResponse]


# ---- Endpoint ----

@router.get(
    "/booked",
    response_model=BookedRoomResponse,
    tags=["BOOKED ROOM"],
    summary="Lihat semua ruang yang sudah dipesan",
    description="Mengembalikan data pemesanan ruang, dikelompokkan per tanggal dan ruang.",
    responses={404: {"model": ErrorResponse, "description": "Tidak ada ruang yang dipesan"}},
)
async def all_booked(response: Response):
    data, status = await service.get_booked_rooms()
    response.status_code = status
    return data


@router.get(
    "/booked/{date}",
    response_model=BookedRoomByDateResponse,
    tags=["BOOKED ROOM"],
    summary="Lihat ruang yang dipesan pada tanggal tertentu",
    description="`date` format DDMmYYYY, contoh `29042024` untuk 29/04/2024.",
    responses={404: {"model": ErrorResponse, "description": "Tidak ada ruang yang dipesan pada tanggal tersebut"}},
)
async def booked_by_date(date: str, response: Response):
    data, status = await service.get_booked_by_date(date)
    response.status_code = status
    return data


@router.get(
    "/available",
    response_model=AvailableRoomResponse,
    tags=["AVAILABLE ROOM"],
    summary="Lihat semua ruang yang tersedia",
    description="Mengembalikan slot waktu kosong per ruang, per tanggal (mulai hari ini).",
    responses={404: {"model": ErrorResponse, "description": "Tidak ada ruang yang tersedia"}},
)
async def available_rooms(response: Response):
    data, status = await service.get_available_rooms()
    response.status_code = status
    return data


@router.get(
    "/available/{date}",
    response_model=AvailableRoomByDateResponse,
    tags=["AVAILABLE ROOM"],
    summary="Lihat ruang yang tersedia pada tanggal tertentu",
    description="`date` format DDMmYYYY, contoh `29042024` untuk 29/04/2024.",
    responses={404: {"model": ErrorResponse, "description": "Tidak ada ruang yang tersedia pada tanggal tersebut"}},
)
async def available_rooms_by_date(date: str, response: Response):
    data, status = await service.get_available_by_date(date)
    response.status_code = status
    return data


@router.post(
    "/booking",
    response_model=BookingResponse,
    tags=["BOOKING ROOM"],
    summary="Pesan ruang (atau cek data mahasiswa)",
    description=(
        "Jika `room`, `date`, `time` dikosongkan, endpoint hanya mengembalikan "
        "nama & NPM. Jika diisi, endpoint memproses pemesanan ruang."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Data booking tidak valid"},
        404: {"model": ErrorResponse, "description": "NPM/NPP tidak terdaftar"},
    },
)
async def booking_room(data: BookingRequest, response: Response):
    body, status = await service.book_room(data.npm, data.room, data.date, data.time)
    response.status_code = status
    return body
