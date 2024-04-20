# The Illustrated Primer Server

This is the code for a Quart based inference endpoint. It uses ::
- LLAMA 3 8B + our custom Lora (wip)
- Distill Whisper

## Setup + Install

```bash
# install libsql from here https://github.com/tursodatabase/libsql/releases
$ sqld --db-path ./data --http-listen-addr 0.0.0.0:8085 --admin-listen-addr 0.0.0.0:8580 --enable-namespaces

# run server
$ huggingface-cli login
$ python3 -m venv server
$ source server/bin/activate
$ pip install -r requirements.txt
$ export QUART_APP=server:app && quart run --host 0.0.0.0 --port 5000

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
