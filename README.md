# Reproductor Cortador de Video

Un reproductor de video simple pero potente con capacidades de reproducción y control de audio, desarrollado en Python.

## Características

- 🎥 Reproducción de video con OpenCV
- 🔊 Reproducción de audio sincronizada
- 🎯 Control de progreso con barra deslizable
- ⏯️ Controles de reproducción (play/pause)
- 🔈 Selector de dispositivo de salida de audio
- 🎚️ Control de volumen
- 📁 Selector de archivos integrado

## Requisitos

- Python 3.x
- OpenCV (`opencv-python`)
- Pygame
- Pillow
- FFmpeg (debe estar instalado en el sistema)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/TU_USUARIO/reproductor-cortador.git
```

2. Instala las dependencias:
```bash
pip install opencv-python pygame pillow
```

3. Asegúrate de tener FFmpeg instalado en tu sistema:
- Windows: `winget install Gyan.FFmpeg`
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

## Uso

1. Ejecuta el programa:
```bash
python reproductor_video.py
```

2. Usa la interfaz para:
- Abrir videos usando el botón "Abrir Video"
- Reproducir/pausar con el botón Play/Pause
- Ajustar el progreso con la barra deslizable
- Controlar el volumen
- Seleccionar el dispositivo de salida de audio

## Formatos Soportados

- MP4
- AVI
- MKV
- MOV

## Contribuir

Si quieres contribuir al proyecto:

1. Haz un Fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.