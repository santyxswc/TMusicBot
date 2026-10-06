"""
Script de verificación para el Bot de Telegram de Música
Verifica que todas las dependencias estén correctamente instaladas
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  [!] Advertencia: Se recomienda Python 3.8 o superior")
        return False
    return True


def check_module(module_name, display_name=None):
    """Verifica si un módulo de Python está instalado"""
    if display_name is None:
        display_name = module_name
    
    try:
        __import__(module_name)
        print(f"[OK] {display_name} instalado")
        return True
    except ImportError:
        print(f"[X] {display_name} NO instalado")
        return False


def check_ffmpeg():
    """Verifica si FFmpeg está instalado y accesible"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extraer versión
            version_line = result.stdout.split('\n')[0]
            print(f"[OK] FFmpeg instalado - {version_line}")
            return True
        else:
            print("[X] FFmpeg NO esta funcionando correctamente")
            return False
    except FileNotFoundError:
        print("[X] FFmpeg NO encontrado en el PATH")
        return False
    except subprocess.TimeoutExpired:
        print("[X] FFmpeg no responde")
        return False
    except Exception as e:
        print(f"[X] Error verificando FFmpeg: {e}")
        return False


def check_token_config():
    """Verifica si el token está configurado"""
    # Verificar archivo .env
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'TELEGRAM_TOKEN=' in content and 'AQUI_TU_TOKEN' not in content:
                print("[OK] Token configurado en .env")
                return True
    
    # Verificar config.py
    try:
        from config import TOKEN
        if TOKEN and TOKEN != "AQUI_TU_TOKEN":
            print("[OK] Token configurado en config.py")
            return True
        else:
            print("[X] Token NO configurado")
            return False
    except:
        print("[X] No se pudo verificar la configuracion del token")
        return False


def check_downloads_dir():
    """Verifica que el directorio de descargas exista"""
    downloads_dir = Path('downloads')
    if downloads_dir.exists():
        print(f"[OK] Directorio de descargas existe: {downloads_dir.absolute()}")
        return True
    else:
        print("[!] Directorio de descargas no existe (se creara automaticamente)")
        return True  # No es crítico


def main():
    """Función principal de verificación"""
    print("=" * 60)
    print("VERIFICACION DE DEPENDENCIAS - Bot de Musica de Telegram")
    print("=" * 60)
    print()
    
    checks = []
    
    print("Verificando Python...")
    checks.append(check_python_version())
    print()
    
    print("Verificando modulos de Python...")
    checks.append(check_module('telegram', 'python-telegram-bot'))
    checks.append(check_module('yt_dlp', 'yt-dlp'))
    checks.append(check_module('requests', 'requests'))
    checks.append(check_module('dotenv', 'python-dotenv'))
    print()
    
    print("Verificando FFmpeg...")
    ffmpeg_ok = check_ffmpeg()
    checks.append(ffmpeg_ok)
    if not ffmpeg_ok:
        print("   [i] Instala FFmpeg:")
        print("      Windows: https://www.gyan.dev/ffmpeg/builds/")
        print("      macOS: brew install ffmpeg")
        print("      Linux: sudo apt install ffmpeg")
    print()
    
    print("Verificando configuracion del token...")
    token_ok = check_token_config()
    checks.append(token_ok)
    if not token_ok:
        print("   [i] Configura tu token:")
        print("      1. Abre Telegram y busca @BotFather")
        print("      2. Envia /newbot y sigue las instrucciones")
        print("      3. Copia el token")
        print("      4. Crea un archivo .env con: TELEGRAM_TOKEN=tu_token")
    print()
    
    print("Verificando directorios...")
    checks.append(check_downloads_dir())
    print()
    
    print("=" * 60)
    if all(checks):
        print("TODO LISTO! Puedes ejecutar el bot con: python main.py")
    else:
        failed = len([c for c in checks if not c])
        print(f"[!] {failed} verificacion(es) fallaron. Revisa los mensajes arriba.")
    print("=" * 60)


if __name__ == "__main__":
    main()
