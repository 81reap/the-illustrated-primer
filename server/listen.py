from quart import Quart, request, jsonify, Response
import asyncio
import torch
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor, AutoTokenizer
from transformers.utils import is_flash_attn_2_available
from transformers import BitsAndBytesConfig
import os
import uuid
from pydub import AudioSegment

torch.random.manual_seed(420)
app = Quart(__name__)

transcription_queue = asyncio.Queue()

async def process_transcription_queue():
  while True:
    item = await transcription_queue.get()
    audio_path = item[0]
    request_id = item[1]

    transcription = whisper_pipeline(
      audio_path,
      chunk_length_s=30,
      stride_length_s=5,
    )

    yield {"id": request_id, "transcription": transcription}
    transcription_queue.task_done()

quantization_config = BitsAndBytesConfig(
  load_in_4bit=torch.cuda.is_available(),
  bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
)

whisper_pipeline = pipeline(
  "automatic-speech-recognition",
  model=AutoModelForSpeechSeq2Seq.from_pretrained(
    "distil-whisper/distil-large-v3",
    quantization_config=quantization_config,
  ),
  tokenizer=AutoProcessor.from_pretrained("distil-whisper/distil-large-v3").tokenizer,
  feature_extractor=AutoProcessor.from_pretrained("distil-whisper/distil-large-v3").feature_extractor,
  model_kwargs={"attn_implementation": "flash_attention_2" if is_flash_attn_2_available() else "sdpa"},
)

@app.route('/transcribe', methods=['POST'])
async def transcribe():
  audio_file = (await request.files)['audio']
  request_id = request.headers.get('X-Request-ID')
  filename = str(uuid.uuid4()) + ".mp3"
  file_path = os.path.join('uploaded_audio', filename)

  # Ensure the directory exists
  os.makedirs(os.path.dirname(file_path), exist_ok=True)

  # Save the file
  audio = AudioSegment.from_file_using_temporary_files(audio_file)
  audio.export(file_path, format='mp3')

  # Put the file path and request_id into the transcription queue
  await transcription_queue.put((file_path, request_id))

  async def stream_transcription():
    async for result in process_transcription_queue():
      if result["id"] == request_id:
        # Assuming 'transcription' is a string, encode it directly
        transcription_text = result["transcription"]
        if isinstance(transcription_text, dict):
          # If transcription is a dictionary, extract the actual text part, adjust the key as necessary
          transcription_text = transcription_text['text']
        yield transcription_text.encode('utf-8')

  return Response(stream_transcription(), mimetype='text/plain')

if __name__ == '__main__':
  app.run()

