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
    # Crear un archivo temporal para las cookies
    with tempfile.NamedTemporaryFile(delete=True) as temp_cookie_file:
        temp_cookie_file.write(await cookies_file.read())
        temp_cookie_file.flush()  # Asegurarse de que los datos estén escritos
        # Retornar el nombre del archivo temporal o un ID único
        return {"cookie_file": temp_cookie_file.name}

@app.get("/info_video/")
def info_video(video_url: str):
    # Opciones de configuración para obtener información sobre el video
    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]'  # Filtrar por m4a y bitrate medio (<=128 kbps)
    }

    # Obtener información del video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)  # download=False para no descargar

    # Extraer información relevante
    title = info_dict.get('title', 'Título no disponible')
    author = info_dict.get('uploader', 'Autor no disponible')
        
    # Retornar el título del video
    return {
        "titulo_video": title,
        "autor_video": author,
    }

@app.get("/download/")
async def download_video(video_url: str, cookie_file: str):
    download_folder = "downloads/"
    
    # Asegurarse de que el directorio de descargas exista
    os.makedirs(download_folder, exist_ok=True)

    # Opciones de configuración para filtrar y descargar formatos específicos
    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',  # Filtrar por m4a y bitrate medio (<=128 kbps)
        'outtmpl': download_folder + '%(title)s.%(ext)s',  # Nombre del archivo como el título del video
        'cookies': cookie_file  # Usar el archivo de cookies proporcionado
    }

    # Intentar descargar el audio
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al descargar el video: " + str(e))

    # Obtener información del video
    info_dict = ydl.extract_info(video_url, download=False)  # download=False para no descargar

    # Extraer información relevante
    file_name = f"{info_dict.get('title')}.m4a"
    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
