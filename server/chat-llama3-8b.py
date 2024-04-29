from quart import Quart, request, jsonify, Response
import asyncio
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, ConversationalPipeline, Conversation, TextIteratorStreamer
from transformers.utils import is_flash_attn_2_available
from transformers import BitsAndBytesConfig
import os
import uuid

torch.random.manual_seed(420)
app = Quart(__name__)

dtype = torch.bfloat16
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=dtype,
)
chat_pipeline = ConversationalPipeline(
    model=AutoModelForCausalLM.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        quantization_config=quantization_config,
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else "sdpa",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        torch_dtype=dtype,
        device_map="auto"
    ),
    tokenizer=AutoTokenizer.from_pretrained(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        trust_remote_code=True
    )
)
chat_terminators = [
    chat_pipeline.tokenizer.eos_token_id,
    chat_pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

@app.route('/respond', methods=['POST'])
async def respond():
    try:
        data = await request.get_json()
        conversation = Conversation()
        
        # Load messages into the conversation
        for msg in data['conversation']:
            conversation.add_message({"role": msg['role'], "content": msg['content']})

        # Process the conversation using the pipeline
        updated_conversation = chat_pipeline(conversation,  eos_token_id=chat_terminators, min_new_tokens=30, max_new_tokens=1024, do_sample=True, temperature=0.6, top_p=0.9,)
        
        # Extract and send the last message in the conversation as the response
        last_response = updated_conversation.messages[-1]["content"] if updated_conversation.messages else ""
        return jsonify({"response": last_response})
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"error": "Failed to generate response", "details": str(e)}), 500


if __name__ == '__main__':
    app.run()
