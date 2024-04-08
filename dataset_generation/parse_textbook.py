from argparse import ArgumentParser
import json
import os
import fitz # if missing, pip install pymupdf

from config import (
    TEXTBOOK_PDF_DIR,
    TEXTBOOK_DIR,
    PDF_EXT,
    JSON_EXT,
    CHAPTER,
    MAIN_TEXT,
    KEY_TERMS,
    CHAPTER_SUMMARY,
    VISUAL_CONNECTION_QUESTIONS,
    CRITICAL_THINKING_QUESTIONS,
    REVIEW_QUESTIONS,
    textbooks
)

def get_text(textbook):
    doc = fitz.open(os.path.join(TEXTBOOK_PDF_DIR, textbooks[textbook]+PDF_EXT))
    text = ''
    for page in doc:
        text += page.get_text()
    return text

def split_text_by_chapter(textbook):
    return get_text(textbook).split('CHAPTER')

def cut_out_textbook_intro(textbook):
    text_by_chapter = split_text_by_chapter(textbook)
    chapter_one_index = None
    for i,t in enumerate(text_by_chapter):
        if 'INTRODUCTION' in t:
            chapter_one_index = i
            break
    return text_by_chapter[chapter_one_index:]

def parse_chapters_into_json(text_by_chapter):
    parsed_chapters = []
    chapter = 0
    for section in text_by_chapter:
        # main chapter section + key terms
        if 'INTRODUCTION' in section:
            chapter_dict = {}
            chapter += 1
            chapter_dict['chapter'] = chapter
            section_split = section.split('KEY TERMS')
            chapter_dict['main_text'] = section_split[0]
            if len(section_split) == 2:
                chapter_dict['key_terms'] = section_split[1]
        # chapter summary, visual connection questions, review questions, critical thinking questions
        elif 'SUMMARY' in section:
            section = section.split('APPENDIX')[0]
            section_split_vis = section.split('VISUAL CONNECTION QUESTIONS')
            chapter_dict['chapter_summary'] = section_split_vis[0]
            if len(section_split_vis) == 2:
                section_split_review = section_split_vis[1].split('REVIEW QUESTIONS')
                chapter_dict['visual_connection_questions'] = section_split_review[0]
                if len(section_split_review) == 2:
                    section_split_crit = section_split_review[1].split('CRITICAL THINKING QUESTIONS')
                    chapter_dict['review_questions'] = section_split_crit[0]
                    if len(section_split_crit) == 2:
                        chapter_dict['critical_thinking_questions'] = section_split_crit[1]
            parsed_chapters.append(chapter_dict)
    return parsed_chapters

def save_json_to_disk(parsed_chapters, textbook):
    with open(os.path.join(TEXTBOOK_DIR, textbooks[textbook]+JSON_EXT), 'w+') as f:
        json.dump(parsed_chapters, f)

def main():
    parser = ArgumentParser()
    parser.add_argument('-t', '--textbook', type=str, required=True, choices=list(textbooks.keys()), help='textbook PDF to parse')

    args = parser.parse_args()

    text_by_chapter = cut_out_textbook_intro(args.textbook)
    parsed_chapters = parse_chapters_into_json(text_by_chapter)
    save_json_to_disk(parsed_chapters, args.textbook)

if __name__ == '__main__':
    main()