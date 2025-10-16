import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import pygame
import pygame._sdl2.audio as sdl2_audio
import subprocess
from pathlib import Path
import os

class ReproductorVideo:
    def __init__(self):
        # Configurar la ventana principal
        self.root = tk.Tk()
        self.root.title("Reproductor de Video")
        self.root.geometry("800x600")

        # Inicializar pygame para audio
        pygame.init()
        pygame.mixer.init()

        # Variables de control
        self.cap = None
        self.playing = False
        self.video_path = None
        self.audio_path = None
        self.frame_delay = 30  # ms entre frames
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0

        self.crear_interfaz()

    def crear_interfaz(self):
        # Panel de controles superior
        panel_controles = ttk.Frame(self.root, padding=5)
        panel_controles.pack(fill=tk.X, padx=5, pady=5)

        # Botón para seleccionar video
        ttk.Button(panel_controles, text="Abrir Video", command=self.seleccionar_video).pack(side=tk.LEFT, padx=5)

        # Selector de dispositivo de audio
        ttk.Label(panel_controles, text="Salida de audio:").pack(side=tk.LEFT, padx=(10,0))
        self.dispositivos_audio = self.obtener_dispositivos_audio()
        self.dispositivo_var = tk.StringVar(value=self.dispositivos_audio[0] if self.dispositivos_audio else "")
        self.selector_audio = ttk.Combobox(
            panel_controles, 
            textvariable=self.dispositivo_var,
            values=self.dispositivos_audio,
            state="readonly",
            width=30
        )
        self.selector_audio.pack(side=tk.LEFT, padx=5)
        self.selector_audio.bind('<<ComboboxSelected>>', self.cambiar_dispositivo_audio)

        # Controles de reproducción
        self.btn_play = ttk.Button(panel_controles, text="Play", command=self.reproducir_pausar)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        # Control de volumen
        ttk.Label(panel_controles, text="Volumen:").pack(side=tk.LEFT, padx=(10,0))
        self.volumen = tk.DoubleVar(value=1.0)
        ttk.Scale(
            panel_controles,
            from_=0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.volumen,
            command=self.ajustar_volumen
        ).pack(side=tk.LEFT, padx=5)

        # Área de video
        self.area_video = ttk.Label(self.root)
        self.area_video.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        # Barra de progreso
        self.frame_progreso = ttk.Frame(self.root)
        self.frame_progreso.pack(fill=tk.X, padx=10, pady=5)

        # Etiqueta de tiempo
        self.etiqueta_tiempo = ttk.Label(self.frame_progreso, text="0:00 / 0:00")
        self.etiqueta_tiempo.pack(side=tk.LEFT, padx=5)

        # Barra de progreso
        self.progreso = tk.DoubleVar(value=0)
        self.barra_progreso = ttk.Scale(
            self.frame_progreso,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progreso
        )
        self.barra_progreso.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.barra_progreso.bind("<Button-1>", self.iniciar_busqueda)
        self.barra_progreso.bind("<ButtonRelease-1>", self.buscar_posicion)

        # Estado de búsqueda
        self.buscando = False
        self.estaba_reproduciendo = False

    def obtener_dispositivos_audio(self):
        """Obtiene la lista de dispositivos de audio disponibles"""
        dispositivos = ["Dispositivo predeterminado"]
        try:
            for i in range(sdl2_audio.get_num_audio_devices(False)):
                nombre = sdl2_audio.get_audio_device_name(i, False).decode('utf-8')
                if nombre not in dispositivos:
                    dispositivos.append(nombre)
            print(f"Dispositivos de audio encontrados: {dispositivos}")
        except Exception as e:
            print(f"Error al obtener dispositivos de audio: {e}")
        return dispositivos

    def cambiar_dispositivo_audio(self, event=None):
        """Cambia el dispositivo de salida de audio"""
        dispositivo = self.dispositivo_var.get()
        try:
            pygame.mixer.quit()
            if dispositivo == "Dispositivo predeterminado":
                pygame.mixer.init()
            else:
                pygame.mixer.init(devicename=dispositivo)
            print(f"Cambiado a dispositivo de audio: {dispositivo}")
            pygame.mixer.music.set_volume(self.volumen.get())
        except Exception as e:
            print(f"Error al cambiar dispositivo de audio: {e}")

    def ajustar_volumen(self, _=None):
        """Ajusta el volumen del audio"""
        try:
            pygame.mixer.music.set_volume(self.volumen.get())
        except:
            pass

    def seleccionar_video(self):
        """Abre el diálogo para seleccionar un archivo de video"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar Video",
            filetypes=[
                ("Archivos de video", "*.mp4 *.avi *.mkv *.mov"),
                ("Todos los archivos", "*.*")
            ]
        )
        if ruta:
            self.cargar_video(ruta)

    def cargar_video(self, ruta):
        """Carga el video seleccionado"""
        if self.cap is not None:
            self.cap.release()

        # Detener audio anterior si existe
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        self.cap = cv2.VideoCapture(ruta)
        if not self.cap.isOpened():
            print(f"Error: No se pudo abrir el video: {ruta}")
            return

        self.video_path = ruta
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.progreso.set(0)

        # Extraer audio del video
        try:
            video_path = Path(ruta)
            self.audio_path = video_path.with_suffix('.temp.wav')
            
            # Eliminar archivo temporal anterior si existe
            if os.path.exists(self.audio_path):
                os.remove(self.audio_path)
            
            # Extraer audio usando ffmpeg
            subprocess.run([
                'ffmpeg', '-y', 
                '-i', str(video_path),
                '-vn', '-acodec', 'pcm_s16le',
                str(self.audio_path)
            ], capture_output=True)
            
            print(f"Audio extraído a: {self.audio_path}")
        except Exception as e:
            print(f"Error al extraer audio: {e}")
            self.audio_path = None
        
        # Actualizar etiqueta de tiempo
        duracion = self.total_frames / self.fps if self.fps > 0 else 0
        self.etiqueta_tiempo.config(text=f"0:00 / {self.formatear_tiempo(duracion)}")
        
        # Iniciar reproducción
        self.reproducir_pausar()

    def formatear_tiempo(self, segundos):
        """Convierte segundos a formato MM:SS"""
        minutos = int(segundos // 60)
        segundos = int(segundos % 60)
        return f"{minutos}:{segundos:02d}"

    def reproducir_pausar(self):
        """Alterna entre reproducir y pausar el video"""
        if self.cap is None:
            return

        self.playing = not self.playing
        self.btn_play.config(text="Pause" if self.playing else "Play")

        if self.playing:
            # Iniciar/reanudar audio
            if self.audio_path:
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.unpause()
                    else:
                        # Calcular posición actual en segundos
                        current_pos = self.current_frame / self.fps if self.fps > 0 else 0
                        pygame.mixer.music.load(str(self.audio_path))
                        pygame.mixer.music.play(start=current_pos)
                        pygame.mixer.music.set_volume(self.volumen.get())
                except Exception as e:
                    print(f"Error al reproducir audio: {e}")
            
            self.actualizar_frame()
        else:
            # Pausar audio
            if self.audio_path and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        
    def iniciar_busqueda(self, event):
        """Prepara para buscar una posición en el video"""
        self.buscando = True
        self.estaba_reproduciendo = self.playing
        if self.playing:
            self.reproducir_pausar()

    def buscar_posicion(self, event):
        """Salta a la posición seleccionada en el video"""
        if self.cap is None:
            return

        # Calcular y establecer nueva posición
        frame_objetivo = int((self.progreso.get() / 100) * self.total_frames)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_objetivo)
        self.current_frame = frame_objetivo
        
        # Actualizar posición del audio
        if self.audio_path:
            try:
                current_pos = self.current_frame / self.fps if self.fps > 0 else 0
                pygame.mixer.music.load(str(self.audio_path))
                if self.estaba_reproduciendo:
                    pygame.mixer.music.play(start=current_pos)
                    pygame.mixer.music.set_volume(self.volumen.get())
            except Exception as e:
                print(f"Error al buscar en audio: {e}")

        # Mostrar el frame en la nueva posición
        ret, frame = self.cap.read()
        if ret:
            self.mostrar_frame(frame)

        # Actualizar tiempo
        tiempo_actual = self.current_frame / self.fps if self.fps > 0 else 0
        tiempo_total = self.total_frames / self.fps if self.fps > 0 else 0
        self.etiqueta_tiempo.config(
            text=f"{self.formatear_tiempo(tiempo_actual)} / {self.formatear_tiempo(tiempo_total)}"
        )

        # Restaurar reproducción si estaba reproduciéndose
        self.buscando = False
        if self.estaba_reproduciendo:
            self.reproducir_pausar()

    def mostrar_frame(self, frame):
        """Muestra un frame en el área de video"""
        # Convertir de BGR a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Obtener dimensiones del área de video
        area_ancho = self.area_video.winfo_width() or 780
        area_alto = self.area_video.winfo_height() or 520

        # Redimensionar manteniendo proporción
        alto, ancho = frame_rgb.shape[:2]
        escala = min(area_ancho/ancho, area_alto/alto)
        nuevo_ancho = int(ancho * escala)
        nuevo_alto = int(alto * escala)
        frame_rgb = cv2.resize(frame_rgb, (nuevo_ancho, nuevo_alto))

        # Convertir a formato Tkinter
        imagen = Image.fromarray(frame_rgb)
        imagen_tk = ImageTk.PhotoImage(image=imagen)
        self.area_video.config(image=imagen_tk)
        self.area_video.image = imagen_tk

    def actualizar_frame(self):
        """Actualiza el frame actual durante la reproducción"""
        if not self.playing or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            
            # Actualizar barra de progreso
            if not self.buscando:
                progress = (self.current_frame / self.total_frames * 100)
                self.progreso.set(progress)
            
            # Actualizar tiempo
            tiempo_actual = self.current_frame / self.fps if self.fps > 0 else 0
            tiempo_total = self.total_frames / self.fps if self.fps > 0 else 0
            self.etiqueta_tiempo.config(
                text=f"{self.formatear_tiempo(tiempo_actual)} / {self.formatear_tiempo(tiempo_total)}"
            )
            
            # Mostrar frame
            self.mostrar_frame(frame)
            
            # Programar siguiente frame
            self.root.after(self.frame_delay, self.actualizar_frame)
        else:
            # Fin del video
            self.playing = False
            self.btn_play.config(text="Play")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            self.progreso.set(0)

    def ejecutar(self):
        """Inicia la aplicación"""
        self.root.mainloop()

    def __del__(self):
        """Limpia recursos al cerrar"""
        if self.cap is not None:
            self.cap.release()
        pygame.mixer.quit()
        pygame.quit()
        
        # Eliminar archivo temporal de audio
        if self.audio_path and os.path.exists(self.audio_path):
            try:
                os.remove(self.audio_path)
            except:
                pass

if __name__ == "__main__":
    app = ReproductorVideo()
    app.ejecutar()