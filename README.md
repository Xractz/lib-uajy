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

| Method | Endpoint            | Deskripsi                            |
|--------|---------------------|--------------------------------------|
| GET    | `/booked`           | Semua ruang yang sudah dipesan       |
| GET    | `/booked/{date}`    | Ruang dipesan pada tanggal tertentu  |
| GET    | `/available`        | Semua ruang yang tersedia            |
| GET    | `/available/{date}` | Ruang tersedia pada tanggal tertentu |
| POST   | `/booking`          | Pesan ruang / cek data mahasiswa     |

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
