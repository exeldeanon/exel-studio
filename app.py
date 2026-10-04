import os
import random
import subprocess
import threading
import json
import math
import concurrent.futures
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Глобальные настройки темы
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ProSaaSStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Exel Studio — Ultimate AI Video Unique Engine v3.3")
        self.geometry("1100x950")
        self.resizable(False, False)

        self.input_folder = ""
        self.output_folder = ""
        self.watermark_path = ""
        self.config_file = "studio_config.json"
        self._is_loading_config = True

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_content()
        
        self.load_config_from_json(silent=True)
        self._is_loading_config = False

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#1a1a24", "#121218"))
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)

        logo_label = ctk.CTkLabel(sidebar, text="⚡ Exel Studio", font=ctk.CTkFont(size=18, weight="bold"), text_color="#a855f7")
        logo_label.grid(row=0, column=0, padx=20, pady=(25, 20), sticky="w")

        ctk.CTkButton(sidebar, text="📁 Основные папки", fg_color="transparent", hover_color="#2b2b3d", anchor="w", command=lambda: self.show_frame("main")).grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(sidebar, text="🎨 Визуальный уникализатор", fg_color="transparent", hover_color="#2b2b3d", anchor="w", command=lambda: self.show_frame("visual")).grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(sidebar, text="💧 Вотермарки и Плашки", fg_color="transparent", hover_color="#2b2b3d", anchor="w", command=lambda: self.show_frame("watermark")).grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(sidebar, text="🎵 Аудио и Эффекты", fg_color="transparent", hover_color="#2b2b3d", anchor="w", command=lambda: self.show_frame("audio")).grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(sidebar, text="⚙️ Система и GPU", fg_color="transparent", hover_color="#2b2b3d", anchor="w", command=lambda: self.show_frame("system")).grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        self.lbl_autosave = ctk.CTkLabel(sidebar, text="💾 Автосохранение: ВКЛ", font=ctk.CTkFont(size=11), text_color="#10b981")
        self.lbl_autosave.grid(row=7, column=0, padx=20, pady=20, sticky="sw")

    def create_main_content(self):
        self.content_frame = ctk.CTkFrame(self, fg_color=("#14141c", "#0d0d12"), corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MainFolderFrame, VisualUniqueFrame, WatermarkConfigFrame, AudioSystemFrame, SystemPerformanceFrame):
            frame = F(parent=self.content_frame, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainFolderFrame")

    def show_frame(self, page_key):
        mapping = {
            "main": "MainFolderFrame",
            "visual": "VisualUniqueFrame",
            "watermark": "WatermarkConfigFrame",
            "audio": "AudioSystemFrame",
            "system": "SystemPerformanceFrame"
        }
        self.frames[mapping.get(page_key, "MainFolderFrame")].tkraise()

    def trigger_autosave(self):
        if self._is_loading_config:
            return
        try:
            data = self.get_all_settings()
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка автосохранения: {e}")

    def get_all_settings(self):
        data = {}
        for frame in self.frames.values():
            if hasattr(frame, "get_settings"):
                data.update(frame.get_settings())
        data["input_folder"] = self.input_folder
        data["output_folder"] = self.output_folder
        data["watermark_path"] = self.watermark_path
        return data

    def set_all_settings(self, data):
        self.input_folder = data.get("input_folder", "")
        self.output_folder = data.get("output_folder", "")
        self.watermark_path = data.get("watermark_path", "")
        for frame in self.frames.values():
            if hasattr(frame, "set_settings"):
                frame.set_settings(data)

    def load_config_from_json(self, silent=False):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.set_all_settings(data)
            except Exception as e:
                if not silent:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить конфиг: {e}")


# --- ВКЛАДКА 1: ПАПКИ И ПРОГРЕСС ---
class MainFolderFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="📁 Управление проектом и директориями", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(25, 15))

        card = ctk.CTkFrame(self, fg_color=("#1a1a24", "#16161f"), corner_radius=12)
        card.pack(fill="x", padx=30, pady=10)

        self.btn_in = ctk.CTkButton(card, text="Выбрать исходную папку", command=self.select_in, width=200)
        self.btn_in.pack(anchor="w", padx=20, pady=15)
        self.lbl_in = ctk.CTkLabel(card, text="Путь не выбран", text_color="gray")
        self.lbl_in.pack(anchor="w", padx=20, pady=(0, 15))

        self.btn_out = ctk.CTkButton(card, text="Папка сохранения готовых", command=self.select_out, width=200, fg_color="#7c3aed", hover_color="#6d28d9")
        self.btn_out.pack(anchor="w", padx=20, pady=15)
        self.lbl_out = ctk.CTkLabel(card, text="Путь не выбран", text_color="gray")
        self.lbl_out.pack(anchor="w", padx=20, pady=(0, 15))

        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.pack(fill="x", padx=30, pady=(10, 0))
        self.lbl_progress_status = ctk.CTkLabel(prog_frame, text="Готов к работе", font=ctk.CTkFont(size=12))
        self.lbl_progress_status.pack(anchor="w", pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(prog_frame, orientation="horizontal", height=14)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0.0)

        ctk.CTkLabel(self, text="💻 Логирование процессов", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=30, pady=(15, 5))
        self.log_box = ctk.CTkTextbox(self, height=120, fg_color=("#101015", "#0a0a0f"), font=ctk.CTkFont(size=11))
        self.log_box.pack(fill="x", padx=30, pady=5)

        self.btn_start = ctk.CTkButton(self, text="⚡ ЗАПУСТИТЬ МУЛЬТИПОТОЧНЫЙ РЕНДЕРИНГ", fg_color="#10b981", hover_color="#059669", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_processing_thread)
        self.btn_start.pack(fill="x", padx=30, pady=15)

    def select_in(self):
        folder = filedialog.askdirectory()
        if folder:
            self.controller.input_folder = folder
            self.lbl_in.configure(text=folder, text_color="white")
            self.controller.trigger_autosave()

    def select_out(self):
        folder = filedialog.askdirectory()
        if folder:
            self.controller.output_folder = folder
            self.lbl_out.configure(text=folder, text_color="white")
            self.controller.trigger_autosave()

    def log(self, text):
        def _update():
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
        self.after(0, _update)

    def update_progress(self, val, text=""):
        def _upd():
            self.progress_bar.set(val)
            if text:
                self.lbl_progress_status.configure(text=text)
        self.after(0, _upd)

    def get_settings(self):
        return {}

    def set_settings(self, data):
        if data.get("input_folder"):
            self.controller.input_folder = data["input_folder"]
            self.lbl_in.configure(text=data["input_folder"], text_color="white")
        if data.get("output_folder"):
            self.controller.output_folder = data["output_folder"]
            self.lbl_out.configure(text=data["output_folder"], text_color="white")

    def start_processing_thread(self):
        if not self.controller.input_folder or not self.controller.output_folder:
            messagebox.showerror("Ошибка", "Выберите папки ввода и вывода!")
            return
        threading.Thread(target=self.run_rendering_pipeline, daemon=True).start()

    def run_rendering_pipeline(self):
        self.btn_start.configure(state="disabled", text="⏳ Выполняется многопоточный рендеринг...")
        self.log("🚀 Запуск конвейера уникализации (Формат 9:16 с размытым фоном)...")
        self.update_progress(0.0, "Анализ файлов...")

        settings = self.controller.get_all_settings()
        
        if not os.path.exists(self.controller.input_folder):
            self.log("❌ Исходная папка не существует!")
            self.btn_start.configure(state="normal", text="⚡ ЗАПУСТИТЬ МУЛЬТИПОТОЧНЫЙ РЕНДЕРИНГ")
            self.update_progress(0.0, "Ошибка")
            return

        videos = [f for f in os.listdir(self.controller.input_folder) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
        
        if not videos:
            self.log("❌ В исходной папке нет видеофайлов!")
            self.btn_start.configure(state="normal", text="⚡ ЗАПУСТИТЬ МУЛЬТИПОТОЧНЫЙ РЕНДЕРИНГ")
            self.update_progress(0.0, "Нет файлов")
            return

        try:
            copies = int(settings.get("copies", 3))
            max_workers = int(settings.get("threads", 4))
        except ValueError:
            copies = 3
            max_workers = 4

        tasks = []
        for video in videos:
            for c in range(1, copies + 1):
                tasks.append((video, c))

        total_tasks = len(tasks)
        completed_tasks = [0]

        def get_random_param(min_val, val_type=float, decimals=3):
            try:
                min_v = float(min_val[0])
                max_v = float(min_val[1])
            except:
                min_v, max_v = 1.0, 1.0
            if min_v > max_v:
                min_v, max_v = max_v, min_v
            if val_type == int:
                return random.randint(int(min_v), int(max_v))
            return round(random.uniform(min_v, max_v), decimals)

        def has_audio_stream(file_path):
            try:
                cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                return b'audio' in res.stdout
            except:
                return True

        def get_video_duration(file_path):
            try:
                cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                return float(res.stdout.strip())
            except:
                return 0.0

        def process_single_task(task):
            video, c = task
            in_path = os.path.join(self.controller.input_folder, video)
            name, ext = os.path.splitext(video)
            out_name = f"{name}_unq_{c}{ext}"
            out_path = os.path.join(self.controller.output_folder, out_name)

            speed = get_random_param((settings.get("s_min", 0.98), settings.get("s_max", 1.02)), float, 3)
            zoom = get_random_param((settings.get("zoom_min", 1.0), settings.get("zoom_max", 1.15)), float, 3)
            rock = get_random_param((settings.get("rock_min", 0.5), settings.get("rock_max", 2.0)), float, 2)
            fade_in = get_random_param((settings.get("fade_min", 0.2), settings.get("fade_max", 1.0)), float, 2)
            flip = settings.get("flip", True) and random.choice([True, False])
            selected_style = settings.get("style_choice", "🎲 Безопасный микс")

            video_dur = get_video_duration(in_path)
            trim_args = []
            atrim_args = []
            if settings.get("trim_enabled", True) and video_dur > 5.0:
                t_start = get_random_param((0.3, 0.7), float, 2)
                t_end = get_random_param((0.3, 0.7), float, 2)
                if video_dur - (t_start + t_end) > 2.0:
                    trim_args = [f"trim=start={t_start}:end={video_dur - t_end}", "setpts=PTS-STARTPTS"]
                    atrim_args = [f"atrim=start={t_start}:end={video_dur - t_end}", "asetpts=PTS-STARTPTS"]

            crop_args = []
            if settings.get("crop_enabled", False):
                crop_pct = get_random_param((0.97, 0.99), float, 3)
                crop_args = [f"crop=iw*{crop_pct}:ih*{crop_pct}"]

            # Цепочка фильтров переднего плана
            fg_parts = [f"scale=iw*{zoom}:ih*{zoom}"]
            if crop_args:
                fg_parts.append(crop_args[0])
            if flip:
                fg_parts.append("hflip")

            freq = round(random.uniform(0.4, 0.7), 2)
            fg_parts.append(f"rotate='sin(t*{freq})*{rock}*PI/180':c=black@0:ow=rotw({rock}*PI/180):oh=roth({rock}*PI/180)")
            
            if trim_args:
                fg_parts.append(trim_args[0])

            c_rand = round(random.uniform(1.03, 1.12), 3)
            b_rand = round(random.uniform(-0.015, 0.02), 3)
            s_rand = round(random.uniform(1.02, 1.14), 3)

            if "Dark Moody" in selected_style:
                style_filter = f"eq=contrast={c_rand}:brightness=-0.03:saturation={s_rand},vignette=PI/3"
            elif "TikTok Gloss" in selected_style:
                style_filter = f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},unsharp=3:3:0.7,vignette=PI/3.5"
            elif "Vintage Film" in selected_style:
                style_filter = f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},colorbalance=rs=0.06:gs=0.02:bs=-0.06"
            elif "Cinematic Teal & Orange" in selected_style:
                style_filter = f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},colorbalance=rs=0.08:bs=-0.08"
            elif "Warm Sunset" in selected_style:
                style_filter = f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},colorbalance=rs=0.1:gs=0.03:bs=-0.05"
            else:
                presets_pool = [
                    f"eq=contrast={c_rand}:brightness=-0.02:saturation={s_rand},vignette=PI/3.5",
                    f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},unsharp=3:3:0.5,vignette=PI/4",
                    f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand},colorbalance=rs=0.05:bs=-0.05",
                    f"eq=contrast={c_rand}:brightness={b_rand}:saturation={s_rand}"
                ]
                style_filter = random.choice(presets_pool)

            fg_parts.append(style_filter)

            if settings.get("pixelate", False):
                px_val = get_random_param((settings.get("px_min", 2), settings.get("px_max", 4)), int, 0)
                if px_val > 1:
                    fg_parts.append(f"scale=iw/{px_val}:ih/{px_val},scale=iw*{px_val}:ih*{px_val}:flags=neighbor")

            if settings.get("noise", True):
                noise_val = get_random_param((settings.get("noise_min", 3), settings.get("noise_max", 8)), int, 0)
                fg_parts.append(f"noise=alls={noise_val}:allf=t+u")
            
            rand_fps = random.choice([29.97, 30.0, 30.03, 59.94, 60.0])
            fg_parts.append(f"fps={rand_fps}")

            if fade_in > 0:
                fg_parts.append(f"fade=t=in:st=0:d={fade_in}")

            foreground_chain = ",".join(fg_parts)

            # Безопасный и полностью связанный filter_complex
            wm_path = self.controller.watermark_path
            use_wm = settings.get("wm_enabled", False) and wm_path and os.path.exists(wm_path)

            if use_wm:
                try:
                    wm_opacity = float(settings.get("wm_opacity", 0.15))
                    wm_scale = int(settings.get("wm_scale", 20))
                    wm_pos_mode = settings.get("wm_pos", "🎲 Случайная позиция")
                    
                    if "Левый верх" in wm_pos_mode:
                        pos_expr = "10:10"
                    elif "Правый верх" in wm_pos_mode:
                        pos_expr = "W-w-10:10"
                    elif "Левый низ" in wm_pos_mode:
                        pos_expr = "10:H-h-10"
                    elif "Правый низ" in wm_pos_mode:
                        pos_expr = "W-w-10:H-h-10"
                    elif "Центр" in wm_pos_mode:
                        pos_expr = "(W-w)/2:(H-h)/2"
                    else:
                        rx = random.randint(20, 150)
                        ry = random.randint(20, 200)
                        pos_expr = f"{rx}:{ry}"

                    complex_vf = (
                        f"[0:v]split=2[main][bg];"
                        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg_blurred];"
                        f"[main]{foreground_chain}[fg];"
                        f"[bg_blurred][fg]overlay=(W-w)/2:(H-h)/2:shortest=1[base_v];"
                        f"[1:v]scale=iw*{wm_scale}/100:-1,format=rgba,colorchannelmixer=aa={wm_opacity}[wm];"
                        f"[base_v][wm]overlay={pos_expr}[outv]"
                    )
                except:
                    use_wm = False

            if not use_wm:
                complex_vf = (
                    f"[0:v]split=2[main][bg];"
                    f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg_blurred];"
                    f"[main]{foreground_chain}[fg];"
                    f"[bg_blurred][fg]overlay=(W-w)/2:(H-h)/2:shortest=1[outv]"
                )

            has_audio = has_audio_stream(in_path)
            cmd = ['ffmpeg', '-y', '-i', in_path]
            if use_wm:
                cmd.extend(['-i', wm_path])

            # Аудиофильтры
            if has_audio:
                vol_val = get_random_param((settings.get("vol_min", 0.95), settings.get("vol_max", 1.05)), float, 2)
                af_parts = []
                if atrim_args:
                    af_parts.extend(atrim_args)
                af_parts.extend([f"atempo={speed}", f"asetrate=44100*{1.0/speed}"])
                if settings.get("audio_mut", True):
                    af_parts.append("treble=g=1.5,bass=g=1.0")
                af_parts.append(f"volume={vol_val}")
                if fade_in > 0:
                    af_parts.append(f"afade=t=in:st=0:d={fade_in}")
                
                af_string = ",".join(af_parts)

                if settings.get("audio_noise", True):
                    noise_vol = get_random_param((settings.get("noise_vol_min", 0.001), settings.get("noise_vol_max", 0.004)), float, 4)
                    complex_vf += f";[0:a]{af_string}[main_audio];anoisesrc=d=999:c=white:r=44100:a={noise_vol}[noise_audio];[main_audio][noise_audio]amix=inputs=2:duration=first:weights=1 0.05[outa]"
                    cmd.extend(['-filter_complex', complex_vf])
                    cmd.extend(['-map', '[outv]', '-map', '[outa]'])
                else:
                    cmd.extend(['-filter_complex', complex_vf])
                    cmd.extend(['-map', '[outv]'])
                    cmd.extend(['-af', af_string])
                    cmd.extend(['-map', '0:a'])
                
                cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            else:
                cmd.extend(['-filter_complex', complex_vf])
                cmd.extend(['-map', '[outv]'])
                cmd.extend(['-an'])

            # Аппаратное ускорение или процессор
            use_gpu = settings.get("use_gpu", False)
            if use_gpu:
                cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', '20'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '20'])

            cmd.extend(['-movflags', '+faststart'])

            if settings.get("meta_scrub", True):
                cmd.extend([
                    '-metadata', 'major_brand=isom',
                    '-metadata', 'minor_version=512',
                    '-metadata', 'compatible_brands=isomiso2avc1mp41',
                    '-metadata', 'encoder=iPhone 16 Pro Max AVC encoder'
                ])

            cmd.append(out_path)

            try:
                process = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if process.returncode != 0:
                    err_msg = process.stderr.decode('utf-8', errors='ignore')
                    return f"❌ Ошибка FFmpeg в {out_name}: {err_msg[-180:]}"

                completed_tasks[0] += 1
                progress_pct = completed_tasks[0] / total_tasks
                self.update_progress(progress_pct, f"Обработано: {completed_tasks[0]} из {total_tasks}")

                return f"✅ Готово: {out_name}"
            except Exception as e:
                return f"❌ Ошибка в {out_name}: {e}"

        self.log(f"⚡ Найдено файлов: {len(videos)}. Копий на файл: {copies}. Всего задач: {total_tasks}. Потоков: {max_workers}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_single_task, tasks))
            for res in results:
                self.log(res)

        self.log("🎉 Пакетная многопоточная обработка завершена!")
        self.btn_start.configure(state="normal", text="⚡ ЗАПУСТИТЬ МУЛЬТИПОТОЧНЫЙ РЕНДЕРИНГ")
        self.update_progress(1.0, "Готово!")


# --- ВКЛАДКА 2: ВИЗУАЛЬНЫЙ УНИКАЛИЗАТОР ---
class VisualUniqueFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="🎨 Настройки диапазонов геометрии, обрезки и фильтров", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(15, 6))

        card = ctk.CTkFrame(self, fg_color=("#1a1a24", "#16161f"), corner_radius=12)
        card.pack(fill="x", padx=30, pady=5)

        zoom_frame = ctk.CTkFrame(card, fg_color="transparent")
        zoom_frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(zoom_frame, text="Исходный зум видео (Диапазон Мин / Макс):").pack(side="left")
        self.zoom_max = ctk.CTkEntry(zoom_frame, width=55); self.zoom_max.insert(0, "1.15"); self.zoom_max.pack(side="right", padx=5)
        self.zoom_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.zoom_min = ctk.CTkEntry(zoom_frame, width=55); self.zoom_min.insert(0, "1.0"); self.zoom_min.pack(side="right", padx=5)
        self.zoom_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        style_frame = ctk.CTkFrame(card, fg_color="transparent")
        style_frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(style_frame, text="Визуальный пресет / Стилистика (с рандомизацией):").pack(side="left")
        
        self.style_combo = ctk.CTkComboBox(style_frame, values=[
            "🎲 Безопасный микс (рандом из мягких)",
            "🎬 Dark Moody (Кинематографичный контраст)",
            "✨ TikTok Gloss (Теплый сочный глянец)",
            "📼 Vintage Film (Пленочный теплый тон)",
            "🌆 Cinematic Teal & Orange (Голливуд)",
            "🌅 Warm Sunset (Мягкие закатные тона)"
        ], width=240, command=lambda _: self.controller.trigger_autosave())
        self.style_combo.set("🎲 Безопасный микс (рандом из мягких)")
        self.style_combo.pack(side="right", padx=5)

        r_frame = ctk.CTkFrame(card, fg_color="transparent")
        r_frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(r_frame, text="Диапазон угла наклона / покачивания (град. Мин / Макс):").pack(side="left")
        self.rock_max = ctk.CTkEntry(r_frame, width=55); self.rock_max.insert(0, "2.0"); self.rock_max.pack(side="right", padx=5)
        self.rock_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.rock_min = ctk.CTkEntry(r_frame, width=55); self.rock_min.insert(0, "0.5"); self.rock_min.pack(side="right", padx=5)
        self.rock_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        tc_frame = ctk.CTkFrame(card, fg_color="transparent")
        tc_frame.pack(fill="x", padx=20, pady=6)
        self.trim_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(tc_frame, text="Рандомный Trim (обрезка 0.3-0.7с в начале/конце)", variable=self.trim_var, command=self.controller.trigger_autosave).pack(side="left")
        
        self.crop_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(tc_frame, text="Случайный Crop (кадрирование 1-3%)", variable=self.crop_var, command=self.controller.trigger_autosave).pack(side="right", padx=5)

        n_frame = ctk.CTkFrame(card, fg_color="transparent")
        n_frame.pack(fill="x", padx=20, pady=6)
        self.noise_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(n_frame, text="Пленочный шум (Диапазон интенсивности Мин / Макс):", variable=self.noise_var, command=self.controller.trigger_autosave).pack(side="left")
        self.noise_max = ctk.CTkEntry(n_frame, width=50); self.noise_max.insert(0, "8"); self.noise_max.pack(side="right", padx=5)
        self.noise_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.noise_min = ctk.CTkEntry(n_frame, width=50); self.noise_min.insert(0, "3"); self.noise_min.pack(side="right", padx=5)
        self.noise_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        px_frame = ctk.CTkFrame(card, fg_color="transparent")
        px_frame.pack(fill="x", padx=20, pady=6)
        self.pixelate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(px_frame, text="Пиксели/Мозаика (Диапазон размера Мин / Макс):", variable=self.pixelate_var, command=self.controller.trigger_autosave).pack(side="left")
        self.px_max = ctk.CTkEntry(px_frame, width=50); self.px_max.insert(0, "4"); self.px_max.pack(side="right", padx=5)
        self.px_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.px_min = ctk.CTkEntry(px_frame, width=50); self.px_min.insert(0, "2"); self.px_min.pack(side="right", padx=5)
        self.px_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        self.flip_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Случайное зеркальное отражение (H-Flip)", variable=self.flip_var, command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=6)

        self.jitter_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Уникализация частоты кадров (FPS Jitter)", variable=self.jitter_var, command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=(6, 12))

    def get_settings(self):
        return {
            "zoom_min": self.zoom_min.get(), "zoom_max": self.zoom_max.get(),
            "style_choice": self.style_combo.get(),
            "rock_min": self.rock_min.get(), "rock_max": self.rock_max.get(),
            "trim_enabled": self.trim_var.get(),
            "crop_enabled": self.crop_var.get(),
            "noise": self.noise_var.get(),
            "noise_min": self.noise_min.get(), "noise_max": self.noise_max.get(),
            "pixelate": self.pixelate_var.get(),
            "px_min": self.px_min.get(), "px_max": self.px_max.get(),
            "flip": self.flip_var.get(),
            "jitter": self.jitter_var.get()
        }

    def set_settings(self, data):
        if "zoom_min" in data: self.zoom_min.delete(0, "end"); self.zoom_min.insert(0, data["zoom_min"])
        if "zoom_max" in data: self.zoom_max.delete(0, "end"); self.zoom_max.insert(0, data["zoom_max"])
        if "style_choice" in data: self.style_combo.set(data["style_choice"])
        if "rock_min" in data: self.rock_min.delete(0, "end"); self.rock_min.insert(0, data["rock_min"])
        if "rock_max" in data: self.rock_max.delete(0, "end"); self.rock_max.insert(0, data["rock_max"])
        if "trim_enabled" in data: self.trim_var.set(data["trim_enabled"])
        if "crop_enabled" in data: self.crop_var.set(data["crop_enabled"])
        if "noise" in data: self.noise_var.set(data["noise"])
        if "noise_min" in data: self.noise_min.delete(0, "end"); self.noise_min.insert(0, data["noise_min"])
        if "noise_max" in data: self.noise_max.delete(0, "end"); self.noise_max.insert(0, data["noise_max"])
        if "pixelate" in data: self.pixelate_var.set(data["pixelate"])
        if "px_min" in data: self.px_min.delete(0, "end"); self.px_min.insert(0, data["px_min"])
        if "px_max" in data: self.px_max.delete(0, "end"); self.px_max.insert(0, data["px_max"])
        if "flip" in data: self.flip_var.set(data["flip"])
        if "jitter" in data: self.jitter_var.set(data["jitter"])


