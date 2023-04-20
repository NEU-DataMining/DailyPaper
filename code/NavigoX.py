import configparser
import datetime
import os
import re
import time
from typing import Dict, List
from urllib.request import urlretrieve

import schedule
import tenacity

from database import Database
from get_arxiv import ArXiv
from process_pdf.get_summary import chat_paper_main
from sendemail import Email


class NavigoX:
    def __init__(
        self, 
        config_path:str, 
        database_path: str,
        language: str,
        pdf_path: str,
        output_path: str,
        file_format: str = 'md',
    ):
        config = configparser.ConfigParser()
        config.read(config_path)

        self.database_path = database_path
        # NavigoX
        self.query_list = config.get('NavigoX', 'QUERY')[1:-1].split(',')
        self.filter_keys_list = config.get('NavigoX', 'KEYS')[1:-1].split(',')
        self.max_results_list = [int(max_results) for max_results in config.get('NavigoX', 'MAX_RESULTS')[1:-1].split(',')]
        assert len(self.query_list) == len(self.filter_keys_list)
        assert len(self.max_results_list) == len(self.query_list)
        # Email
        self.host_server = config.get('Email', 'HOST_SERVER')
        self.host_password = config.get('Email', 'HOST_PASSWORD')
        self.sender_email = config.get('Email', 'SENDER')
        self.recevier = config.get('Email', 'RECEVIER')
        # Api2D
        self.apikey = config.get('Api2D', 'API2D_API_KEYS')
        
        self.emailtime = datetime.datetime.now().strftime("%Y年%m月%d日")
        self.language = language
        self.file_format = file_format

        self.pdf_path = pdf_path
        if not os.path.exists(self.pdf_path):
            os.makedirs(self.pdf_path)
        self.output_path = output_path

    def analysis_paper(self, key_word: str):
        chat_paper_main(
            pdf_path    = self.pdf_path,
            apikey      = self.apikey,
            key_word    = key_word,
            output_path = self.output_path,
            language    = self.language,
            file_format = self.file_format
        )
    # 链接数据库，更新数据库
    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                stop=tenacity.stop_after_attempt(5),
                reraise=True)
    def get_arxiv_dict(
        self,
        query: str,
        filter_keys: str,
        database_path: str,
        max_results: int=30
    ) -> List[Dict]:
        db = Database(db_name=database_path)
        myarxiv = ArXiv(
            query=query,
            filter_keys=filter_keys,
            max_results=max_results,
            id_list=[]
        )
        myarxiv.get_search()
        results = myarxiv.info_2_dict()

        pdf_url_dict_list = []
        for result in results:
            # print(result)
            if db.add_paper(result):
                # print(result)
                pdf_url_dict_list.append(result)
            else:
                pass
        for pdf_url_dict in pdf_url_dict_list:
            try:
                self.get_pdf(pdf_url_dict)
            except Exception as e:
                print(e)
    ## 下载论文
    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                stop=tenacity.stop_after_attempt(5),
                reraise=True)
    def get_pdf(self, pdf_url_dict: Dict):
        def validateTitle(title):
            # 将论文的乱七八糟的路径格式修正
            rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
            new_title = re.sub(rstr, "_", title)  # 替换为下划线
            return new_title
        title = validateTitle(pdf_url_dict['title']) + '.pdf'
        print('* * * [DOWNLOADING]: {} * * *'.format(title))
        path = os.path.join(self.pdf_path, title)
        written_path, _ = urlretrieve(pdf_url_dict['pdf_url'], path)
        return written_path
    
    def daily_arxiv(self):
        for query, filter_keys, max_results in zip(self.query_list, self.filter_keys_list, self.max_results_list):
            self.get_arxiv_dict(
                query         = query,
                database_path = self.database_path,
                filter_keys   = filter_keys,
                max_results   = max_results,
            )

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
            stop=tenacity.stop_after_attempt(5),
            reraise=True)
    def send_email(self):
        print("* * * * * * * * * * * ")
        print("发送今天的论文更新情况！")
        myemail = Email(
            sender_email    = self.sender_email,
            sender_password = self.host_password,
            host_server     = self.host_server,
            receiver_email  = self.recevier,
            subject         = '{} 论文更新情况'.format(self.emailtime),
            body            = "论文更新情况:"
        )
        localtime = datetime.datetime.now().strftime('%Y_%m_%d')
        output_path = os.path.join(self.output_path, '{}.md'.format(localtime))
        myemail.send_email_with_attachment(output_path)
        print("发送完毕！")
        print("* * * * * * * * * * * ")

    def delete_path_at_time(
        self,
        delta: int = -7,
        path_root: str = './Paper',
    ):
        delete_time = (datetime.datetime.now() + datetime.timedelta(days=delta)).strftime("%Y_%m_%d")
        delete_path = os.path.join(path_root, delete_time)
        if os.path.exists(delete_path):
            try:
                print("路径存在！删除{}的论文".format(delete_time))
                os.system('rm -rf {}'.format(delete_path))
            except Exception as e:
                print(e)
        else:
            print("路径不存在！")

def workflows(
        config_path:str, 
        database_path: str,
        pdf_path: str,
        output_path: str,
        key_word: str,
    ):
    start_time = time.time()
    navigox = NavigoX(
        config_path   = config_path,
        database_path = database_path,
        language      = 'zh',
        pdf_path      = pdf_path,
        output_path   = output_path,
    )
    navigox.daily_arxiv()
    navigox.analysis_paper(key_word=key_word)
    navigox.send_email()
    # 删除7天前的论文
    # navigox.delete_path_at_time(delta=-7)
    print("summary time:", time.time() - start_time)

def automatic():
    localtime = datetime.datetime.now().strftime('%Y_%m_%d')
    key_word = "deeplearning, ML, NLP, CV"
    workflows(
        config_path   = 'config.ini',
        database_path = './Database/article_xxx.db',
        pdf_path      = './Paper/{}'.format(localtime),
        output_path   = './Output',
        key_word      = key_word,
    )


if __name__ == '__main__':
    start_time = "10:30"
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time == start_time:
            automatic()
            time.sleep(3600*23)
        else:
            print(" * * * [current/start:{}/{}] ...waiting... * * * ".format(current_time, start_time))
            time.sleep(60)
