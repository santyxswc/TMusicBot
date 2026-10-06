# 🎧 Bot de Telegram para Descargar Música

Un bot de Telegram que permite buscar y descargar música utilizando la API de Deezer para búsqueda y yt-dlp para descargas desde YouTube.

## ✨ Características

- 🎵 Búsqueda de canciones por nombre
- 👤 Búsqueda por artista (muestra lista de artistas y sus canciones)
- 💿 Búsqueda por álbum (muestra lista de álbumes y sus canciones)
- ⏬ Descarga automática en formato MP3
- 📱 Interfaz intuitiva con botones inline
- 🎨 Emojis y formato bonito en los mensajes

## 📋 Requisitos

- Python 3.8 o superior
- ffmpeg (para convertir audio a MP3)

## 🔧 Instalación

### 1. Instalar dependencias de Python

```bash
python -m pip install -r requirements.txt
```

### 2. Instalar FFmpeg

**Windows:**
1. Descarga FFmpeg desde: https://www.gyan.dev/ffmpeg/builds/
2. Extrae el archivo ZIP
3. Agrega la carpeta `bin` al PATH del sistema

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Configurar el Token de Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot` y sigue las instrucciones
3. Copia el token que te proporciona
4. Crea un archivo `.env` en la raíz del proyecto (o copia `.env.example`):

```env
TELEGRAM_TOKEN=tu_token_aqui
```

Alternativamente, puedes editar directamente el archivo `config.py` y reemplazar `AQUÍ_TU_TOKEN`.

## 🚀 Uso

### Iniciar el bot

```bash
python main.py
```

Si todo está configurado correctamente, verás:
```
✅ Bot de música corriendo...
📱 Abre Telegram y escribe /start para comenzar
⏹️  Presiona Ctrl+C para detener el bot
```

### Comandos disponibles

- `/start` - Muestra el menú principal con opciones de búsqueda
- `/cancel` - Cancela la operación actual

### Flujo de uso

1. Envía `/start` al bot
2. Selecciona el tipo de búsqueda:
   - 🎵 **Buscar por nombre**: Escribe el nombre de la canción
   - 👤 **Buscar por artista**: Escribe el nombre del artista → Selecciona un artista → Selecciona una canción
   - 💿 **Buscar por álbum**: Escribe el nombre del álbum → Selecciona un álbum → Selecciona una canción
3. El bot descargará y enviará el archivo de audio

## 📁 Estructura del Proyecto

```
Telegram_bot/
├── main.py                 # Archivo principal del bot
├── config.py              # Configuración (token, rutas, etc.)
├── requirements.txt       # Dependencias de Python
├── .env.example          # Plantilla para variables de entorno
├── handlers/             # Handlers de comandos y conversaciones
│   ├── start_handler.py  # Handler del comando /start
│   └── search_handler.py # Handler de búsqueda y selección
├── services/             # Servicios de lógica de negocio
│   ├── music_search.py   # Búsqueda en Deezer API
│   └── downloader.py     # Descarga con yt-dlp
└── downloads/            # Carpeta temporal para descargas
```

## 🔍 APIs Utilizadas

- **Deezer API**: Para búsqueda de música (no requiere autenticación)
- **yt-dlp**: Para descargar audio desde YouTube

## ⚠️ Notas Importantes

1. **Descargas temporales**: Los archivos se eliminan automáticamente después de enviarse al usuario
2. **Límites**: Por defecto muestra hasta 10 resultados por búsqueda
3. **Formato**: Los archivos se convierten automáticamente a MP3 a 192kbps
4. **Disponibilidad**: La descarga depende de la disponibilidad del contenido en YouTube

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError"
- Asegúrate de haber instalado todas las dependencias: `python -m pip install -r requirements.txt`

### Error: "ffmpeg not found"
- Instala ffmpeg y asegúrate de que esté en el PATH del sistema

### El bot no responde
- Verifica que el token esté configurado correctamente
- Comprueba que el bot esté corriendo (`python main.py`)
- Revisa los logs en la consola para ver errores

### No se pueden descargar canciones
- Asegúrate de tener conexión a internet
- Verifica que ffmpeg esté instalado
- Comprueba los permisos de escritura en la carpeta `downloads/`

## 📝 Licencia

Este proyecto es de código abierto y está disponible para uso personal y educativo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes sugerencias, no dudes en crear un issue o pull request.
