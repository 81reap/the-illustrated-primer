from argparse import ArgumentParser
import os
import anthropic
import json
import time
from datetime import datetime
from math import ceil
from config import (
    TEXTBOOK_DIR,
    textbooks,
    student_teacher_prompt,
    textbook_question_prompts,
    SYSTEM,
    TEXT,
    MAIN_TEXT,
    CRITICAL_THINKING_QUESTIONS,
    REVIEW_QUESTIONS,
    QA_DATASET,
    DATASETS_DIR,
    UNPARSED_DATASETS_DIR,
    JSON_EXT,
    TXT_EXT
)

def get_anthropic_client(key):
    client = anthropic.Anthropic(
        api_key=key
    )
    return client

def get_textbook_json(textbook):
    with open(os.path.join(TEXTBOOK_DIR, textbooks[textbook]+JSON_EXT)) as f:
        textbook_json = json.load(f)
    return textbook_json

def initialize(args):
    client = get_anthropic_client(args.key)
    textbook_json = get_textbook_json(args.textbook)
    if not os.path.exists(os.path.join(UNPARSED_DATASETS_DIR, textbooks[textbook])):
        os.makedirs(os.path.join(UNPARSED_DATASETS_DIR, textbooks[textbook]))
    return client, textbook_json

def query_claude(client, messages, system=None):
    start = datetime.now().timestamp()
    if system:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.2,
            system=system,
            messages=messages
        )
    else:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.2,
            messages=messages
        )
    end = datetime.now().timestamp()
    if end - start < 60:
        time.sleep(ceil(60 - (end - start)))
    return message

def parse_message(message):
    return message.content[0].text

def parse_message_to_json(message):
    parsed_message = parse_message(message)
    if parsed_message.find('[') >= 0:
        parsed_message = parsed_message[parsed_message.find('['):]
    try:
        parsed_message_json = json.loads(parsed_message, strict=False)
    except Exception as e:
        print(f'failed to parse {message.id} to json due to -- {e}')
        with open(os.path.join(UNPARSED_DATASETS_DIR, message.id+TXT_EXT), 'w+') as f:
            f.writelines([e, '\n', parsed_message])
        parsed_message_json = []
    return parsed_message_json

def create_messages(text):
    messages = [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': text
                }
            ]
        }
    ]
    return messages

def get_student_teacher_qa(client, chapter):
    print('\tgetting student-teacher qa')
    text = student_teacher_prompt[TEXT].format(textbook=chapter[MAIN_TEXT])
    messages = create_messages(text)
    results = query_claude(client, messages, student_teacher_prompt[SYSTEM])
    return parse_message_to_json(results)

def get_textbook_questions_answers(client, chapter, questions_list):
    question_answer_list_temp = []
    for question_set in questions_list:
        for questions_name,message_attr in question_set.items():
            print(f'\tgetting {questions_name} qa')
            text = message_attr[TEXT].format(textbook=chapter[MAIN_TEXT], questions=chapter[questions_name])
            messages = create_messages(text)
            results = query_claude(client, messages, message_attr[SYSTEM])
            question_answer_list_temp.extend(parse_message_to_json(results))
    return question_answer_list_temp

def save_json_to_disk(question_answers_json, textbook):
    filename = os.path.join(DATASETS_DIR, textbooks[textbook]+QA_DATASET+JSON_EXT)
    print(f'saving dataset to: {filename}')
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w+') as f:
        json.dump(question_answers_json, f)

def main():
    parser = ArgumentParser()
    parser.add_argument('-k', '--key', type=str, help='anthropic api key')
    parser.add_argument('-t', '--textbook', type=str, choices=list(textbooks.keys()), help='textbook to generate question/answer pairs for')
    parser.add_argument('-s', '--start', type=int, default=1, help='the starting chapter to generate question/answer pairs for, default to 1 for first chapter')
    parser.add_argument('-e', '--end', type=int, help='the ending chapter to generate question/answer pairs for, don\'t provide arg to go until last chapter')

    args = parser.parse_args()

    client, textbook_json = initialize(args)

    start = args.start
    end = args.end if args.end else len(textbook_json) + 1
    
    if end < 1 or end > (len(textbook_json) + 1):
        end = len(textbook_json) + 1
    if start <= 0 or start >= end:
        start = 1

    question_answer_list = []

    try:
        for i,chapter in enumerate(textbook_json[start-1:end]):
            print(f'chapter {i+start} of {end-1}')
            question_answer_list.extend(get_student_teacher_qa(client, chapter))
            question_answer_list.extend(get_textbook_questions_answers(client, chapter, textbook_question_prompts[args.textbook]))
    except Exception as e:
        print(f'failed on chapter {i+1} due to: {e}')
    finally:
        save_json_to_disk(question_answer_list, args.textbook)

if __name__ == '__main__':
    main()