TEXTBOOK_DIR = 'parsed_textbooks'
TEXTBOOK_PDF_DIR = 'textbooks'
SYSTEM = 'system'
TEXT = 'text'
CHAPTER = 'chapter'
MAIN_TEXT = 'main_text'
KEY_TERMS = 'key_terms'
CHAPTER_SUMMARY = 'chapter_summary'
VISUAL_CONNECTION_QUESTIONS = 'visual_connection_questions'
CRITICAL_THINKING_QUESTIONS = 'critical_thinking_questions'
REVIEW_QUESTIONS = 'review_questions'
QA_DATASET = '_qa_dataset'
DATASETS_DIR = 'datasets'
UNPARSED_DATASETS_DIR = 'unparsed_dataset_files'
FROM_UNPARSED = '_from_unparsed'
PDF_EXT = '.pdf'
JSON_EXT = '.json'
TXT_EXT = '.txt'

textbooks = {
    'biology': 'Biology2e'
}

student_teacher_prompt = {
    SYSTEM: None,
    TEXT: '''
Based on the following textbook chapter, complete the task.
<textbook-chapter>
{textbook}
</textbook-chapter>

<task>
Generate 10 questions a confused high schooler might ask their teacher as they read the textbook chapter. Do not talk about being confused. Ask the question as if the student were sending a simple message to the teacher. For each question, write a teacher's response. Answer so that a high schooler can understand. Explain the reasoning thoroughly, step by step. Create a list of JSON objects with the keys "question" and "answer".
</task>
'''
}

textbook_question_prompts = {
    'biology': [
        {
            CRITICAL_THINKING_QUESTIONS: {
                SYSTEM: 'You are a knowledgeable teacher.',
                TEXT: '''Based on the following textbook chapter, complete the task.
<textbook-chapter>
{textbook}
</textbook-chapter>

<task>
Answer the following critical thinking questions. Give answers that would help a high schooler learn the textbook material better. Create a list of JSON objects with the keys "question" and "answer". Do not include the question number.
</task>

<questions>
{questions}
</questions>
'''
            },
            REVIEW_QUESTIONS: {
                SYSTEM: None,
                TEXT: '''Based on the following textbook chapter, complete the task.
<textbook-chapter>
{textbook}
</textbook-chapter>

<task>
Given the following multiple choice exam, rewrite each problem into a question that a high schooler might search up on the internet. Write an answer to that question with a short explanation of reasoning based on the textbook. Do not mention the textbook. Create a list of JSON objects with the keys "question" and "answer". Do not include the question number. Only include the list of questions and answers in the response, do not include any form of preamble.
</task>

<exam>
{questions}
</exam>
'''
            }
        }
    ]
}
