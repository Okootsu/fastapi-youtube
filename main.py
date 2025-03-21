import yt_dlp

import os

from fastapi import FastAPI

from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Descarga de Videos de Youtube"}


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
def download_video(video_url: str):

    download_folder = "downloads/"

    # Opciones de configuración para filtrar y descargar formatos específicos
    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',  # Filtrar por m4a y bitrate medio (<=128 kbps)
        'outtmpl': download_folder +'%(title)s.%(ext)s',  # Nombre del archivo como el título del video
    }

    # Descargar el audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])



    # Obtener información del video
    info_dict = ydl.extract_info(video_url, download=False)  # download=False para no descargar

    # Extraer información relevante
    file_name = f"{info_dict.get('title')}.m4a"

    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
