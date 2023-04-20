import argparse
import datetime
import os
import re
import time

import numpy as np
import tiktoken
import sys
sys.path.append('..')
from api2d import OpenAI
from .get_paper_from_pdf import Paper

import glob
from .prompt_convert_json import jsonl_2_prompt, prompt_2_jsonl

# tiktoken 是一个fast bpe tokeniser
# 这里只保留处理summary（实际上是论文的第一页）的部分
class Reader:
    def __init__(
        self,
        apikey: str,
        key_word: str,
        output_path: str,
        language: str,
        file_format: str = 'md',
        root_path: str = '../',
    ):
        # 调用tiktoken来对文档编码
        self.key_word = key_word
        # 这个主要是用来算token的
        self.encoding = tiktoken.get_encoding("gpt2")
        self.output_path = output_path
        self.apikey = apikey
        if language == 'en':
            self.language = 'English'
        elif language == 'zh':
            self.language = 'Chinese'
        else:
            self.language = 'Chinese'
        self.max_token_num = 4096
        self.root_path = root_path
        self.file_format = file_format

        self.prompt_token_used = 0
        self.completion_token_used = 0
        self.total_token_used = 0

    def token_used_refresh(self, prompt_token_used, completion_token_used, total_token_used):
        self.prompt_token_used += prompt_token_used
        self.completion_token_used += completion_token_used
        self.total_token_used += total_token_used

    def show_token_used(self) -> None:
        ##TODO: 考虑加一个log
        print("* * * * * TOKEN USED INFO * * * * *")
        print("prompt token used: ", self.prompt_token_used)
        print("completion token used: ", self.completion_token_used)
        print("total token used: ", self.total_token_used)
        print("total P points used(API2D): ", self.total_token_used / 100)
        print("* * * * * PROCESS FINISH * * * * *")

    def chat_summary(
        self,
        text,
        summary_prompt_token=1100
    ):
        text_token = len(self.encoding.encode(text))
        clip_text_index = int(len(text) * (self.max_token_num - summary_prompt_token) / text_token)
        clip_text = text[:clip_text_index]
        # keyword, clip_text, language
        replace_dict = {
            "[clip_text]": clip_text,
            "[language]": self.language,
            "[key_word]": self.key_word,
        }
        messages = jsonl_2_prompt(
            input_name='./process_pdf/prompt_template/prompt_summary.jsonl',
            replace_dict=replace_dict
        )
        # print(messages)
        result, prompt_token_used, completion_token_used, total_token_used = self.get_response(messages)
        self.token_used_refresh(prompt_token_used=prompt_token_used, completion_token_used=completion_token_used, total_token_used=total_token_used)
        return result
    
    def init_export(self, local_time):
        htmls = []
        htmls.append("# {} Arxiv更新论文汇总".format(local_time))
        return htmls
    
    def summary_with_chat(self, paper_list):
        # init export file
        local_time = datetime.datetime.now().strftime("%Y_%m_%d")
        htmls = self.init_export(local_time=local_time)
        paper_index = 0
        if len(paper_list) == 0:
            htmls.append('今天没有论文更新！')
        ## summary & introduction section
        else:
            htmls.append('今天共有{}篇论文\n\n'.format(len(paper_list)))
            for paper_index, paper in enumerate(paper_list):
                text = ''
                text += 'Title' + paper.title
                text += 'Url:' + paper.url
                text += 'Abstract:' + paper.abs
                text += 'Paper_info:' + paper.section_text_dict['paper_info']
                # text += 'Introduction:' + paper.section_text_dict['Introduction']
                # intro
                text += list(paper.section_text_dict.values())[0]
                chat_summary_text = ""
                try:
                    chat_summary_text = self.chat_summary(text=text)
                except Exception as e:
                    print("summary_error:", e)
                    if "maximum context" in str(e):
                        current_tokens_index = str(e).find("your messages resulted in") + len(
                            "your messages resulted in") + 1
                        offset = int(str(e)[current_tokens_index:current_tokens_index + 4])
                        summary_prompt_token = offset + 1000 + 150
                        chat_summary_text = self.chat_summary(text=text, summary_prompt_token=summary_prompt_token)
                htmls.append(' ## Paper:' + str(paper_index + 1))
                htmls.append('\n\n\n')
                htmls.append(chat_summary_text)
                htmls.append('\n\n\n')
        # 整合文件，打包保存
        ## 
        export_path = self.output_path
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        
        mode = 'w' if paper_index == 0 else 'a'
        file_name = os.path.join(
            export_path,
            local_time + '.' + self.file_format
        )
        self.export_to_markdown("\n".join(htmls), file_name=file_name, mode=mode)
        self.show_token_used()
    
    def validateTitle(self, title):
        # 将论文的乱七八糟的路径格式修正
        rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
        new_title = re.sub(rstr, "_", title)  # 替换为下划线
        return new_title

    def export_to_markdown(
        self,
        text: str,
        file_name: str,
        mode='w'
    ) -> None:
        with open(file_name, mode, encoding='utf-8') as f:
            f.write(text)

    def get_response(self, message):
        #TODO 这里可以实现改变模型的接口
        myopenai = OpenAI(
            modelname='gpt-3.5-turbo', 
            apikey=self.apikey
        )
        response = myopenai.get_response(message=message)
        result, prompt_token_used, completion_token_used, total_token_used = myopenai.show_result(response)

        return result, prompt_token_used, completion_token_used, total_token_used
        
def chat_paper_main(
        pdf_path,
        apikey,
        key_word,
        output_path, 
        language, 
        file_format,
    ):
    paper_list = []
    if pdf_path.endswith(".pdf"):
        paper_list.append(
            Paper(path=pdf_path)
        )
    else:
        pdf_path_list = glob.glob(pdf_path + '/*.pdf')
        for pdf in pdf_path_list:
            paper = Paper(pdf)
            paper_list.append(paper)

    reader = Reader(apikey, key_word, output_path, language, file_format)
    reader.summary_with_chat(
        paper_list=paper_list
    )


if __name__ == '__main__':
    start_time = time.time()
    chat_paper_main(
        apikey='',
        key_word="",
        output_path = "./Output",
        language='zh',
        file_format='md',
    )
    print("summary time:", time.time() - start_time)