import yt_dlp
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

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

    ydl_opts = {
        'format': 'bestaudio[ext=m4a][abr<=128]',
        'outtmpl': download_folder + '%(title)s.%(ext)s',
        'cookies': cookie_file,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
        },
        'verbose': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"Error al descargar el video: {str(e)}")  # Mensaje de depuración
        raise HTTPException(status_code=500, detail="Error al descargar el video: " + str(e))
    finally:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)

    info_dict = ydl.extract_info(video_url, download=False)
    file_name = f"{info_dict.get('title')}.m4a"
    file_path = os.path.join(download_folder, file_name)

    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)
