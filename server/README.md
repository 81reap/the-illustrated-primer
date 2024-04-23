# The Illustrated Primer Server

This is the code for a Quart based inference endpoint. It uses ::
- LLAMA 3 8B + our custom Lora (wip)
- Distill Whisper

## Setup + Install

```bash
podman build -t libsql -f libsql.Dockerfile .
podman build -t server -f server.Dockerfile .
podman play kube pod.primer.yaml 

# test creation endpoint
$ curl -X POST -H "Content-Type: application/json" -d '{
  "user_uuid": "1234"
}' http://100.94.67.41:5000/api/create_user 
# test chat endpoint
$ curl -X POST -H "Content-Type: application/json" -d '{
  "input": "ELI5 :: String Theory",
  "user_uuid": "1234",
  "channel": "default",
  "thread": "default",
  "lora_name": null
}' http://100.94.67.41:5000/api/chat 
# test the audio chat endpoint
$ curl -X POST -F "messageFile=@/Users/prayagbhakar/Downloads/DIALOGUE.mp3" http://100.94.67.41:5000/api/chat/audio
# test history endpoint
$ curl 'http://100.94.67.41:5000/api/history?user_uuid=1234'
```

## Resources
- https://quart.palletsprojects.com/en/latest/reference/cheatsheet.html
- https://github.com/tursodatabase/libsql
- https://github.com/tursodatabase/libsql-client-py
- https://huggingface.co/docs/hub/en/security-tokens
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html
