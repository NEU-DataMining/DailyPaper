import requests
from typing import Dict, List, Any

class OpenAI:
    def __init__(
        self,
        modelname: str,
        apikey: str, 
        url: str = "https://openai.api2d.net/v1/chat/completions",
    ):
        self.apikey = apikey
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.apikey)
        }
        self.modelname = modelname
        self.url = url
    def get_response(
        self,
        message: List[Dict]
    ):
        data = {
            "model": self.modelname,
            "messages": message,
        }
        response = requests.post(self.url, headers=self.headers, json=data)
        return response.json()
    
    def show_result(
        self,
        response: Dict[str, Any],
    ):
        result = ''
        for choice in response['choices']:
            result += choice['message']['content']
        usage = response['usage']
        prompt_token_used = usage['prompt_tokens']
        completion_token_used = usage['completion_tokens']
        total_token_used = usage['total_tokens'] 
        print("result :{}\n \
            prompt_token_used: {}\n \
            completion_token_used: {}\n \
            total_token_used: {}\n \
            ".format(result, 
                    prompt_token_used, 
                    completion_token_used, 
                    total_token_used
        ))
        return result, prompt_token_used, completion_token_used, total_token_used


if __name__ == '__main__':
    modelname = 'gpt-3.5-turbo'
    message = [
        {
            "role": "system",
            "content": "hello, how are you?"
        },
    ]
    myapi = OpenAI(modelname)
    response = myapi.get_response(
        message
    )
    myapi.show_result(response)