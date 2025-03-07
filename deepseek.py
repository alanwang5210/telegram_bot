import requests

from config import config_data
from OutPut import op


class AiDialogue:

    def __init__(self):
        self.systemAiRole = config_data['aiConfig']['systemAiRule']

        self.localDeepSeekModelConfig = {
            'localDeepSeekApi': config_data['aiConfig']['localDeepSeek']['localDeepSeekApi'],
            'localDeepSeekModel': config_data['aiConfig']['localDeepSeek']['localDeepSeekModel']
        }
        self.siliconFlowConfig = {
            'siliconFlowApi': config_data['aiConfig']['siliconFlow']['siliconFlowApi'],
            'siliconFlowKey': config_data['aiConfig']['siliconFlow']['siliconFlowKey'],
            'siliconFlowModel': config_data['aiConfig']['siliconFlow']['siliconFlowModel']
        }
        self.deepSeekMessages = [{"role": "system", "content": f'{self.systemAiRole}'}]
        self.siliconFlowMessages = [{"role": "system", "content": f'{self.systemAiRole}'}]
        self.aiPriority = config_data['aiConfig']['aiPriority']

    def get_silicon_flow(self, content, message):
        """
        deepSeek
        :param content: 对话内容
        :param message: 消息列表
        :return:
        """
        op(f'[*]: 正在调用硅基流动对话接口... ...')
        if not self.siliconFlowConfig.get('siliconFlowKey'):
            op(f'[-]: deepSeek模型未配置, 请检查相关配置!!!')
            return None, []
        message.append({"role": "user", "content": f'{content}'})
        data = {
            "model": self.siliconFlowConfig.get('siliconFlowModel'),
            "messages": message
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.siliconFlowConfig.get('siliconFlowKey')}",
        }
        try:
            resp = requests.post(url=self.siliconFlowConfig.get('siliconFlowApi'), headers=headers, json=data,
                                 timeout=300)
            json_data = resp.json()
            assistant_content = json_data['choices'][0]['message']['content']
            messages.append({"role": "assistant", "content": f"{assistant_content}"})
            if len(messages) == 21:
                del messages[1]
                del messages[2]
            return assistant_content, messages
        except Exception as e:
            op(f'[-]: 硅基对话接口出现错误, 错误信息: {e}')
            return None, [{"role": "system", "content": f'{self.systemAiRole}'}]

    def get_local_deep_seek(self, content, message):
        """
        deepSeek
        :param content: 对话内容
        :param message: 消息列表
        :return:
        """
        op(f'[*]: 正在调用deepSeek本地对话接口... ...')
        if not self.localDeepSeekModelConfig:
            op(f'[-]: deepSeek本地模型未配置, 请检查相关配置!!!')
            return None, []
        message.append({"role": "user", "content": f'{content}'})
        data = {
            "model": self.localDeepSeekModelConfig.get('localDeepSeekModel'),
            'messages': message,
            'stream': False
        }
        try:
            resp = requests.post(url=self.localDeepSeekModelConfig.get('localDeepSeekApi'), json=data)
            json_data = resp.json()
            print(json_data)
            assistant_content = json_data['message']['content'].split('</think>')[-1].strip()
            return assistant_content, []
        except Exception as e:
            op(f'[-]: deepSeek本地对话接口出现错误, 错误信息: {e}')
            return None, []

    def get_ai(self, content):
        """
        处理优先级
        :param content:
        :return:
        """
        result = ''
        for i in range(1, 10):
            ai_module = self.aiPriority.get(i)
            if ai_module == 'localDeepSeek':
                result, self.deepSeekMessages = self.get_local_deep_seek(content, self.deepSeekMessages)
            if ai_module == 'siliconFlow':
                result, self.siliconFlowMessages = self.get_silicon_flow(content, self.siliconFlowMessages)
            if not result:
                continue
            else:
                break
        return result


if __name__ == '__main__':
    messages = []
    Ad = AiDialogue()
    reply = Ad.get_ai('你好')
    print(reply)
