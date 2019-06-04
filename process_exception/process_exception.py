import os


class ProcessException(object):

    def __init__(self):
        """
        初始化文件路径
        """
        pass

    def listdir(self, path):
        """
        传入路径，获取所有的文件名称
        :param path:
        :return:
        """
        # 创建一个列表
        list_name = list()
        for file in os.listdir(path):
            print(file)

    def is_exist(self, path):
        """
        根据路径判断文件是否存在
        这里需要使用文件名的绝对路径
        :param path:
        :return:
        """
        return os.path.exists(path)

    def delete_file(self, path):
        """
        根据路径将文件删除
        :param path:
        :return:
        """
        if os.path.exists(path):
            os.remove(path)
            print("成功删除文件：%s" % path)


# 测试代码
if __name__ == "__main__":
    # 创建对象
    p = ProcessException()
    # 调用方法
    p.listdir(r'D:\工作\商标数据\\')
