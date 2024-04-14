from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, ConversationalPipeline, Conversation, pipeline, AutoModelForCTC, AutoProcessor, AutoModelForSpeechSeq2Seq
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import sqlite3
import os
import torch
import re
from transformers.utils import is_flash_attn_2_available

app = Flask(__name__)
CORS(app)

device = torch.device("cpu")
dtype = torch.float16
if torch.cuda.is_available():
    device = torch.device("cuda")
    dtype = torch.bfloat16
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    dtype = torch.float32

# todo :: bundle this into a docker image
# todo :: We can use GPTQ here to compress the model before we even load it. However this requires GCC to be downgraded
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=dtype,)

conversations = {}

chat_pipeline = ConversationalPipeline(
    model=AutoModelForCausalLM.from_pretrained(
        "Nexusflow/Starling-LM-7B-beta", 
        quantization_config=quantization_config, 
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else "sdpa",
        trust_remote_code=True, 
        low_cpu_mem_usage=True, 
        torch_dtype=dtype,
        device_map="auto"),
    tokenizer=AutoTokenizer.from_pretrained(
        "Nexusflow/Starling-LM-7B-beta", 
        trust_remote_code=True),)

audio_to_text_pipeline = pipeline(
    "automatic-speech-recognition",
    model=AutoModelForSpeechSeq2Seq.from_pretrained(
        "distil-whisper/distil-large-v3", 
        torch_dtype=dtype, 
        low_cpu_mem_usage=True, 
        use_safetensors=True,
        quantization_config=quantization_config,),
    tokenizer=AutoProcessor.from_pretrained(
        "distil-whisper/distil-large-v3").tokenizer,
    feature_extractor=AutoProcessor.from_pretrained(
        "distil-whisper/distil-large-v3").feature_extractor,
    torch_dtype=dtype,
    model_kwargs={"attn_implementation": "flash_attention_2" if is_flash_attn_2_available() else "sdpa"},)

def get_db_connection(db_name):
    db_path = f"{db_name}.db"
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 role TEXT,
                 content TEXT)''')
    return conn

def load_conversation_from_db(db_name):
    conn = get_db_connection(db_name)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history")
    history = c.fetchall()

    conversation = Conversation(
        system="You professional educator who is trying to help a student learn a new concept. Be concise."
    )

    for role, content in history:
        conversation.add_message({"role": role, "content": content})

    return conversation

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['input']
    db_name = request.json.get('db_name', 'default')
    lora = request.json.get('lora', 'normal')
    
    if db_name not in conversations:
        conversations[db_name] = load_conversation_from_db(db_name)
    
    conversation = conversations[db_name]
    conversation.add_user_input(user_input)

    # if lora :
    #     chat_pipeline.model.load_adapter(lora)
    # else:
    #     chat_pipeline.model.disable_adapter()

    response = chat_pipeline([conversation])

    last_answer = response.generated_responses[-1]
    conversation.mark_processed()

    conn = get_db_connection(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO history (role, content) VALUES (?, ?)", ('user', user_input))
    c.execute("INSERT INTO history (role, content) VALUES (?, ?)", ('assistant', last_answer))
    conn.commit()

    return jsonify({'response': last_answer})

@app.route('/api/chat/audio', methods=['POST'])
def chatAudio():
    audio_file = request.files['messageFile']
    audio_file.save('./tmpAudio.mp3')
    
    outputs = audio_to_text_pipeline(
        './tmpAudio.mp3',
        chunk_length_s=30,
        batch_size=24,
        return_timestamps=True,)

    # todo :: see if there is a better way than few shot prompting
    prompt = Conversation(system="Formulate a question for an LLM based on the provided audio transcript. Pretend that you are the user who has asked this. Do let the user know EVER that you are an LLM asking a quesiton, just repharase the questions. Be concise. Condense long questions into a simpler smaller one. ONLY RETURN ONE QUESTION. DO NOT INCLUDE SUMMARIES.")
    prompt.add_message({"role":"user", "content":"The recent advancements in artificial intelligence have raised ethical concerns regarding privacy and autonomy."})
    prompt.add_message({"role":"assistant", "content":"What are the ethical concerns associated with recent advancements in artificial intelligence, particularly in terms of privacy and autonomy?"})
    prompt.add_message({"role":"user", "content":"The economic impact of climate change is becoming increasingly significant, with potential effects on agriculture, infrastructure, and overall global stability."})
    prompt.add_message({"role":"assistant", "content":"What are the potential economic impacts of climate change on agriculture and infrastructure, and how might they affect global stability?"})
    prompt.add_message({"role":"user", "content":outputs['text']})

    response = chat_pipeline([prompt])
    
    return jsonify({'response': response.generated_responses[-1]})

@app.route('/api/history', methods=['GET'])
def get_history():
    db_name = request.args.get('db_name', 'default')
    db_path = f"{db_name}.db"

    if not os.path.exists(db_path):
        return jsonify({'history': []})
    
    conn = get_db_connection(db_name)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history")
    history = c.fetchall()

    messages = [{"role": role, "content": content} for role, content in history]
    return jsonify({'history': messages})

if __name__ == '__main__':
    app.run(host='0.0.0.0')