from argparse import ArgumentParser
import os
import json
from config import (
    QA_DATASET,
    DATASETS_DIR,
    UNPARSED_DATASETS_DIR,
    JSON_EXT,
    TXT_EXT,
    FROM_UNPARSED,
    textbooks
)

def get_list_of_files(textbook):
    files_list = [filename for filename in os.listdir(os.path.join(UNPARSED_DATASETS_DIR, textbooks[textbook])) if filename.endswith(TXT_EXT)]
    return files_list

def return_text(textbook, filename):
    with open(os.path.join(UNPARSED_DATASETS_DIR, textbooks[textbook], filename)) as f:
        text = f.read()
    return text

def parse_json_from_text(textbook, filename):
    text = return_text(textbook, filename)
    try:
        parsed_json = json.loads(text, strict=False)
    except Exception as e:
        print(f'failed to parse {filename} to json due to -- {e}')
        parsed_json = []
    return parsed_json

def save_json_to_disk(parsed_json_list, textbook):
    filename = os.path.join(DATASETS_DIR, textbooks[textbook]+QA_DATASET+FROM_UNPARSED+JSON_EXT)
    print(f'saving dataset to: {filename}')
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w+') as f:
        json.dump(parsed_json_list, f)

def main():
    parser = ArgumentParser()
    parser.add_argument('-t', '--textbook', type=str, choices=list(textbooks.keys()), help='textbook to reparse failed question/answer pairs for')

    args = parser.parse_args()

    parsed_json_list = []

    for filename in get_list_of_files(args.textbook):
        parsed_json_list.extend(parse_json_from_text(args.textbook, filename))

    save_json_to_disk(parsed_json_list, args.textbook)

if __name__ == '__main__':
    main()