import os
import yaml


def get_config_path():
    """
    返回配置文件夹路径
    :return:
    """
    current_path = os.path.dirname(__file__)
    if '\\' in current_path:
        current_list_path = current_path.split('\\')
        config_path = '/'.join(current_list_path) + '/config'
        return config_path
    else:
        return current_path


def get_config_data():
    """
    返回配置文件数据（YAML格式）
    :return:
    """
    current_path = get_config_path()
    config_data = yaml.load(open(current_path + '/Config.yaml', mode='r', encoding='UTF-8'), yaml.Loader)
    return config_data
