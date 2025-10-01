# Image Python légère basée sur Debian
FROM python:3.10-slim

# Créer un dossier pour le bot
RUN mkdir /bot && chmod 777 /bot
WORKDIR /bot

# Empêcher les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget pv jq python3-dev ffmpeg mediainfo \
    && rm -rf /var/lib/apt/lists/*

# Copier tous les fichiers du projet dans /bot
COPY . .

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Lancer ton bot
CMD ["bash", "run.sh"]
