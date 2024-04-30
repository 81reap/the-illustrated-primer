FROM docker.io/nvidia/cuda:12.4.1-devel-ubuntu22.04

WORKDIR /app
COPY chat.requirements.txt /app

RUN apt-get update
RUN apt-get install -y python3.11
RUN apt-get install -y python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y git

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r chat.requirements.txt
# todo :: figure out how to move this back to requirements.txt
RUN pip3 install --no-cache-dir --no-build-isolation flash-attn

COPY chat-llama3-70b.py /app

ENV QUART_APP=chat-llama3-70b:app
ENV QUART_ENV=production

EXPOSE 8113

CMD ["quart", "run", "--host", "0.0.0.0", "--port", "8113"]
