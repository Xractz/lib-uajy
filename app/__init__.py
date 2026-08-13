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
