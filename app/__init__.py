from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Library Universitas Atma Jaya Yogyakarta",
    version="0.1.0", 
    description="API untuk peminjaman buku di perpustakaan dan cek plagiarisme UAJY", 
    docs_url="/",
    redoc_url="/redocs",
)

app.include_router(router)