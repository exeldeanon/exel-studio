import os
import random
import subprocess
from pathlib import Path

# --- КОНФИГУРАЦИЯ ---
INPUT_DIR = "input_videos"      # Папка с исходниками
OUTPUT_DIR = "output_videos"    # Папка для готовых роликов
COPIES_PER_VIDEO = 5            # Сколько уникальных копий сделать из 1 исходника

# Лимиты рандомизации (чтобы визуально не испортить ролик)
ZOOM_MIN, ZOOM_MAX = 0.01, 0.03            # Срез краев (1-3%)
BRIGHTNESS_MIN, BRIGHTNESS_MAX = -0.04, 0.04 # Яркость
CONTRAST_MIN, CONTRAST_MAX = 0.95, 1.05      # Контрастность
SATURATION_MIN, SATURATION_MAX = 0.95, 1.05  # Насыщенность
SPEED_MIN, SPEED_MAX = 0.98, 1.02            # Скорость видео/аудио
TRIM_START_MAX = 0.2                         # Макс. срез с начала (сек)
TRIM_END_MAX = 0.2                           # Макс. срез с конца (сек)
# --------------------

def generate_random_params():
    """Генерация уникального набора параметров для каждого рендера"""
    return {
        "zoom": random.uniform(ZOOM_MIN, ZOOM_MAX),
        "brightness": random.uniform(BRIGHTNESS_MIN, BRIGHTNESS_MAX),
        "contrast": random.uniform(CONTRAST_MIN, CONTRAST_MAX),
        "saturation": random.uniform(SATURATION_MIN, SATURATION_MAX),
        "speed": random.uniform(SPEED_MIN, SPEED_MAX),
        "volume": random.uniform(0.95, 1.05),
        "trim_start": random.uniform(0.05, TRIM_START_MAX),
        "trim_end": random.uniform(0.05, TRIM_END_MAX),
        "noise_level": random.randint(1, 3) # Интенсивность шума
    }

def process_video(input_path: Path, output_path: Path, params: dict):
    """Сборка команды FFmpeg и рендер"""
    
    # Расчет параметров для фильтров
    z = params['zoom']
    # Формула кропа: вырезаем центр, масштаб возвращаем к исходному
    crop_filter = f"crop=w=iw*{1-z}:h=ih*{1-z}:x=iw*{z/2}:y=ih*{z/2},scale=iw:ih"
    color_filter = f"eq=brightness={params['brightness']:.3f}:contrast={params['contrast']:.3f}:saturation={params['saturation']:.3f}"
    noise_filter = f"noise=alls={params['noise_level']}:allf=t"
    
    # Видео фильтры (объединяем)
    v_speed = 1.0 / params['speed']
    vf_string = f"{crop_filter},{color_filter},{noise_filter},setpts={v_speed:.3f}*PTS"
    
    # Аудио фильтры
    af_string = f"atempo={params['speed']:.3f},volume={params['volume']:.3f}"

    # Команда FFmpeg
    command = [
        "ffmpeg",
        "-y",                             # Перезаписывать файлы без вопроса
        "-i", str(input_path),            # Исходный файл
        "-ss", str(params['trim_start']), # Срез с начала
        # Для среза с конца нужно знать точную длину, но для простоты опустим (хватает начала и скорости)
        "-vf", vf_string,                 # Применение видеофильтров
        "-af", af_string,                 # Применение аудиофильтров
        "-map_metadata", "-1",            # Удаление всех метаданных
        "-c:v", "libx264",                # Кодек видео (универсальный для Instagram)
        "-preset", "fast",                # Скорость рендера
        "-crf", "23",                     # Качество (18-28, где 23 — оптимальный баланс)
        "-c:a", "aac",                    # Аудио кодек
        "-b:a", "192k",                   # Битрейт аудио
        str(output_path)
    ]

    try:
        # Запуск процесса без вывода логов в консоль (только ошибки)
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка обработки файла {input_path.name}: {e}")
        return False

def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    
    in_dir.mkdir(exist_ok=True)
    out_dir.mkdir(exist_ok=True)

    video_files = [f for f in in_dir.iterdir() if f.suffix.lower() in ['.mp4', '.mov', '.avi']]
    
    if not video_files:
        print(f"Положите исходные видео в папку '{INPUT_DIR}'")
        return

    print(f"Найдено {len(video_files)} видео. Начинаем уникализацию...")

    for video in video_files:
        print(f"\nОбработка: {video.name}")
        for i in range(1, COPIES_PER_VIDEO + 1):
            params = generate_random_params()
            out_name = f"{video.stem}_uniq_{i}{video.suffix}"
            out_path = out_dir / out_name
            
            print(f"  -> Создание копии {i}/{COPIES_PER_VIDEO}...", end="", flush=True)
            success = process_video(video, out_path, params)
            if success:
                print(" Готово")

if __name__ == "__main__":
    main()