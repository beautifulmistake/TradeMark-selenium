import time
from login.branddb_login import WipoLogin
from process_requests.process import WIPOSpider
from write_to_file.write_to_file import WriteToFile


class Scheduler(object):

    def __init__(self):
        """
        初始化方法
        """
        # 初始化初始页号
        self.page_num = 1
        # 初始化文件对象
        self.write_to_file = WriteToFile()
        # 初始化selenium抓取列表页对象
        self.w = WipoLogin()

    def run(self):
        # 记录抓取的页号,初始值为1
        # page_num = 1
        # 创建写入文件的对象
        # write_to_file = WriteToFile()
        # 实例化selenium抓取列表页的对象
        # w = WipoLogin()
        # 使用selenium打开WIPO 数据库
        # w.open()
        self.w.open()
        # 获取保存有Cookies的session对象
        # session_ = w.process_cookies(w.get_cookies())
        session_ = self.w.process_cookies(self.w.get_cookies())
        # 创建采集详情页的WipoSpider对象
        w_spider = WIPOSpider(session_)
        # 采集第一页的详情页链接,存入数据库
        self.w.get_detail_page()
        # 留有跳转页面的时间，不然捕获的元素的是前一页的，页面刷新完成后会报错
        # time.sleep(3)
        # 保存列表页的图片
        if self.w.is_element_exist():
            self.w.save_picture()
        # time.sleep(10)
        # 尝试采集详情页的信息,发起请求获取响应,一个响应的生成器
        responses = w_spider.request_from_redis()
        # 遍历获取响应的页面,解析获取数据,为保证数据存入的及时性，此次采用采集一页存储一页的策略
        datas = w_spider.get_data(responses)    # 此时的数据是有字典形式组成的列表
        # 将数据写入文件，文件名为当前页号
        self.write_to_file.save_data(self.page_num, datas)
        # 判断是否有下一页
        while self.w.next_successfully():
            # 改变page_num的值
            self.page_num += 1
            # 点击获取下一页的链接
            # w.get_next_page()
            self.w.get_one_page(self.page_num)
            # 留有跳转页面的时间，不然捕获的元素的是前一页的，页面刷新完成后会报错
            time.sleep(5)
            #######################################################################################
            # 此处代码冗余，考虑封装成一个函数
            # 采集当前页的详情页的链接，存入数据库
            self.w.get_detail_page()
            if self.w.is_element_exist():
                # 保存列表页的图片
                self.w.save_picture()
            # time.sleep(10)
            # 尝试采集详情页的信息,发起请求获取响应,一个响应的生成器
            responses = w_spider.request_from_redis()
            # 遍历获取响应的页面,解析获取数据,为保证数据存入的及时性，此次采用采集一页存储一页的策略
            datas_ = w_spider.get_data(responses)  # 此时的数据是有字典形式组成的列表
            # 将数据写入文件，文件名为当前页号
            self.write_to_file.save_data(self.page_num, datas_)
            #########################################################################################
            # 降低采集速度(后期考虑是否还有优化的空间，调试程序时，采集了八页）
            # time.sleep(15)


# 测试方法
# if __name__ == "__main__":
#     run()


































