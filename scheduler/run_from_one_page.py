import time
from login.branddb_login import WipoLogin
from process_requests.process import WIPOSpider
from write_to_file.write_to_file import WriteToFile

"""
/*函数说明*/
此函数主要用于因意外情况导致程序中断时使用，根据记录抓取的页号，传入重新抓取的页号开始抓取
"""


def start_crawl(num):
    """
    接受参数，传入的页号此时为字符串类型，开始抓取
    :param num:
    :return:
    """
    # 将字符串转换为整型
    page_num = int(num)
    # 创建写入文件的对象
    write_to_file = WriteToFile()
    # 记录页号
    write_to_file.record_breakpoint(num)
    # 实例化selenium抓取列表页的对象
    w = WipoLogin()
    # 使用selenium打开WIPO 数据库
    w.open()
    # 获取保存有Cookies的session对象
    session_ = w.process_cookies(w.get_cookies())
    # 创建采集详情页的WipoSpider对象
    w_spider = WIPOSpider(session_)
    # 完成页面的跳转，跳转到指定的 page_num 页
    w.get_one_page(num)
    # 留有跳转页面的时间，不然捕获的元素的是前一页的，页面刷新完成后会报错
    time.sleep(3)
    # 获取详情页的链接
    w.get_detail_page()
    if w.is_element_exist():
        # 保存列表页的图片
        w.save_picture()
    # 尝试采集详情页的信息，发起请求获取响应,一个响应的生成器
    responses = w_spider.request_from_redis()
    # 遍历获取响应的页面,解析获取数据,为保证数据存入的及时性，此次采用采集一页存储一页的策略
    datas = w_spider.get_data(responses)  # 此时的数据是有字典形式组成的列表
    # 将数据写入文件，文件名为当前页号
    write_to_file.save_data(page_num, datas)
    # 判断是否有下一页
    while w.next_successfully():
        # 改变page_num的值
        page_num += 1
        # 更新页号
        write_to_file.record_breakpoint(page_num)
        # 点击获取下一页的链接
        # w.get_next_page()
        w.get_one_page(page_num)
        # 留有跳转页面的时间，不然捕获的元素的是前一页的，页面刷新完成后会报错
        time.sleep(5)
        # 采集当前页的详情页的链接，存入数据库
        w.get_detail_page()
        #######################################################################################
        # 此处代码冗余，考虑封装成一个函数
        # 保存列表页的图片
        if w.is_element_exist():
            # 增加这一步的目的是防止在没有图片的情况下操纵鼠标
            w.save_picture()
        # 尝试采集详情页的信息，发起请求获取响应,一个响应的生成器
        responses = w_spider.request_from_redis()
        # 遍历获取响应的页面,解析获取数据,为保证数据存入的及时性，此次采用采集一页存储一页的策略
        datas_ = w_spider.get_data(responses)  # 此时的数据是有字典形式组成的列表
        # 将数据写入文件，文件名为当前页号
        write_to_file.save_data(page_num, datas_)
        #########################################################################################
        # # 降低采集速度
        # time.sleep(15)


def scan():
    print("请输入要开始抓取的页号，输入exit退出")
    while True:
        page_num = input()
        if page_num == 'exit':
            break
        # 调用方法开始抓取
        start_crawl(page_num)


# 测试运行的方法
if __name__ == "__main__":
    scan()
