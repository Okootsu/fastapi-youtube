import yt_dlp
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Descarga de Videos de Youtube"}

@app.post("/upload_cookies/")
async def upload_cookies(cookies_file: UploadFile = File(...)):
    # Crear un directorio para almacenar cookies si no existe
    os.makedirs("cookies", exist_ok=True)
    
    # Crear un archivo permanente para las cookies
    file_path = os.path.join("cookies", cookies_file.filename)
    with open(file_path, "wb") as f:
        f.write(await cookies_file.read())
    
    return {"cookie_file": file_path}

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
async def download_video(video_url: str, cookie_file: str):
    download_folder = "downloads/"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',
        'outtmpl': download_folder + '%(title)s.%(ext)s',
        'cookies': cookie_file
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al descargar el video: " + str(e))

    info_dict = ydl.extract_info(video_url, download=False)
    file_name = f"{info_dict.get('title')}.m4a"
    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
