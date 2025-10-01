FROM python:3.10-slim

RUN mkdir /bot && chmod 777 /bot
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget pv jq python3-dev ffmpeg mediainfo \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Installer le fix pour lxml
RUN pip3 install --no-cache-dir lxml[html_clean]

# Installer les dépendances du projet
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["bash","run.sh"]
