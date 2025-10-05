import os
import subprocess

CURRENT_MODE = "auto"
MULTI_RES_ENABLED = False

def set_mode(mode):
    global CURRENT_MODE
    if mode in ["auto", "hq", "eco"]:
        CURRENT_MODE = mode
        return f"✅ Mode de compression défini sur : {mode.upper()}"
    return "❌ Mode invalide. Utilisez /setmode auto | hq | eco"

def toggle_multires(state: bool):
    global MULTI_RES_ENABLED
    MULTI_RES_ENABLED = state
    return f"✅ Multi-résolution {'activée' if state else 'désactivée'}"

def select_ffmpeg_command(input_file, output_file):
    """Retourne la commande ffmpeg selon la taille du fichier ou le mode choisi."""
    file_size = os.path.getsize(input_file)

    if CURRENT_MODE == "auto":
        if file_size < 150 * 1024 * 1024:
            cmd = f"-preset medium -c:v libx264 -s 1280x720 -crf 24 -pix_fmt yuv420p -c:a aac -b:a 96k"
        elif file_size < 400 * 1024 * 1024:
            cmd = f"-preset fast -c:v libx264 -s 854x480 -crf 26 -pix_fmt yuv420p -c:a aac -b:a 64k"
        else:
            cmd = f"-preset ultrafast -c:v libx264 -s 640x360 -crf 30 -pix_fmt yuv420p -c:a aac -b:a 48k"

    elif CURRENT_MODE == "hq":
        cmd = f"-preset medium -c:v libx264 -s 1280x720 -crf 22 -pix_fmt yuv420p -c:a aac -b:a 96k"

    elif CURRENT_MODE == "eco":
        cmd = f"-preset veryfast -c:v libx264 -s 640x360 -crf 30 -pix_fmt yuv420p -c:a aac -b:a 48k"

    return f'ffmpeg -i "{input_file}" {cmd} "{output_file}" -y'

def compress_video(input_path, output_base):
    """Effectue la compression principale (et multi-résolution si activée)."""
    results = []

    if MULTI_RES_ENABLED:
        resolutions = [("720p", "1280x720"), ("480p", "854x480"), ("360p", "640x360")]
        for label, size in resolutions:
            output_file = f"{output_base}_{label}.mp4"
            cmd = f'ffmpeg -i "{input_path}" -preset fast -c:v libx264 -s {size} -crf 26 -pix_fmt yuv420p -c:a aac -b:a 64k "{output_file}" -y'
            run_ffmpeg(cmd)
            results.append(output_file)
    else:
        output_file = f"{output_base}_compressed.mp4"
        cmd = select_ffmpeg_command(input_path, output_file)
        run_ffmpeg(cmd)
        results.append(output_file)

    return results

def run_ffmpeg(cmd):
    print(f"⚙️  Exécution : {cmd}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b''):
        print(line.decode(errors='ignore').strip())
    process.wait()