# --- ВКЛАДКА 3: ВОТЕРМАРКИ И ОВЕРЛЕИ ---
class WatermarkConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="💧 Динамические вотермарки, плашки и оверлеи", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(20, 10))

        card = ctk.CTkFrame(self, fg_color=("#1a1a24", "#16161f"), corner_radius=12)
        card.pack(fill="x", padx=30, pady=5)

        self.wm_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Включить наложение водяного знака / плашки (.png/.jpg)", variable=self.wm_enabled_var, font=ctk.CTkFont(weight="bold"), text_color="#a855f7", command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=15)

        btn_wm_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_wm_frame.pack(fill="x", padx=20, pady=8)
        self.btn_select_wm = ctk.CTkButton(btn_wm_frame, text="Выбрать файл вотермарки", command=self.select_watermark_file, width=200)
        self.btn_select_wm.pack(side="left")
        self.lbl_wm_path = ctk.CTkLabel(btn_wm_frame, text="Файл не выбран", text_color="gray")
        self.lbl_wm_path.pack(side="left", padx=15)

        op_frame = ctk.CTkFrame(card, fg_color="transparent")
        op_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(op_frame, text="Прозрачность вотермарки (Альфа 0.05 - 0.5):").pack(side="left")
        self.wm_opacity_entry = ctk.CTkEntry(op_frame, width=70)
        self.wm_opacity_entry.insert(0, "0.15")
        self.wm_opacity_entry.pack(side="right", padx=5)
        self.wm_opacity_entry.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        sc_frame = ctk.CTkFrame(card, fg_color="transparent")
        sc_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(sc_frame, text="Размер плашки (% от ширины экрана видео):").pack(side="left")
        self.wm_scale_entry = ctk.CTkEntry(sc_frame, width=70)
        self.wm_scale_entry.insert(0, "20")
        self.wm_scale_entry.pack(side="right", padx=5)
        self.wm_scale_entry.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        pos_frame = ctk.CTkFrame(card, fg_color="transparent")
        pos_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(pos_frame, text="Позиция вотермарки на холсте:").pack(side="left")
        self.wm_pos_combo = ctk.CTkComboBox(pos_frame, values=[
            "🎲 Случайная позиция (для каждой копии)",
            "📍 Верхний левый угол",
            "📍 Верхний правый угол",
            "📍 Нижний левый угол",
            "📍 Нижний правый угол",
            "🎯 Центр экрана"
        ], width=260, command=lambda _: self.controller.trigger_autosave())
        self.wm_pos_combo.set("🎲 Случайная позиция (для каждой копии)")
        self.wm_pos_combo.pack(side="right", padx=5)

    def select_watermark_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.controller.watermark_path = file_path
            self.lbl_wm_path.configure(text=os.path.basename(file_path), text_color="white")
            self.controller.trigger_autosave()

    def get_settings(self):
        return {
            "wm_enabled": self.wm_enabled_var.get(),
            "wm_opacity": self.wm_opacity_entry.get(),
            "wm_scale": self.wm_scale_entry.get(),
            "wm_pos": self.wm_pos_combo.get()
        }

    def set_settings(self, data):
        if "wm_enabled" in data: self.wm_enabled_var.set(data["wm_enabled"])
        if "wm_opacity" in data: self.wm_opacity_entry.delete(0, "end"); self.wm_opacity_entry.insert(0, data["wm_opacity"])
        if "wm_scale" in data: self.wm_scale_entry.delete(0, "end"); self.wm_scale_entry.insert(0, data["wm_scale"])
        if "wm_pos" in data: self.wm_pos_combo.set(data["wm_pos"])
        if self.controller.watermark_path:
            self.lbl_wm_path.configure(text=os.path.basename(self.controller.watermark_path), text_color="white")


