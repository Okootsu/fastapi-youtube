import yt_dlp
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/upload_cookies/")
async def upload_cookies(cookies_file: UploadFile = File(...)):
    # Leer el archivo de cookies y almacenarlo en un archivo temporal
    cookie_storage = await cookies_file.read()
    temp_cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    temp_cookie_file.write(cookie_storage)
    temp_cookie_file.close()  # Cerrar el archivo para que yt-dlp pueda leerlo

    return {"cookie_file": temp_cookie_file.name}  # Retorna la ruta del archivo temporal

@app.get("/download/")
async def download_video(video_url: str):
    # Verifica que el archivo de cookies existe
    if not os.path.exists(cookie_file):
        raise HTTPException(status_code=400, detail="No se han subido cookies")

    download_folder = "downloads/"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',
        'outtmpl': download_folder + '%(title)s.%(ext)s',
        'cookies': cookie_file  # Usar el archivo temporal de cookies
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
