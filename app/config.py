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
]

TZ = ZoneInfo("Asia/Jakarta")