# --- ВКЛАДКА 4: АУДИО И МЕТАДАННЫЕ ---
class AudioSystemFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="🎵 Диапазоны звука, плавность и метаданные", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(20, 10))

        card = ctk.CTkFrame(self, fg_color=("#1a1a24", "#16161f"), corner_radius=12)
        card.pack(fill="x", padx=30, pady=5)

        s_frame = ctk.CTkFrame(card, fg_color="transparent")
        s_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(s_frame, text="Диапазон вариации скорости (Мин / Макс):").pack(side="left")
        self.s_max = ctk.CTkEntry(s_frame, width=55); self.s_max.insert(0, "1.02"); self.s_max.pack(side="right", padx=5)
        self.s_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.s_min = ctk.CTkEntry(s_frame, width=55); self.s_min.insert(0, "0.98"); self.s_min.pack(side="right", padx=5)
        self.s_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        v_frame = ctk.CTkFrame(card, fg_color="transparent")
        v_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(v_frame, text="Диапазон громкости звука (Мин / Макс):").pack(side="left")
        self.vol_max = ctk.CTkEntry(v_frame, width=55); self.vol_max.insert(0, "1.05"); self.vol_max.pack(side="right", padx=5)
        self.vol_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.vol_min = ctk.CTkEntry(v_frame, width=55); self.vol_min.insert(0, "0.95"); self.vol_min.pack(side="right", padx=5)
        self.vol_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        f_frame = ctk.CTkFrame(card, fg_color="transparent")
        f_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(f_frame, text="Плавное появление Fade-In (Диапазон сек Мин / Макс):").pack(side="left")
        self.fade_max = ctk.CTkEntry(f_frame, width=55); self.fade_max.insert(0, "1.0"); self.fade_max.pack(side="right", padx=5)
        self.fade_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.fade_min = ctk.CTkEntry(f_frame, width=55); self.fade_min.insert(0, "0.3"); self.fade_min.pack(side="right", padx=5)
        self.fade_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        self.audio_mut_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Мягкая аудиомутация (Комфортная эквализация без питч-шока)", variable=self.audio_mut_var, command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=8)

        an_frame = ctk.CTkFrame(card, fg_color="transparent")
        an_frame.pack(fill="x", padx=20, pady=6)
        self.audio_noise_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(an_frame, text="Фоновый аудиошум (Интервал Мин / Макс):", variable=self.audio_noise_var, command=self.controller.trigger_autosave).pack(side="left")
        self.noise_vol_max = ctk.CTkEntry(an_frame, width=65); self.noise_vol_max.insert(0, "0.004"); self.noise_vol_max.pack(side="right", padx=5)
        self.noise_vol_max.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())
        self.noise_vol_min = ctk.CTkEntry(an_frame, width=65); self.noise_vol_min.insert(0, "0.001"); self.noise_vol_min.pack(side="right", padx=5)
        self.noise_vol_min.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        self.meta_scrub_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Подмена EXIF и метаданных контейнера (Эмуляция iPhone)", variable=self.meta_scrub_var, command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=8)

        self.hash_pad_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Бинарный хэш-паддинг в конце файла (Безопасный режим)", variable=self.hash_pad_var, command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=(8, 10))

    def get_settings(self):
        return {
            "s_min": self.s_min.get(), "s_max": self.s_max.get(),
            "vol_min": self.vol_min.get(), "vol_max": self.vol_max.get(),
            "fade_min": self.fade_min.get(), "fade_max": self.fade_max.get(),
            "audio_mut": self.audio_mut_var.get(),
            "audio_noise": self.audio_noise_var.get(),
            "noise_vol_min": self.noise_vol_min.get(), "noise_vol_max": self.noise_vol_max.get(),
            "meta_scrub": self.meta_scrub_var.get(),
            "hash_pad": self.hash_pad_var.get()
        }

    def set_settings(self, data):
        if "s_min" in data: self.s_min.delete(0, "end"); self.s_min.insert(0, data["s_min"])
        if "s_max" in data: self.s_max.delete(0, "end"); self.s_max.insert(0, data["s_max"])
        if "vol_min" in data: self.vol_min.delete(0, "end"); self.vol_min.insert(0, data["vol_min"])
        if "vol_max" in data: self.vol_max.delete(0, "end"); self.vol_max.insert(0, data["vol_max"])
        if "fade_min" in data: self.fade_min.delete(0, "end"); self.fade_min.insert(0, data["fade_min"])
        if "fade_max" in data: self.fade_max.delete(0, "end"); self.fade_max.insert(0, data["fade_max"])
        if "audio_mut" in data: self.audio_mut_var.set(data["audio_mut"])
        if "audio_noise" in data: self.audio_noise_var.set(data["audio_noise"])
        if "noise_vol_min" in data: self.noise_vol_min.delete(0, "end"); self.noise_vol_min.insert(0, data["noise_vol_min"])
        if "noise_vol_max" in data: self.noise_vol_max.delete(0, "end"); self.noise_vol_max.insert(0, data["noise_vol_max"])
        if "meta_scrub" in data: self.meta_scrub_var.set(data["meta_scrub"])
        if "hash_pad" in data: self.hash_pad_var.set(data["hash_pad"])


