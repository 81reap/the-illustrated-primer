import asyncio
import aiohttp
import libsql_client
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, ConversationalPipeline, Conversation, pipeline, AutoModelForCTC, AutoProcessor, AutoModelForSpeechSeq2Seq
from quart import Quart, request, jsonify, Response
from quart_cors import cors
import json
import os
import torch
import re
from transformers.utils import is_flash_attn_2_available
from datetime import datetime
# todo :: use proper UUIDs
import uuid

app = Quart(__name__)
app = cors(app)

device = torch.device("cpu")
dtype = torch.float16
if torch.cuda.is_available():
    device = torch.device("cuda")
    dtype = torch.bfloat16
elif torch.backends.mps.is_available():
    device = torch.device("mps")
    dtype = torch.float32

# todo :: check why this is only sometimes being applied
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=dtype,)

# todo :: there's some stuff in the LLAMA 3 license that effects us. we should eventually read it and make the corresponding changes
chat_pipeline = ConversationalPipeline(
    model=AutoModelForCausalLM.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct", 
        quantization_config=quantization_config, 
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else "sdpa",
        trust_remote_code=True, 
        low_cpu_mem_usage=True, 
        torch_dtype=dtype,
        device_map="auto"),
    tokenizer=AutoTokenizer.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct", 
        trust_remote_code=True),)
