import yt_dlp
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uuid

app = FastAPI()

# Variable global para almacenar la ruta del archivo de cookies
cookie_file = None

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Descarga de Videos de Youtube"}

@app.post("/upload_cookies/")
async def upload_cookies(cookies_file: UploadFile = File(...)):
    global cookie_file
    cookie_storage = await cookies_file.read()
    
    if not cookie_storage.startswith(b"# HTTP Cookie File") and not cookie_storage.startswith(b"# Netscape HTTP Cookie File"):
        raise HTTPException(status_code=400, detail="El archivo de cookies no tiene el formato correcto.")
    
    temp_cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    temp_cookie_file.write(cookie_storage)
    temp_cookie_file.close()

    cookie_file = temp_cookie_file.name
    print(f"Archivo de cookies guardado en: {cookie_file}")  # Mensaje de depuración

    return {"cookie_file": cookie_file}

@app.get("/download/")
async def download_video(video_url: str):
    global cookie_file

    if not cookie_file or not os.path.exists(cookie_file):
        raise HTTPException(status_code=400, detail="No se han subido cookies")

    download_folder = "downloads/"
    os.makedirs(download_folder, exist_ok=True)

    # Configuración más detallada de yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',  # Cambio en la selección de formato
        'outtmpl': os.path.join(download_folder, '%(title)s-%(id)s.%(ext)s'),
        'cookies': cookie_file,
        'verbose': True,
        'no_warnings': False,
        'ignoreerrors': False,
        'no_color': True,
        'socket_timeout': 30,  # Timeout de 30 segundos
        'retries': 3,  # Número de reintentos
        'fragment_retries': 3,
        'extractor_retries': 3,
        'force_generic_extractor': True,  # Forzar extractor genérico
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer información sin descargar
            info_dict = ydl.extract_info(video_url, download=False)
            
            # Imprimir información detallada para depuración
            print("Información del video:", info_dict)
            
            # Descargar el video
            ydl.download([video_url])
    except Exception as e:
        print(f"Error al descargar el video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al descargar el video: {str(e)}")
    finally:
        # Limpiar archivo de cookies
        if os.path.exists(cookie_file):
            os.remove(cookie_file)

    # Generar nombre de archivo único
    file_name = f"{info_dict.get('title', 'video')}-{info_dict.get('id', str(uuid.uuid4()))}.{info_dict.get('ext', 'm4a')}"
    file_path = os.path.join(download_folder, file_name)

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No se pudo encontrar el archivo descargado")

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
