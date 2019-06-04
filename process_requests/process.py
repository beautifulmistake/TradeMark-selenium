import re
import time
import redis
import requests
from lxml import etree
from proxy.db import REDISCLIENT


class WIPOSpider(object):

    def __init__(self, session_):
        """
        初始化方法,session_ 是selenium运行后保存Cookies的session对象
        """
        # 获取随机代理的数据库连接对象
        self.db = REDISCLIENT()
        # 获取初始化session对象
        self.s = session_
        # redis数据库连接对象，获取详情页的链接
        self.conn = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, decode_responses=True)
        self.page_key = "detail_page_url"  # 详情页队列的key
        # 此时的Cookies具有一定的失效性，所以请求设置成动态的
        self.headers = {
            'Referer': 'https://www.wipo.int/branddb/en/',  # 此值不需要变动
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
        }

    def get_proxy(self):
        """
        确保获取随机的，有效的代理
        :return: 代理
        """
        # 获取代理ip
        try:
            # 获取随机的代理
            proxy = self.db.random()
            # 顺便检查一下代理数量是否达到阈值
            self.db.check()
            # 增加添加代理前的检测环节，保证获取的代理有效
            if proxy:
                ip = proxy.split(":")[0]
                port = proxy.split(":")[1]
                if self.db.check_proxy(ip, port):
                    return proxy
                else:   # 回调自己重新获取代理
                    self.get_proxy()
        except requests.ConnectionError:
            return False

    def request_from_redis(self):
        """
        从redis数据库获取请求，获取Cookies，发起请求
        :return: 存放响应的生成器
        """
        while True:
            proxy = self.get_proxy()
            if proxy:
                proxies = {"http:": proxy}
                # 从redis数据库中获取详情页链接
                detail_page_url = self.conn.lpop("detail_page_url")
                # 判断是否存在
                if detail_page_url:
                    # 放入生成器当中
                    yield self.s.get(url=detail_page_url, headers=self.headers, proxies=proxies)
                else:
                    break

    def parse_response(self, response):
        """
        转换响应的页面为HTML，可使用xpath解析
        :param response:
        :return:
        """
        # try:
        if response.status_code == 200:
            # 测试时使用
            # print("查看获取的响应：", response.text)
            response.encoding = response.apparent_encoding
            return etree.HTML(response.text, etree.HTMLParser())
        else:
            print("响应的状态码不是200")
        # except:
        #     return "<process_requests--process>---解析页面产生异常"

    def get_data(self, responses):
        """
        接收转换后的响应，解析获取数据，由于各个国家的页面结构相同但字段不相同所以采取全字段采集然后zip处理为字典格式
        添加异常处理的方法
        :param responses:
        :return: 每一个详情页数据组成的列表
        """
        # try:
        # 创建全局的列表，用与存放打包后的每一条数据
        page_data = list()
        for response in responses:
            # 获取转换后的HTML
            html = self.parse_response(response)
            # 使用xpath解析页面获取字段
            # 创建存放title的列表
            title = list()
            # 创建存放标题内容的列表
            title_text = list()
            # 获取总的inid的数量
            inid_num = len(html.xpath('//div[@id="documentContent"]/div[@class="inid"]'))
            ###############################################################
            # 增加商标隶属国别字段,获取的是列表形式
            mark_country = html.xpath('//div[@id="topHeader"]/h4/text()')
            # 在title中设置 country 键
            title.append("country")
            # 在title_text 中增加国家名称
            title_text.append(re.sub('\W', ' ', " ".join(mark_country)))
            ################################################################
            # 获取mark的标题，第一个是固定的
            mark_title = html.xpath('//div[@id="documentContent"]/h2/text()|'
                                    '//div[@id="documentContent"]/h2/span/text()|'
                                    '//div[@id="documentContent"]/h2/div[child::text()]')
            title.append(re.sub('\W', ' ', " ".join(mark_title)).strip())
            mark_text = html.xpath('//div[@id="documentContent"]/div[1]/text()')
            title_text.append(" ".join(mark_text).strip())
            # 设置一个初始变量
            start = 1
            while start < inid_num:
                title_info = html.xpath('//div[@id="documentContent"]/div[@class="inid"][{}]/'
                                        'child::*/text()'.format(start))
                title.append(re.sub('\W', ' ', " ".join(title_info)).strip())
                title_info_text = html.xpath('//div[@id="documentContent"]/'
                                             'div[@class="text"][{}]/text()|'
                                             '//div[@id="documentContent"]/'
                                             'div[@class="text"][{}]/img/@src'.format(start + 1, start + 1))
                title_text.append(re.sub('\W', ' ', " ".join(title_info_text).strip()))
                start += 1
            # 获取最后一个标签的数据
            title_class = html.xpath('//div[@id="documentContent"]/div[@class="inid"][{}]/'
                                     'div[@class="inidText"]/text()'.format(start))
            title.append(re.sub('\W', ' ', " ".join(title_class)).strip())
            # 获取最后一个标签的内容，一般是 dd -- dl 的结构,这获取的是一个Element对象，使用re将文本提取出来
            title_class_text = html.xpath('//div[@id="documentContent"]/'
                                          'div[@class="text"][last()]/dl/child::*/text()')
            title_text.append(" ".join(title_class_text).strip())
            # 将最后的结果进行打包生成字典
            print("查看获取的title列表项：===========", title)
            print("查看获取的title_text列表项：===========", title_text)
            # 将字段打包成字典格式
            dict_ = dict(zip(title, title_text))
            # 添加到列表中存储
            page_data.append(dict_)
            # 两个请求之间间歇60秒,原先间歇15秒，结果帐号被封
            time.sleep(20)   # 暂时调整成一分钟请求少于10次/这会影响抓取的速率
        return page_data
        # except Exception:
        #     print("<process_requests--process>---解析目标字段产生异常")

    def load_pic(self, url):
        """
        如果有图片，再次发送请求下载图片方法
        考虑请求的频繁会被封，此次使用selenium右击保存
        :param url:
        :return:
        """
        pass
