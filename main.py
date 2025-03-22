import yt_dlp
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from io import BytesIO

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Descarga de Videos de Youtube"}

# Almacenar cookies en memoria
cookie_storage = None

@app.post("/upload_cookies/")
async def upload_cookies(cookies_file: UploadFile = File(...)):
    global cookie_storage
    # Leer el archivo de cookies y almacenarlo en memoria
    cookie_storage = await cookies_file.read()
    
    return {"message": "Cookies almacenadas en memoria"}

@app.get("/info_video/")
def info_video(video_url: str):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)

    title = info_dict.get('title', 'Título no disponible')
    author = info_dict.get('uploader', 'Autor no disponible')
        
    return {
        "titulo_video": title,
        "autor_video": author,
    }

@app.get("/download/")
async def download_video(video_url: str):
    if cookie_storage is None:
        raise HTTPException(status_code=400, detail="No se han subido cookies")

    download_folder = "downloads/"
    os.makedirs(download_folder, exist_ok=True)

    # Guardar las cookies en un archivo temporal en memoria
    with BytesIO(cookie_storage) as cookie_file:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a][abr<=128]',
            'outtmpl': download_folder + '%(title)s.%(ext)s',
            'cookies': cookie_file  # Usar el flujo de bytes
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al descargar el video: " + str(e))

    # Obtener información del video
    info_dict = ydl.extract_info(video_url, download=False)
    file_name = f"{info_dict.get('title')}.m4a"
    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
