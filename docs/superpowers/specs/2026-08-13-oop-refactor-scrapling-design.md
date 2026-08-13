# Design Doc: Refactor OOP + Scrapling

**Tanggal:** 2026-08-13  
**Status:** Approved  

---

## Latar Belakang

Proyek ini adalah unofficial REST API untuk pemesanan ruang perpustakaan UAJY, dibangun dengan FastAPI dan web scraping ke `form.lib.uajy.ac.id`. Codebase saat ini menggunakan deep inheritance (`Token → FetchData → Room`) dan `requests` + `re` (regex) untuk scraping. Tujuan refactor:

1. Terapkan OOP dengan **composition** (bukan inheritance) agar mudah dikembangkan dev lain
2. Ganti `requests` + `re` dengan **Scrapling** untuk scraping lebih robust
3. Hapus fitur **Plagiarisme** (tidak dibutuhkan lagi)
4. Struktur folder **modular per domain**
5. Perbarui README (Bahasa Indonesia) dan Swagger docs

---

## Struktur Folder

```
app/
├── __init__.py          # FastAPI app setup (title, version, router)
├── config.py            # Semua konstanta: URL, ROOMS, TIME_SLOTS, timezone
└── booking/
    ├── __init__.py      # (kosong)
    ├── scraper.py       # BookingScraper — HTTP + parsing HTML via Scrapling
    ├── service.py       # RoomService — logika bisnis & transformasi data
    └── routes.py        # FastAPI router + Pydantic models

run.py                   # Entry point uvicorn
requirements.txt         # scrapling[fetchers], fastapi, uvicorn, python-multipart
vercel.json              # Tidak berubah
README.md                # Bahasa Indonesia, diperbarui
docs/superpowers/specs/  # Design docs
```

---

## Desain Class

### `config.py`
Satu file untuk semua nilai yang mungkin berubah:
```python
BASE_URL = "http://form.lib.uajy.ac.id/booking/"
URL_DEFAULT = BASE_URL + "default.aspx"
URL_JADWAL  = BASE_URL + "CekJadwal.aspx"

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

TIMEZONE = "Asia/Jakarta"
```

### `booking/scraper.py` — `BookingScraper`
Satu-satunya class yang tahu cara berbicara dengan website UAJY. Tidak ada logika bisnis di sini.

```python
class BookingScraper:
    def fetch_token(self, url: str) -> dict
    # GET url → return {"__VIEWSTATE": ..., "__VIEWSTATEGENERATOR": ..., "__EVENTVALIDATION": ...}
    # Pakai Scrapling: page.css('#__VIEWSTATE::attr(value)').get()

    def fetch_max_page(self) -> int
    # GET CekJadwal → parse pagination, return angka halaman terakhir

    def fetch_schedule_page(self, page: int, token: dict) -> list[dict]
    # POST CekJadwal dengan token + Page$N → parse tr.RowStyle
    # Return: [{"room": ..., "date": ..., "time": ..., "name": ...}, ...]

    def get_student_info(self, npm: int, token: dict) -> dict | None
    # POST default.aspx dengan npm → ekstrak nama & email
    # Return: {"name": ..., "email": ...} atau None jika tidak ditemukan

    def submit_booking(self, payload: dict, token: dict) -> str
    # POST default.aspx dengan payload lengkap → ekstrak pesan dari alert()
    # Return: string pesan dari server
```

**Catatan Scrapling:** Buat instance `Fetcher` baru per method call (stateless). Untuk request yang butuh session cookie (POST setelah GET), gunakan `Fetcher` dengan session yang sama dalam satu method.

### `booking/service.py` — `RoomService`
Seluruh logika bisnis ada di sini. Tidak tahu soal HTTP.

```python
class RoomService:
    def __init__(self, scraper: BookingScraper)
    # Dependency injection — mudah di-mock untuk testing

    async def _fetch_all_bookings(self) -> list[dict]
    # Private: ambil semua halaman, return flat list booking

    async def get_booked_rooms(self) -> tuple[dict, int]
    async def get_booked_by_date(self, date_str: str) -> tuple[dict, int]
    async def get_available_rooms(self) -> tuple[dict, int]
    async def get_available_by_date(self, date_str: str) -> tuple[dict, int]
    async def book_room(self, npm: int, room: str, date: str, time: str) -> tuple[dict, int]
    async def get_student_info(self, npm: int) -> tuple[dict, int]
```

**Return convention:** semua method return `(dict, status_code)` — konsisten dengan pattern sekarang, mudah dipahami dev lain.

### `booking/routes.py`
Hanya wiring: Router → Service → JSONResponse. Tidak ada logika bisnis, tidak ada try/except (exception ditangkap di service).

---

## Error Handling

```
BookingScraper  →  raise exception jika HTTP gagal atau elemen tidak ditemukan
RoomService     →  tangkap exception, return ({"message": ...}, status_code)
Routes          →  JSONResponse(content, status_code) — bersih, tanpa try/except
```

Exception yang didefinisikan di `scraper.py`:
- `ScraperError` — error umum HTTP/parsing
- `StudentNotFoundError` — NPM tidak terdaftar

---

## Yang Dihapus

| Item | Alasan |
|------|--------|
| Class `Plagiarism` | Tidak dibutuhkan lagi (sesuai permintaan) |
| Endpoint `/turnitin`, `/turnitin/status` | Dihapus bersama Plagiarism |
| Library `requests` | Diganti Scrapling |
| Library `pytz` | Diganti `datetime.timezone` + `zoneinfo` (stdlib Python 3.9+) |
| Deep inheritance `Token → FetchData → Room` | Diganti composition |

---

## Dependencies Baru

```
# requirements.txt
fastapi==0.110.2
uvicorn==0.29.0
python-multipart==0.0.9
scrapling[fetchers]
```

---

## Swagger / OpenAPI

- Semua tag, summary, description tetap ada dan diperbarui
- Tag diubah: hapus `PLAGIARISM CHECKER`
- Deskripsi app diperbarui di `app/__init__.py`
- `docs_url="/"` tetap (akses Swagger di root)

---

## README

- Bahasa Indonesia seluruhnya
- Daftar endpoint diperbarui (tanpa turnitin)
- Cara install dan run dengan `python3` dan `pip3`
- Contoh response per endpoint
