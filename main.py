import yt_dlp
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Variable global para almacenar la ruta del archivo de cookies
cookie_file = None

@app.post("/upload_cookies/")
async def upload_cookies(cookies_file: UploadFile = File(...)):
    global cookie_file  # Usar la variable global
    # Leer el archivo de cookies y almacenarlo en un archivo temporal
    cookie_storage = await cookies_file.read()
    
    # Verificar que el archivo de cookies tenga el formato correcto
    if not cookie_storage.startswith(b"# HTTP Cookie File") and not cookie_storage.startswith(b"# Netscape HTTP Cookie File"):
        raise HTTPException(status_code=400, detail="El archivo de cookies no tiene el formato correcto.")
    
    temp_cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    temp_cookie_file.write(cookie_storage)
    temp_cookie_file.close()  # Cerrar el archivo para que yt-dlp pueda leerlo

    cookie_file = temp_cookie_file.name  # Guardar la ruta del archivo temporal

    return {"cookie_file": cookie_file}  # Retorna la ruta del archivo temporal


@app.get("/download/")
async def download_video(video_url: str):
    global cookie_file  # Usar la variable global

    # Verifica que el archivo de cookies existe
    if not cookie_file or not os.path.exists(cookie_file):
        raise HTTPException(status_code=400, detail="No se han subido cookies")

    download_folder = "downloads/"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',
        'outtmpl': download_folder + '%(title)s.%(ext)s',
        'cookies': cookie_file,  # Usar el archivo temporal de cookies
        'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
    }
        'verbose': True,  # Para obtener más detalles sobre el proceso
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al descargar el video: " + str(e))
    finally:
        # Limpia el archivo de cookies después de usarlo
        if os.path.exists(cookie_file):
            os.remove(cookie_file)

    # Obtener información del video
    info_dict = ydl.extract_info(video_url, download=False)
    file_name = f"{info_dict.get('title')}.m4a"
    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
