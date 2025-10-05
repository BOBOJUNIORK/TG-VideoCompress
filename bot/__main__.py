import os, json, asyncio, itertools
from datetime import datetime as dt
from telethon import events
from . import *
from .config import *
from .worker import *
from .devtools import *
from .FastTelethon import *
from .compress_manager import compress_video

# === Configuration runtime dynamique ===
RUNTIME_FILE = "config/runtime.json"

DEFAULT_RUNTIME = {
    "mode": "auto",       # auto / hq / eco
    "multires": False     # True / False
}

def load_runtime():
    if not os.path.exists(RUNTIME_FILE):
        os.makedirs("config", exist_ok=True)
        with open(RUNTIME_FILE, "w") as f:
            json.dump(DEFAULT_RUNTIME, f, indent=2)
    with open(RUNTIME_FILE, "r") as f:
        return json.load(f)

def save_runtime(cfg):
    with open(RUNTIME_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

RUNTIME = load_runtime()

# === LOGGING amélioré ===
import logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%d-%b-%y %H:%M:%S"
)
LOGS = logging.getLogger("bot")

LOGS.info("Starting bot...")

try:
    bot.start(bot_token=BOT_TOKEN)
except Exception as er:
    LOGS.error(er)


########## COMMANDES DE BASE ##########

@bot.on(events.NewMessage(pattern="/start"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return await e.reply("**❌ Vous n’êtes pas autorisé à utiliser ce bot.**")
    await start(e)

@bot.on(events.NewMessage(pattern="/help"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return await e.reply("**❌ Vous n’êtes pas autorisé à utiliser ce bot.**")
    help_msg = (
        "🎥 **Commandes disponibles :**\n\n"
        "/getcode — voir la commande ffmpeg actuelle\n"
        "/setcode <commande> — définir un nouveau preset ffmpeg\n"
        "/setmode [auto|hq|eco] — changer le mode de compression\n"
        "/multires [on|off] — activer/désactiver la multi-résolution\n"
        "/showthumb — voir la miniature actuelle\n"
        "/ping — test du bot\n"
        "/clear — vider la file d’attente\n"
        "\n⚙️ **Mode actuel :** `{}`\n📺 **Multi-résolutions :** `{}`".format(
            RUNTIME["mode"], "activé" if RUNTIME["multires"] else "désactivé"
        )
    )
    await e.reply(help_msg)

@bot.on(events.NewMessage(pattern="/setmode"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return await e.reply("**❌ Non autorisé.**")
    try:
        mode = e.text.split(" ", 1)[1].strip().lower()
        if mode not in ["auto", "hq", "eco"]:
            return await e.reply("⚠️ Modes disponibles : `auto`, `hq`, `eco`")
        RUNTIME["mode"] = mode
        save_runtime(RUNTIME)
        await e.reply(f"✅ Mode changé en `{mode}` avec succès.")
    except:
        await e.reply("⚠️ Usage : `/setmode auto|hq|eco`")

@bot.on(events.NewMessage(pattern="/multires"))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return await e.reply("**❌ Non autorisé.**")
    try:
        state = e.text.split(" ", 1)[1].strip().lower()
        if state not in ["on", "off"]:
            return await e.reply("⚙️ Usage : `/multires on|off`")
        RUNTIME["multires"] = state == "on"
        save_runtime(RUNTIME)
        await e.reply(f"✅ Multi-résolutions {'activées' if state == 'on' else 'désactivées'}.")
    except:
        await e.reply("⚙️ Usage : `/multires on|off`")


########### MINIATURES ###########

@bot.on(events.NewMessage(incoming=True))
async def _(e):
    if str(e.sender_id) not in OWNER and e.sender_id != DEV:
        return
    if e.photo:
        os.system("rm -f bot/thumb.jpg")
        await e.client.download_media(e.media, file="bot/thumb.jpg")
        await e.reply("🖼️ **Miniature enregistrée avec succès !**")


########### TRAITEMENT PRINCIPAL ###########

async def main_loop():
    while True:
        try:
            if not WORKING and QUEUE:
                user = int(OWNER.split()[0])
                e = await bot.send_message(user, "📥 **Téléchargement en cours...**")
                s = dt.now()
                dl, file = QUEUE[list(QUEUE.keys())[0]]
                dl_path = "downloads/" + dl
                os.makedirs("encode", exist_ok=True)

                with open(dl_path, "wb") as f:
                    await download_file(client=bot, location=file, out=f)

                es = dt.now()
                LOGS.info(f"Téléchargement terminé en {(es - s).seconds}s")

                out_base = f"encode/{os.path.basename(dl_path).split('.')[0]}"
                await e.edit("🗜 **Compression vidéo...**")

                # Compression dynamique
                results = compress_video(
                    dl_path,
                    out_base,
                    mode=RUNTIME["mode"],
                    multires=RUNTIME["multires"]
                )

                if not results:
                    await e.reply("❌ **Échec de la compression : aucun fichier généré.**")
                    QUEUE.pop(list(QUEUE.keys())[0])
                    WORKING.clear()
                    continue

                # Upload
                for out in results:
                    size = os.path.getsize(out)
                    caption = f"✅ **{os.path.basename(out)}**\n📦 {size/1024/1024:.2f} MB\n🎚 Mode : `{RUNTIME['mode']}`"
                    await e.client.send_file(
                        e.chat_id,
                        file=out,
                        caption=caption,
                        force_document=True,
                        thumb="bot/thumb.jpg" if os.path.exists("bot/thumb.jpg") else None
                    )
                    LOGS.info(f"Fichier envoyé : {out}")

                # Nettoyage
                QUEUE.pop(list(QUEUE.keys())[0])
                os.remove(dl_path)
                for f in results:
                    os.remove(f)

                WORKING.clear()
                await e.edit("✅ **Tâche terminée !**")

            await asyncio.sleep(3)
        except Exception as err:
            LOGS.error(f"[Erreur] {err}")
            await asyncio.sleep(2)

LOGS.info("🚀 Bot lancé avec succès.")
with bot:
    bot.loop.run_until_complete(main_loop())
    bot.loop.run_forever()
