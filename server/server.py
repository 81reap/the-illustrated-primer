from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import sqlite3
import os
import torch
import re

app = Flask(__name__)
CORS(app)

# todo :: bundle this into a docker image
# todo :: We can use GPTQ here to compress the model before we even load it. However this requires GCC to be downgraded
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,)

device = "cpu" 
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"

model = AutoModelForCausalLM.from_pretrained(
    "Nexusflow/Starling-LM-7B-beta", 
    quantization_config=quantization_config,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    # todo :: This requires GCC to be downgraded as the latest CUDA uses a newer GCC than this can handle
    # https://huggingface.co/docs/transformers/perf_infer_gpu_one#flashattention-2
    # attn_implementation="flash_attention_2",
)#.to(device)
tokenizer = AutoTokenizer.from_pretrained("Nexusflow/Starling-LM-7B-beta", trust_remote_code=True)

def get_db_connection(db_name):
    db_path = f"{db_name}.db"
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 role TEXT,
                 content TEXT)''')
    return conn

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['input']
    db_name = request.json.get('db_name', 'default')
    lora_name = request.json.get('lora_name', None)
    
    conn = get_db_connection(db_name)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history")
    history = c.fetchall()

    messages = [{
        "role": "system",
        "content": "You professional educator who is trying to help a student learn a new concept. Be concise.",
    }]
    messages.extend({"role": role, "content": content} for role, content in history)
    messages.append({"role": "user", "content": user_input})

    # https://huggingface.co/docs/transformers/main/en/peft
    # model.load_lora_model(lora_name)

    # todo (prayag):: Stream the response to the front end
    # https://mathspp.com/blog/streaming-data-from-flask-to-htmx-using-server-side-events

    model_inputs = tokenizer.apply_chat_template(
        messages, 
        tokenize=True, 
        add_generation_prompt=True,
        #return_attention_mask=False,
        return_tensors="pt",
        torch_dtype=torch.bfloat16,)#.to(device)
    generated_ids = model.generate(
        model_inputs, 
        max_new_tokens=512, 
        do_sample=True)
    response = tokenizer.batch_decode(
        generated_ids, 
        skip_special_tokens=True,)
        #clean_up_tokenization_spaces=True)

    # Regex pattern to find the last assistant's answer
    pattern = r"GPT4 Correct Assistant: (.*?)(?=GPT4 Correct User:|$)"
    
    # Find all matches
    matches = re.findall(pattern, response[0], re.DOTALL)
    
    # Extract the last answer if any matches are found
    last_answer = matches[-1] if matches else None

    c.execute("INSERT INTO history (role, content) VALUES (?, ?)", ('user', user_input))
    c.execute("INSERT INTO history (role, content) VALUES (?, ?)", ('assistant', last_answer))
    conn.commit()

    return jsonify({'response': last_answer})

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