import codecs
import json
import os
import time


class WriteToFile(object):
    def __init__(self):
        # 初始化数据保存路径,需要传入page_num拼接完整的文件名称
        self.file_name = r'D:\工作\商标数据\\'
        # 初始化图片保存的路径，需要传入商标序列号和商标名称组成文件名称
        # 此次暂时不采用这个方案，这个为备用方案
        self.pic_name = r'D:\工作\商标图片\\'

    def save_data(self, page_num, datas):
        """
        传入页号，打包成字典格式的数据(此时是列表形式），逐条将数据写入文件
        :param page_num: 页号
        :param datas: 字典格式的数据
        :return: 写入完成page_num页数据
        """
        # 拼接出完整的路径
        file_name = self.file_name + str(page_num) + '.json'
        # 使用codecs模块，避免由于不是二进制存储带来的不能使用seek函数问题
        fw = codecs.open(file_name, 'a+', encoding='utf-8')
        fw.write('[')
        for data in datas:
            # 将数据转换为json
            data = json.dumps(data, ensure_ascii=False) + ",\n"
            # 将每条数据写入文件
            fw.write(data)
        fw.seek(-2, os.SEEK_END)
        fw.truncate()
        fw.write(']')
        fw.close()
        # 程序暂停2秒，防止下一页请求失败导致，已经采集的数据未来的及写入文件
        time.sleep(2)

    def save_pic(self, data):
        """
        起初的方案是再次发送请求然后下载图片，将图片以二进制写入文件之中保存
        现在在selenium请求获取列表页的时候，图片加载完毕之后就先采集
        故此次这个方法先保留
        :param data:
        :return:
        """
        pass

    def record_breakpoint(self, num):
        """
        将获取的数字转换为字符串写入文件
        :param num:
        :return:
        """
        with open(r'./breakpoint.txt', 'w+', encoding='utf-8') as f:
            if isinstance(num, str):
                f.write(num)
            f.write(str(num))

    def read_breakpoint(self):
        """
        根据文件名读取断点
        :return: 记录的页号（返回的为字符串形式）
        """
        with open(r'./breakpoint.txt', 'r', encoding='utf-8') as fr:
            return fr.readlines()[-1]

    def trans_num_to_path(self, num):
        """
        转换获取的页号为绝对路径
        :param num:
        :return: 路径
        """
        return self.file_name + num + ".json"