# --- ВКЛАДКА 5: СИСТЕМА И GPU ---
class SystemPerformanceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="⚙️ Системные параметры, потоки и GPU", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(25, 15))

        card = ctk.CTkFrame(self, fg_color=("#1a1a24", "#16161f"), corner_radius=12)
        card.pack(fill="x", padx=30, pady=10)

        self.gpu_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="⚡ Использовать аппаратное ускорение GPU (NVIDIA NVENC)", variable=self.gpu_var, font=ctk.CTkFont(weight="bold"), text_color="#10b981", command=self.controller.trigger_autosave).pack(anchor="w", padx=20, pady=15)

        t_frame = ctk.CTkFrame(card, fg_color="transparent")
        t_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(t_frame, text="Количество потоков рендеринга (CPU Cores):").pack(side="left")
        self.threads_entry = ctk.CTkEntry(t_frame, width=60); self.threads_entry.insert(0, "4"); self.threads_entry.pack(side="right", padx=5)
        self.threads_entry.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

        c_frame = ctk.CTkFrame(card, fg_color="transparent")
        c_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(c_frame, text="Количество вариаций (копий) на 1 файл:").pack(side="left")
        self.copies_entry = ctk.CTkEntry(c_frame, width=60); self.copies_entry.insert(0, "3"); self.copies_entry.pack(side="right", padx=5)
        self.copies_entry.bind("<KeyRelease>", lambda e: self.controller.trigger_autosave())

    def get_settings(self):
        return {
            "use_gpu": self.gpu_var.get(),
            "threads": self.threads_entry.get(),
            "copies": self.copies_entry.get()
        }

    def set_settings(self, data):
        if "use_gpu" in data: self.gpu_var.set(data["use_gpu"])
        if "threads" in data: self.threads_entry.delete(0, "end"); self.threads_entry.insert(0, data["threads"])
        if "copies" in data: self.copies_entry.delete(0, "end"); self.copies_entry.insert(0, data["copies"])


if __name__ == "__main__":
    app = ProSaaSStudio()
    app.mainloop()