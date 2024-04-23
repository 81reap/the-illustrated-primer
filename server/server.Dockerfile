FROM docker.io/nvidia/cuda:12.4.1-devel-ubuntu22.04

WORKDIR /app
#COPY server.py /app
COPY requirements.txt /app
#COPY Meta-Llama-3-8B-Instruct /app/Meta-Llama-3-8B-Instruct
#COPY distil-whisper/distil-large-v3 /app/distil-large-v3

RUN apt-get update
RUN apt-get install -y python3.11
RUN apt-get install -y python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y git

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
# todo :: figure out how to move this back to requirements.txt
RUN pip3 install --no-cache-dir --no-build-isolation flash-attn

COPY server.py /app

ENV QUART_APP=server:app
ENV QUART_ENV=production

EXPOSE 5000

CMD ["quart", "run", "--host", "0.0.0.0", "--port", "5000"]