chat_terminators = [
    chat_pipeline.tokenizer.eos_token_id,
    chat_pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

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

# todo :: move queue pipelines to separate files for scalability
chat_queue = asyncio.Queue()
audio_queue = asyncio.Queue()

async def process_chat_queue():
    while True:
        conversation = await chat_queue.get()
        # todo :: play around output settings and their memory penalites
        # beam search :: https://huggingface.co/docs/transformers/en/main_classes/text_generation#transformers.GenerationConfig.num_beams
        # -> num_beams=4, early_stopping=True, low_memory=True
        # temp + more :: https://huggingface.co/docs/transformers/en/main_classes/text_generation#transformers.GenerationConfig.temperature
        response = chat_pipeline([conversation], eos_token_id=chat_terminators, min_new_tokens=30, max_new_tokens=1024, do_sample=True, temperature=0.6, top_p=0.9,)
        last_answer = response.generated_responses[-1]
        conversation.mark_processed()
        chat_queue.task_done()
        return last_answer

# todo :: do we really need this to be a seperate processing queue?
async def process_audio_queue():
    while True:
        prompt = await audio_queue.get()
        response = chat_pipeline([prompt])
        audio_queue.task_done()
        return response.generated_responses[-1]

# todo :: add delete
# curl -X DELETE "http://100.94.67.41:8580/v1/namespaces/1234"
@app.route('/api/create_user', methods=['POST'])
async def create_user():
    data = await request.get_json()
    user_uuid = data['user_uuid']
    
    # Async HTTP session to communicate with the admin API
    async with aiohttp.ClientSession() as session:
        # Create the namespace via the admin API
        async with session.post(f"http://localhost:8580/v1/namespaces/{user_uuid}/create", json={}) as response:
            if response.status != 200:
                return jsonify({'error': 'Failed to create namespace'}), 500

    async with libsql_client.create_client(f"http://{user_uuid}.db.sarna.dev:8085") as conn :
        await conn.execute('''CREATE TABLE IF NOT EXISTS history
                            (timestamp TEXT,
                             channel TEXT,
                             thread TEXT,
                             role TEXT,
                             message TEXT,
                             uuid TEXT)''')
    return jsonify({'message': 'User created successfully'})

async def load_conversation_from_db(user_uuid):
    async with libsql_client.create_client(f"http://{user_uuid}.db.sarna.dev:8085") as conn:
        result_set = await conn.execute("SELECT role, message FROM history")

    conversation = Conversation(
        system="You professional educator who is trying to help a student learn a new concept. Be concise."
    )

    for row in result_set.rows:
        conversation.add_message({"role": row[0], "content": row[1]})

    return conversation

@app.route('/api/chat', methods=['POST'])
async def chat():
    data = await request.get_json()
    user_input = data['input']
    user_uuid = data['user_uuid']
    channel = data['channel']
    thread = data['thread']
    #lora = data.get('lora', 'normal')
    
    conversation = await load_conversation_from_db(user_uuid)
    conversation.add_user_input(user_input)

    await chat_queue.put(conversation)
    last_answer = await asyncio.create_task(process_chat_queue())

    async with libsql_client.create_client(f"http://{user_uuid}.db.sarna.dev:8085") as conn:
        await conn.execute("INSERT INTO history (timestamp, channel, thread, role, message, uuid) VALUES (?, ?, ?, ?, ?, ?)", (datetime.now().isoformat(), channel, thread, 'user', user_input, str(uuid.uuid4())))
        await conn.execute("INSERT INTO history (timestamp, channel, thread, role, message, uuid) VALUES (?, ?, ?, ?, ?, ?)", (datetime.now().isoformat(), channel, thread, 'assistant', last_answer, str(uuid.uuid4())))

    return jsonify({'response': last_answer})

# todo :: fix async file parsing, this currently doesn't work
@app.route('/api/chat/audio', methods=['POST'])
async def chatAudio():
    audio_file = (await request.files)['messageFile']
    data = await request.get_json()
    user_uuid = data['user_uuid']
    channel = data['channel']
    thread = data['thread']
    
    # todo :: improve compatibility with more filetypes
    file_path = f"/data/files/{user_uuid}/{str(uuid.uuid4())}.mp3"
    await audio_file.save(file_path)
    
    # todo :: tune hyperparams
    outputs = audio_to_text_pipeline(
        file_path,
        chunk_length_s=30,
        batch_size=24,
        return_timestamps=False,)

    # todo :: further testing required
    prompt = Conversation(system="Convert the following audio transcript excerpts into succinct questions. Assume the role of an assistant who rephrases user statements into direct questions without disclosing your identity as an LLM. Each question should be concise, addressing only the core issue mentioned in the transcript. Provide only one question for each user input.")
    prompt.add_message({"role":"user", "content":"So, I was at this seminar last week where they were talking about AI, and they brought up some pretty big concerns about how it's affecting our privacy and even our freedom to make choices, you know?"})
    prompt.add_message({"role":"assistant", "content":"What are the main ethical concerns related to AI impacting privacy and personal autonomy as discussed in the seminar?"})
    prompt.add_message({"role":"user", "content":"Oh, and there was also this part where they discussed climate change. They said it's not just about the weather — it's making things tougher for farmers, it’s messing up our roads and buildings, and it might even shake up the whole world economy."})
    prompt.add_message({"role":"assistant", "content":"What are the projected economic impacts of climate change on agriculture and infrastructure, and how could these affect global stability?"})
    prompt.add_message({"role":"user", "content":"You know, when I was listening to this really long lecture the other day, the speaker went on and on about various things, but what really stuck with me was this part where they talked about how technology is just moving so fast and it’s kind of scary, you know? They mentioned something about computers getting smarter than us and what that might mean for jobs and, well, just everyday life in general."})
    prompt.add_message({"role":"assistant", "content":"What concerns did the speaker express about the rapid advancement of technology and its potential impact on employment and daily life?"})
    prompt.add_message({"role":"user", "content":outputs['text']})

    await audio_queue.put(prompt)
    response_text = await asyncio.create_task(process_audio_queue())
    
    # todo :: fix how audio transcripts are stored
    async with libsql_client.create_client(f"http://{user_uuid}.db.sarna.dev:8085") as conn:
        #await conn.execute("INSERT INTO history (timestamp, channel, thread, role, message, uuid) VALUES (?, ?, ?, ?, ?, ?)", (datetime.now().isoformat(), channel, thread, 'user_audio', file_path, str(uuid.uuid4())))
        await conn.execute("INSERT INTO history (timestamp, channel, thread, role, message, uuid) VALUES (?, ?, ?, ?, ?, ?)", (datetime.now().isoformat(), channel, thread, 'user', response_text, str(uuid.uuid4())))
        await conn.execute("INSERT INTO history (timestamp, channel, thread, role, message, uuid) VALUES (?, ?, ?, ?, ?, ?)", (datetime.now().isoformat(), channel, thread, 'assistant', response_text, str(uuid.uuid4())))
    
    return jsonify({'response': response_text})

@app.route('/api/history', methods=['GET'])
async def get_history():
    user_uuid = request.args['user_uuid']

    async with libsql_client.create_client(f"http://{user_uuid}.db.sarna.dev:8085") as conn:
        result_set = await conn.execute("SELECT role, message FROM history")

    blocklist = ['user_audio']
    messages = [{"role": row[0], "content": row[1]} for row in result_set.rows]
    return jsonify({'history': messages})

async def start_background_tasks():
    asyncio.create_task(process_chat_queue())
    asyncio.create_task(process_audio_queue())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_background_tasks())
    app.run(loop=loop)
