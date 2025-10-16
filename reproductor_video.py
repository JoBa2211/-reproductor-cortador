import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import pygame
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

        # Panel izquierdo para controles de archivo
        panel_archivo = ttk.Frame(panel_controles)
        panel_archivo.pack(side=tk.LEFT, padx=5)

        # Botón para seleccionar video
        ttk.Button(panel_archivo, text="Abrir Video", command=self.seleccionar_video).pack(side=tk.LEFT, padx=5)
        
        # Botón para recortar video
        self.btn_recortar = ttk.Button(panel_archivo, text="Recortar", command=self.recortar_video, state="disabled")
        self.btn_recortar.pack(side=tk.LEFT, padx=5)

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
        return ["Dispositivo predeterminado"]

    def cambiar_dispositivo_audio(self, event=None):
        """Cambia el dispositivo de salida de audio"""
        try:
            pygame.mixer.quit()
            pygame.mixer.init()
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
            
        # Habilitar botón de recortar
        self.btn_recortar.config(state="normal")

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

    def recortar_video(self):
        """Abre la ventana para recortar el video en clips"""
        if not self.cap:
            return

        duracion_total = self.total_frames / self.fps if self.fps > 0 else 0
        clips = self.calcular_clips(duracion_total)
        
        # Crear ventana para mostrar clips
        ventana_clips = tk.Toplevel(self.root)
        ventana_clips.title("Clips de Video")
        ventana_clips.geometry("800x600")
        
        # Frame principal
        frame_principal = ttk.Frame(ventana_clips, padding=10)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Lista de clips (panel izquierdo)
        frame_lista = ttk.Frame(frame_principal)
        frame_lista.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(frame_lista, text="Clips Disponibles").pack()
        
        # Lista con selección múltiple
        lista_clips = tk.Listbox(frame_lista, width=40, height=20, selectmode=tk.EXTENDED)
        lista_clips.pack(fill=tk.Y, pady=5)
        
        # Barra de desplazamiento para la lista
        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=lista_clips.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lista_clips.config(yscrollcommand=scrollbar.set)
        
        # Frame para botones de exportación
        frame_botones_exp = ttk.Frame(frame_lista)
        frame_botones_exp.pack(fill=tk.X, pady=5)
        
        def exportar_seleccionados():
            # Detener reproducción actual
            self.clip_playing = False
            if self.clip_cap:
                self.clip_cap.release()
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.btn_play_clip.config(text="Play")
            
            seleccionados = lista_clips.curselection()
            if not seleccionados:
                messagebox.showwarning("Aviso", "Selecciona al menos un clip para exportar")
                return
                
            directorio = filedialog.askdirectory(title="Seleccionar carpeta para guardar clips")
            if not directorio:
                return
                
            progreso = ttk.Progressbar(frame_lista, mode='determinate', length=200)
            progreso.pack(pady=5)
            
            total_clips = len(seleccionados)
            for idx, i in enumerate(seleccionados):
                progreso['value'] = (idx / total_clips) * 100
                ventana_clips.update()
                
                inicio, duracion = clips[i]
                nombre_archivo = f"clip_{i+1}.mp4"
                ruta_salida = os.path.join(directorio, nombre_archivo)
                
                try:
                    # Primero extraemos el segmento recodificando para asegurar frames clave
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', self.video_path,
                        '-ss', str(inicio),
                        '-t', str(duracion),
                        '-c:v', 'libx264',     # Usar codec H.264
                        '-preset', 'fast',      # Usar preset rápido para balance velocidad/calidad
                        '-crf', '18',           # Alta calidad (0-51, menor es mejor)
                        '-c:a', 'aac',          # Codec de audio AAC
                        '-b:a', '192k',         # Bitrate de audio
                        '-movflags', '+faststart',  # Optimizar para reproducción web
                        ruta_salida
                    ], capture_output=True, check=True)
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Error al procesar clip {i+1}: {e}")
            
            progreso.destroy()
            messagebox.showinfo("Éxito", f"Se exportaron {total_clips} clips correctamente")
        
        # Área de reproducción (panel derecho)
        frame_reprod = ttk.Frame(frame_principal)
        frame_reprod.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Variables para el reproductor de clips
        self.clip_actual = None
        self.clip_cap = None
        self.clip_playing = False
        self.clip_current_frame = 0
        
        # Marco negro para el área de video
        marco_video = ttk.Frame(frame_reprod, style="Black.TFrame")
        marco_video.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Estilo para marco negro
        style = ttk.Style()
        style.configure("Black.TFrame", background="black")
        
        # Área de video para clips
        area_video_clip = ttk.Label(marco_video)
        area_video_clip.pack(expand=True, fill=tk.BOTH)
        
        # Hacer que el área de video se adapte al redimensionar
        def on_resize(event):
            if hasattr(self, 'clip_current_frame'):
                # Forzar actualización del frame si hay un video reproduciéndose
                self.clip_playing = True
                
        area_video_clip.bind('<Configure>', on_resize)
        
        # Panel de controles para clips
        panel_controles_clip = ttk.Frame(frame_reprod)
        panel_controles_clip.pack(fill=tk.X, pady=5)
        
        # Variables de control para clips
        self.btn_play_clip = ttk.Button(panel_controles_clip, text="Play", 
            command=lambda: self.toggle_clip(clips[lista_clips.curselection()[0]], area_video_clip))
        self.btn_play_clip.pack(side=tk.LEFT, padx=5)
        
        # Manejar cierre de ventana
        def on_closing():
            self.clip_playing = False
            if self.clip_cap:
                self.clip_cap.release()
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            ventana_clips.destroy()
            
        ventana_clips.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Barra de progreso para clips
        barra_progreso_clip = ttk.Scale(panel_controles_clip, from_=0, to=100, orient=tk.HORIZONTAL)
        barra_progreso_clip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Insertar clips en la lista
        for i, (inicio, duracion) in enumerate(clips):
            lista_clips.insert(tk.END, f"Clip {i+1} ({self.formatear_tiempo(duracion)})")

        # Botones de exportación
        ttk.Button(frame_botones_exp, text="Exportar Seleccionados", 
                  command=exportar_seleccionados).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botones_exp, text="Exportar Todos", 
                  command=lambda: lista_clips.selection_set(0, tk.END) or exportar_seleccionados()).pack(side=tk.LEFT, padx=5)
        
        # Botón para seleccionar/deseleccionar todos
        def toggle_seleccion():
            if lista_clips.curselection():
                lista_clips.selection_clear(0, tk.END)
            else:
                lista_clips.selection_set(0, tk.END)
        
        ttk.Button(frame_botones_exp, text="Seleccionar/Deseleccionar Todo", 
                  command=toggle_seleccion).pack(side=tk.LEFT, padx=5)
        
        # Centrar ventana
        ventana_clips.transient(self.root)
        ventana_clips.grab_set()

    def calcular_clips(self, duracion_total):
        """Calcula la distribución óptima de clips"""
        DURACION_CLIP = 50  # segundos
        MIN_DURACION_ULTIMO = 30  # segundos
        
        # Calcular número inicial de clips completos
        num_clips = int(duracion_total / DURACION_CLIP)
        duracion_restante = duracion_total % DURACION_CLIP
        
        clips = []
        
        # Si el último fragmento es muy corto, redistribuir
        if 0 < duracion_restante < MIN_DURACION_ULTIMO:
            # Calcular nueva duración para distribuir el remanente
            if num_clips > 0:
                nueva_duracion = (duracion_total) / num_clips
                for i in range(num_clips):
                    clips.append((i * nueva_duracion, nueva_duracion))
            else:
                # Si el video es más corto que MIN_DURACION_ULTIMO
                clips.append((0, duracion_total))
        else:
            # Crear clips normales
            for i in range(num_clips):
                clips.append((i * DURACION_CLIP, DURACION_CLIP))
            
            # Agregar último clip si hay suficiente duración
            if duracion_restante >= MIN_DURACION_ULTIMO:
                clips.append((num_clips * DURACION_CLIP, duracion_restante))
        
        return clips

    def toggle_clip(self, info_clip, area_video):
        """Alterna entre reproducir y pausar un clip"""
        if not hasattr(self, 'clip_info') or self.clip_info != info_clip:
            # Es un clip nuevo
            self.clip_info = info_clip
            self.iniciar_nuevo_clip(info_clip, area_video)
        else:
            # Es el mismo clip, alternar play/pause
            self.clip_playing = not self.clip_playing
            self.btn_play_clip.config(text="Pause" if self.clip_playing else "Play")
            
            if self.clip_playing:
                # Si no hay audio reproduciéndose, reiniciar desde la posición actual
                if not pygame.mixer.music.get_busy():
                    inicio, _ = self.clip_info
                    pos_actual = (self.clip_current_frame / self.fps) if self.fps > 0 else 0
                    try:
                        pygame.mixer.music.load(str(self.audio_path))
                        pygame.mixer.music.play(start=inicio + pos_actual)
                        pygame.mixer.music.set_volume(self.volumen.get())
                    except Exception as e:
                        print(f"Error al reanudar audio: {e}")
                else:
                    pygame.mixer.music.unpause()
                self.actualizar_frame_clip(area_video)
            else:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()

    def iniciar_nuevo_clip(self, info_clip, area_video):
        """Inicia la reproducción de un nuevo clip"""
        inicio, duracion = info_clip
        
        if self.clip_cap is not None:
            self.clip_cap.release()
            
        # Detener audio anterior si existe
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        self.clip_cap = cv2.VideoCapture(self.video_path)
        if not self.clip_cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir el clip")
            return
        
        # Posicionar en el inicio del clip
        self.clip_cap.set(cv2.CAP_PROP_POS_FRAMES, int(inicio * self.fps))
        self.clip_current_frame = 0
        self.clip_playing = True
        self.btn_play_clip.config(text="Pause")
        
        # Iniciar audio desde la posición correcta
        if self.audio_path:
            try:
                pygame.mixer.music.load(str(self.audio_path))
                pygame.mixer.music.play(start=inicio)
                pygame.mixer.music.set_volume(self.volumen.get())
            except Exception as e:
                print(f"Error al reproducir audio del clip: {e}")
        
        def actualizar_frame_clip():
            if not self.clip_playing:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                return
                
            ret, frame = self.clip_cap.read()
            if ret:
                self.clip_current_frame += 1
                if self.clip_current_frame > duracion * self.fps:
                    self.clip_playing = False
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    return
                    
                # Mostrar frame adaptado al tamaño del área
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Obtener dimensiones del área de video
                area_ancho = area_video.winfo_width()
                area_alto = area_video.winfo_height()
                
                if area_ancho > 1 and area_alto > 1:  # Asegurarse de que el área está visible
                    # Calcular proporción
                    alto, ancho = frame_rgb.shape[:2]
                    proporcion_video = ancho / alto
                    proporcion_area = area_ancho / area_alto
                    
                    if proporcion_video > proporcion_area:
                        # El video es más ancho que el área
                        nuevo_ancho = area_ancho
                        nuevo_alto = int(area_ancho / proporcion_video)
                    else:
                        # El video es más alto que el área
                        nuevo_alto = area_alto
                        nuevo_ancho = int(area_alto * proporcion_video)
                    
                    frame_rgb = cv2.resize(frame_rgb, (nuevo_ancho, nuevo_alto))
                
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)
                area_video.config(image=img_tk)
                area_video.image = img_tk
                
                if self.clip_playing:
                    area_video.after(self.frame_delay, actualizar_frame_clip)
            else:
                self.clip_playing = False
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
        
        actualizar_frame_clip()
        
        # Frame para los controles

    def actualizar_frame_clip(self, area_video):
        """Actualiza el frame actual del clip durante la reproducción"""
        if not self.clip_playing:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            return
            
        ret, frame = self.clip_cap.read()
        if ret:
            self.clip_current_frame += 1
            if self.clip_current_frame > self.clip_info[1] * self.fps:
                self.clip_playing = False
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                self.btn_play_clip.config(text="Play")
                return
                
            # Mostrar frame adaptado al tamaño del área
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Obtener dimensiones del área de video
            area_ancho = area_video.winfo_width()
            area_alto = area_video.winfo_height()
            
            if area_ancho > 1 and area_alto > 1:  # Asegurarse de que el área está visible
                # Calcular proporción
                alto, ancho = frame_rgb.shape[:2]
                proporcion_video = ancho / alto
                proporcion_area = area_ancho / area_alto
                
                if proporcion_video > proporcion_area:
                    # El video es más ancho que el área
                    nuevo_ancho = area_ancho
                    nuevo_alto = int(area_ancho / proporcion_video)
                else:
                    # El video es más alto que el área
                    nuevo_alto = area_alto
                    nuevo_ancho = int(area_alto * proporcion_video)
                
                frame_rgb = cv2.resize(frame_rgb, (nuevo_ancho, nuevo_alto))
            
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            area_video.config(image=img_tk)
            area_video.image = img_tk
            
            if self.clip_playing:
                area_video.after(self.frame_delay, lambda: self.actualizar_frame_clip(area_video))
        else:
            self.clip_playing = False
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.btn_play_clip.config(text="Play")

    def parsear_tiempo(self, tiempo_str):
        """Convierte un string MM:SS a segundos"""
        try:
            minutos, segundos = map(int, tiempo_str.split(':'))
            return minutos * 60 + segundos
        except:
            raise ValueError("Formato de tiempo inválido. Use MM:SS")
            
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