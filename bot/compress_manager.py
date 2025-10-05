import os
import subprocess
import time
from datetime import timedelta

def run_ffmpeg(input_file: str, output_file: str, ffmpeg_code: str) -> bool:
    """
    Exécute ffmpeg avec un code personnalisé et renvoie True si succès.
    """
    try:
        command = f"ffmpeg -y -hide_banner -loglevel error -i \"{input_file}\" {ffmpeg_code} \"{output_file}\""
        print(f"\n[FFMPEG] ➤ Running command:\n{command}\n")

        start_time = time.time()
        result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        duration = timedelta(seconds=round(time.time() - start_time))

        if result.returncode != 0:
            print(f"[FFMPEG] ❌ Compression failed after {duration}. Error output:")
            print(result.stderr.decode("utf-8") or "No stderr captured.")
            return False

        # Vérifie la taille du fichier généré
        if not os.path.exists(output_file):
            print(f"[ERROR] Output file not found: {output_file}")
            return False

        size = os.path.getsize(output_file)
        if size < 100000:  # Moins de 100 Ko → erreur probable
            print(f"[ERROR] Output file too small ({size} bytes): {output_file}")
            return False

        print(f"[FFMPEG] ✅ Compression succeeded in {duration}. Size: {size/1024/1024:.2f} MB")
        return True

    except Exception as e:
        print(f"[EXCEPTION] ffmpeg crashed: {e}")
        return False


def compress_video(input_file: str, output_base: str) -> list:
    """
    Gère la compression et génère plusieurs résolutions automatiquement.
    Retourne la liste des fichiers générés.
    """

    # Liste des profils de résolution
    profiles = {
        "720p": "-preset medium -c:v libx264 -s 1280x720 -crf 25 -pix_fmt yuv420p -c:a aac -b:a 96k -threads 1",
        "480p": "-preset faster -c:v libx264 -s 854x480 -crf 28 -pix_fmt yuv420p -c:a aac -b:a 64k -threads 1",
        "360p": "-preset veryfast -c:v libx264 -s 640x360 -crf 30 -pix_fmt yuv420p -c:a aac -b:a 48k -threads 1"
    }

    results = []
    print(f"[START] Compressing: {input_file}")

    for label, ffmpeg_code in profiles.items():
        output_file = f"{output_base}_{label}.mp4"
        print(f"\n[PROCESS] Generating {label} version → {output_file}")

        ok = run_ffmpeg(input_file, output_file, ffmpeg_code)
        if ok:
            results.append(output_file)
        else:
            print(f"[WARN] Skipped {label} due to compression failure.")

    # Nettoyage et vérification finale
    print("\n[SUMMARY] Compression completed.")
    if not results:
        print("[FAIL] ❌ No valid output files were created.")
    else:
        for f in results:
            print(f" → ✅ {f} ({os.path.getsize(f)/1024/1024:.2f} MB)")

    return results
