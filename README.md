# The Illustrated Primer

This was our team's submission for the GNEC 2024 Hackathon. It is designed to work along with one of our other projects, [DiplomaLink](https://github.com/81reap/diplomalink).

The Illustrated Primer is an educational platform powered by generative AI designed reduce educational inequalities accessible on low end consumer hardware. Leveraging various generative machine learning models, we are able to generate high-quality content in native languages and accessible formats that is both contextually relevant and tailored to the curriculum needs. The platform is designed to be used by multiple user groups like students, educators, and teachers in training.

## More Information

### Data + Training Pipeline

1. **Data Collection**: We scrape open-source educational content from sources like OpenStax to create a diverse dataset.
2. **Dataset Creation**: A custom dataset is generated focusing on instruction-following capabilities using few-shot learning techniques with LoRA.
3. **Model Fine-tuning**: LLMs are fine-tuned with the custom dataset to enhance their understanding and generation of educational content.
4. **Validation**: Rigorous testing and validation of the LLMs ensure the accuracy and quality of the generated content.

### Inference Pipeline

1. **Input Parsing**: Student inputs are parsed and interpreted using a combination of speech-to-text services (Whisper) and automated parsing tools.
2. **Prompt Generation**: AI generates prompts based on the parsed input to guide the LLM towards generating the required educational content.
3. **Content Generation**: The LLM uses retrieval-augmented generation (RAG) techniques to create detailed, accurate educational content.
4. **Scoring and Resampling**: The content is scored and resampled for quality and relevance.
5. **Output Parsing**: The generated content is parsed into different formats (text, audio, images) to match the preferred learning mode.
6. **Delivery**: The content is delivered back to the student, with options for text-to-speech conversion or other multimedia formats.

## Features

- **Customizable Learning**: The platform can adapt content based on specific student needs and educational goals.
- **Multimedia Support**: Generates and delivers content in various formats, including text, audio, and images, to cater to different learning styles.
- **Scalability**: Designed to work with both cloud-based and local compute resources, ensuring scalability and flexibility.
- **Accessibility**: Optimized to function on lower-end hardware, making it accessible to schools with limited technological infrastructure.

## Usage

This platform is suitable for:
- Educators seeking to supplement teaching with AI-generated content.
- Students who require additional educational support outside of the classroom.
- Developers interested in contributing to an open-source education project.

## Project Structure

- `dataset_generation/`: Scripts and tools used for scraping and processing educational content.
- `model_training/`: Code and datasets related to LLM training and fine-tuning.
- `server/`: The server side AI-driven content generation system + libSQL DB.
- `frontend/`: The Front-end interface for interacting with the platform. Will eventually support local llm infrenceing.
