# The Illustrated Primer Server

This is the code for a Flask based inference endpoint of Mistral 7B + our custom Lora. 

## Setup + Installation
```bash
# setting up the env
$ python3 -m venv server
$ source server/bin/activate
$ pip install flask transformers bitsandbytes accelerate torch torchvision torchaudio optimum flask-cors soundfile wheel
$ pip install flash-attn --no-build-isolation
$ python3 server.py 
# [optional]if you are getting precision errors then add these flags --precision full --no-half
$ deactivate

# serve the server with flask
$ flask --app server run --host=0.0.0.0
# [optional] to debug add the --debug flag

# serve the server with a systemd service
$ vim /etc/systemd/system/unicc-flask.service
$ systemctl daemon-reload
$ systemctl enable unicc-flask.service
$ systemctl start unicc-flask.service

# test the chat endpoint
$ curl -X POST -H "Content-Type: application/json" -d '{
  "input": "INPUT",
  "db_name": "CONVERSATION_DATABASE_NAME",
  "lora_name": null
}' http://100.100.11.57:5000/api/chat 

# test the audio chat endpoint
$ curl -X POST -F "messageFile=@/Users/prayagbhakar/Downloads/DIALOGUE.mp3" http://100.94.67.41:5000/api/chat/audio
```