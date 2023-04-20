import jsonlines
from typing import List, Dict, Any
import os

def prompt_2_jsonl(
    prompt: List[Dict], 
    output_name: str
) -> None:
    output_name = os.path.join('./prompt_template', output_name)
    fp = jsonlines.open(output_name, 'w')
    for p in prompt:
        jsonlines.Writer.write(fp, p)
    fp.close()

def jsonl_2_prompt(
    input_name: str,
    replace_dict: Dict,
) -> List[Dict]:
    fp = open(input_name, 'r')
    reader = jsonlines.Reader(fp)
    messages = list()
    for p in reader:
        for k, v in replace_dict.items():
            p['content'] = p['content'].replace(k, v)
        messages.append(p)
    
    return messages

if __name__ == '__main__':
    replace_dict = {
        "[key_word]": "reinforcement learning",
        "[language]": "Chinese",
        "[clip_text]": "this is a text",
    }
    summary_messages: List[Dict] = [
        {"role": "system",
            "content": "You are a researcher in the field of [\"[key_word]\"] who is good at summarizing papers using concise statements"},
        {"role": "assistant",
            "content": "This is the title, author, link, abstract and introduction of an English document. I need your help to read and summarize the following questions: [clip_text]"},
        {"role": "user", "content": """                 
                1. Mark the title of the paper (with [language] translation)
                2. list all the authors' names (use English)
                3. mark the first author's affiliation (output [language] translation only)                 
                4. mark the keywords of this article (use English)
                5. link to the paper, Github code link (if available, fill in Github:None if not)
                6. summarize according to the following four points.Be sure to use [language] answers (proper nouns need to be marked in English)
                - (1):What is the research background of this article?
                - (2):What are the past methods? What are the problems with them? Is the approach well motivated?
                - (3):What is the research methodology proposed in this paper?
                - (4):On what task and what performance is achieved by the methods in this paper? Can the performance support their goals?
                - (5):What is the motivation for the research in this article?
                Follow the format of the output that follows:                  
                1. Title: xxx\n\n
                2. Authors: xxx\n\n
                3. Affiliation: xxx\n\n                 
                4. Keywords: xxx\n\n   
                5. Urls: xxx or xxx , xxx \n\n      
                6. Summary: \n\n
                - (1):xxx;\n 
                - (2):xxx;\n 
                - (3):xxx;\n  
                - (4):xxx.\n
                - (5):xxx.\n\n     
                
                Be sure to use [language] answers (proper nouns need to be marked in English), statements as concise and academic as possible, do not have too much repetitive information, numerical values using the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed.                 
                """},
    ]
    method_messages = [
            {"role": "system",
             "content": "You are a researcher in the field of [\"[keyword]\"] who is good at summarizing papers using concise statements"},
            # chatgpt 角色
            {"role": "assistant",
             "content": "This is the <summary> and <Method> part of an English document, where <summary> you have summarized, but the <Methods> part, I need your help to read and summarize the following questions: [clip_text]"},
            # 背景知识
            {"role": "user", "content": """                 
                 7. Describe in detail the methodological idea of this article. Be sure to use [language] answers (proper nouns need to be marked in English). For example, its steps are.
                    - (1):...
                    - (2):...
                    - (3):...
                    - .......
                 Follow the format of the output that follows: 
                 7. Methods: \n\n
                    - (1):xxx;\n 
                    - (2):xxx;\n 
                    - (3):xxx;\n  
                    ....... \n\n     
                 
                 Be sure to use [language] answers (proper nouns need to be marked in English), statements as concise and academic as possible, do not repeat the content of the previous <summary>, the value of the use of the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed, ....... means fill in according to the actual requirements, if not, you can not write.                 
                 """},
        ]
    conclusion_messages = [
            {"role": "system",
             "content": "You are a reviewer in the field of [\"[key_word]\"] and you need to critically review this article"},
            # chatgpt 角色
            {"role": "assistant",
             "content": "This is the <summary> and <conclusion> part of an English literature, where <summary> you have already summarized, but <conclusion> part, I need your help to summarize the following questions: [clip_text]"},
            # 背景知识，可以参考OpenReview的审稿流程
            {"role": "user", "content": """                 
                 8. Make the following summary.Be sure to use [language] answers (proper nouns need to be marked in English).
                    - (1):What is the significance of this piece of work?
                    - (2):Summarize the strengths and weaknesses of this article in three dimensions: innovation point, performance, and workload.                   
                    .......
                 9. As a rigorous and serious researcher, please list the strengths and weaknesses of the article, then rate the article (0-10) and give reasons
                 Follow the format of the output later: 
                 8. Conclusion: \n\n
                    - (1):xxx;\n                     
                    - (2):Innovation point: xxx; Performance: xxx; Workload: xxx;\n                      
                 9. Score and Recommend: \n\n
                    - strengths:\n
                    - weaknesses:\n
                    - scores:\n 
                 Be sure to use [language] answers (proper nouns need to be marked in English), statements as concise and academic as possible, do not repeat the content of the previous <summary>, the value of the use of the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed, ....... means fill in according to the actual requirements, if not, you can not write.                 
                 """},
        ]
    prompt_2_jsonl(prompt=summary_messages, output_name='prompt_summary.jsonl')
    # prompt_2_jsonl(prompt=method_messages, output_name='prompt_method.jsonl')
    # prompt_2_jsonl(prompt=conclusion_messages, output_name='prompt_conclusion.jsonl')
    
