# Primer Server Components

This is the code for a Quart based inference endpoint. It uses ::
- LLAMA 3 8B + our custom Lora (wip)
- LLAMA 3 70B + our custom Lora (wip)
- Distill Whisper

## Setup + Install

### Setting up the Pod

```bash
podman pod create --replace \
  -p 8085:8085 -p 8580:8580 -p 5001:5001 \
  -p 8111:8111 -p 8112:8112 -p 8113:8113 \
  primer
```

### Setting up the `libSQL` database

```bash
podman build -t libsql -f libsql.Dockerfile .
podman run --replace -dt --name primer-libsql --pod primer \
  --volume /mnt/black_hole/apps/primer/sqld:/data \
  libsql 

# validate libsql
curl -d '{"statements": ["CREATE TABLE IF NOT EXISTS users (username)", "INSERT INTO users VALUES (\"alice\")"]}' http://100.94.67.41:8085
curl -X POST -H "Content-Type: application/json" -d '{"statements": [{"q": "SELECT * FROM users"}]}' http://100.94.67.41:8085
# todo :: figure out namespaces
curl -X POST -H "Content-Type: application/json" -d '{}' http://100.94.67.41:8580/v1/namespaces/NAMESPACE/create 
curl -d '{"statements": ["CREATE TABLE IF NOT EXISTS users (username)", "INSERT INTO users VALUES (\"alice\")"]}' http://NAMESPACE:100.94.67.41:8085
```

### Setting up the Audio to Text endpoint

```bash
podman build -t listen -f listen.Dockerfile .
podman run --replace -dt --name primer-listen --pod primer \
  --env HF_TOKEN=hf_xd... \
  --volume /mnt/black_hole/apps/primer/huggingface:/root/.cache/huggingface \
  --security-opt label=disable \
  --device nvidia.com/gpu=all \
  listen

# validate listen
curl -X POST -H "X-Request-ID: request-1" -F "audio=@/Users/prayagbhakar/Downloads/DIALOGUE.mp3" http://100.94.67.41:8101/transcribe
```

### Setting up the Text to Text endpoints

```bash
# === LLAMA 3 7B ===
podman build -t chat-llama3-8b -f chat-llama3-8b.Dockerfile .
podman run --replace -dt --name primer-chat-llama3-8b --pod primer \
  --env HF_TOKEN=hf_xd... \
  --volume /mnt/black_hole/apps/primer/huggingface:/root/.cache/huggingface \
  --security-opt label=disable \
  --device nvidia.com/gpu=all \
  chat-llama3-8b

# validate chat-llama3-8b
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"conversation": [
    {"role": "system","content": "You are a helpful ai assistant."},
    {"role": "user","content": "Hello, how are you today?"},
    {"role": "assistant","content": "Im good, thank you for asking! How can I assist you today?"},
    {"role": "user","content": "Can you tell me more about LLAMA 3?"}
  ]}' http://100.94.67.41:8112/respond

# === LLAMA 3 70B ===
podman build -t chat-llama3-70b -f chat-llama3-70b.Dockerfile .
podman run --replace -dt --name primer-chat-llama3-70b --pod primer \
  --env HF_TOKEN=hf_xd... \
  --volume /mnt/black_hole/apps/primer/huggingface:/root/.cache/huggingface \
  --security-opt label=disable \
  --device nvidia.com/gpu=all \
  chat-llama3-70b

# validate chat-llama3-70b
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"conversation": [
    {"role": "system","content": "You are a helpful ai assistant."},
    {"role": "user","content": "Hello, how are you today?"},
    {"role": "assistant","content": "Im good, thank you for asking! How can I assist you today?"},
    {"role": "user","content": "Can you tell me more about LLAMA 3?"}
  ]}' http://100.94.67.41:8113/respond
```

## Resources
- https://quart.palletsprojects.com/en/latest/reference/cheatsheet.html
- https://github.com/tursodatabase/libsql
- https://github.com/tursodatabase/libsql-client-py
- https://huggingface.co/docs/hub/en/security-tokens
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html

