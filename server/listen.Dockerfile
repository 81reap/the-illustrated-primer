FROM docker.io/nvidia/cuda:12.4.1-devel-ubuntu22.04

WORKDIR /app
COPY listen.requirements.txt /app

RUN apt-get update
RUN apt-get install -y python3.11
RUN apt-get install -y python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y git

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r listen.requirements.txt
# todo :: figure out how to move this back to requirements.txt
RUN pip3 install --no-cache-dir --no-build-isolation flash-attn

COPY listen.py /app

ENV QUART_APP=listen:app
ENV QUART_ENV=production

EXPOSE 8111

CMD ["quart", "run", "--host", "0.0.0.0", "--port", "8111"]
