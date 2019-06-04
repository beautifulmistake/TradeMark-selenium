import pyautogui
import redis
import requests
from selenium.common.exceptions import TimeoutException  # ,StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
from requests.cookies import RequestsCookieJar
# from process_exception.process_exception import ProcessException
from proxy.db import REDISCLIENT
from write_to_file.write_to_file import WriteToFile
# import sys
# sys.path.append("D:\project\markSpider")
# from scheduler import run_from_one_page


class WipoLogin(object):

    def __init__(self):
        # 初始化Redis连接对象，存放代理的接口
        self.db = REDISCLIENT()
        # 初始化获取Redis的链接,将要采集的链接存入redis的1号库
        self.db_ = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)
        # 初始化一个文件对象
        self.file = WriteToFile()
        # 这是进入Global Brand Database的接口，从这儿开始使用selenium模拟浏览器行为开始进入
        self.start_url = 'https://www.wipo.int/tools/en/gsearch.html?' \
                         'cx=016458537594905406506%3Ahmturfwvzzq&cof=FORID%3A11&q='
        # 这是选择图片的xpath,获取的是一个列表集合
        self.pic_xpath = '//table[@id="gridForsearch_pane"]/tbody/tr/td/img'
        # 获取一个有效的代理
        # self.proxy = self.get_proxy()
        self.chrome_options = Options()
        # 设置无头浏览器
        # self.chrome_options.add_argument('--headless')
        # 添加代理，目前还未解决掉代理问题，代理的时效性
        # self.chrome_options.add_argument('--proxy-server=http://{}'.format(self.proxy))
        # 初始化浏览器对象
        # self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.browser = webdriver.Chrome()
        # 设置浏览器大小：全屏显示
        self.browser.maximize_window()
        # 等待页面加载完成
        self.wait = WebDriverWait(self.browser, 60)

    def load_js(self):
        """
        辅助性的方法：
        执行js修改浏览器属性
        :return:
        """
        self.browser.execute_script("Object.defineProperties(navigator,{webdriver:{get:() => false}})")
        print("执行修改浏览属性脚本")

    def get_proxy(self):
        """
        辅助性方法：
        从redis中获取随机的代理
        :return: 有效可用的代理
        """
        try:
            # 获取随机的代理
            proxy = self.db.random()
            # 顺便检查一下代理数量是否达到阈值
            self.db.check()
            if proxy:
                ip = proxy.split(":")[0]
                port = proxy.split(":")[1]
                if self.db.check_proxy(ip, port):
                    print("给selenium设置代理：", proxy)
                    return proxy
                else:   # 回调自己重新获取代理
                    print("回调自己重新获取代理")
                    self.get_proxy()
        except requests.ConnectionError:
            # 出现连接错误
            return False

    def open(self):
        """
        打开网页获取Global Brand Database
        :return:
        """
        try:
            # 先修改浏览器的属性
            self.load_js()
            # 获取网页
            self.browser.get(self.start_url)
            # 查看获取的HTML
            # print(self.browser.page_source)
            # 定位Global Brand Database a 标签
            skip_page = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="box"]/ul/li[2]/a')))
            skip_page.click()
            # print(self.browser.page_source)
        # 打开网页超时后重新打开
        except TimeoutException:
            self.open()

    def is_element_exist(self):
        """
        辅助性方法：
        判断是否有图片,此次先尝试xpath选择器选择所有的标签
        :return: 返回判断结果(试验有多个的时候返回值）
        """
        # 初始方案，硬性等待元素加载，不灵活
        s = self.browser.find_elements_by_xpath(xpath=self.pic_xpath)
        # 修改方案：显性的等待页面元素加载完成
        # s = self.wait.until(EC.presence_of_element_located((By.XPATH, self.pic_xpath)))
        if len(s) == 0:
            print("包含图片的元素并未找到：%s" % self.pic_xpath)
            return False
        else:
            return True

    def save_picture(self):
        """
        使用selenium模拟鼠标键盘操作实现图片的保存
        重点在于处理保存路径的方法，怎么按页号存储
        此处会有一个问题：当保存时，会有弹窗出现确认保存信息，此时需要手动点击确认，比较繁琐，引入第三方工具来实现此功能
        :return:
        """
        # 此处增加捕获 selenium.common.exceptions.StaleElementReferenceException 这个异常
        # try:
        # 禁用故障安全功能，当鼠标快速移动到左上角时会引发故障安全功能
        pyautogui.FAILSAFE = False
        # 判断该列表页是否有图片
        if self.is_element_exist():
            # try:
            # 获取页面所有的img标签
            elements = self.browser.find_elements_by_xpath(self.pic_xpath)
            # elements = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, self.pic_xpath)))
            # 遍历每一个图片，点击保存
            for element in elements:
                try:
                    action = ActionChains(self.browser).move_to_element(element)
                    # 点击图片
                    action.context_click(element)
                    action.perform()
                    # 发送键盘按键，根据不同的网页，
                    # 右键之后按对应次数向下键，
                    # 找到图片另存为菜单
                    pyautogui.typewrite(['down', 'down', 'enter', 'enter'])
                    # 图片保存之后，暂停3秒后点击回车
                    time.sleep(2)
                    # 点击保存
                    pyautogui.typewrite(['enter'])
                except pyautogui.FailSafeException:
                    # 出现这个异常的时候其实浏览器已经错乱
                    print("保存图片时引发故障安全功能")
            return "这一页图片保存成功"
            # except Exception as e:
            #     print("图片保存过程中出现异常")
        # except StaleElementReferenceException:
        #     # 捕捉到这个错误后是由于页面找到元素后又刷新导致，重新定位元素
        #     print("捕获异常%s" % StaleElementReferenceException, "尝试重新调用自身处理")
        #     # 创建异常处理对象
        #     e = ProcessException()
        #     # self.save_picture()     # 先尝试重新调用自身函数试试(此时出现的情况是页面重新跳转到第一页，故调用自身方法不能解决问题）
        #     # 以防并未加载完成第一页，首先刷新页面
        #     self.browser.refresh()
        #     # 先判断详情页数据库是否有链接，有，先删除(耦合性较强，后期考虑将self.db_写成配置文件）
        #     self.db_.delete("detail_page_url")  # 键存在就删除，不存在的 key 会被忽略
        #     # 先判断代理库是否有，有，先删除（其实相隔时间较短时可以不清除代理）
        #     self.db.delete_all()
        #     # 获取已经抓取到的页号,为字符串类型
        #     num = self.file.read_breakpoint()
        #     # 获取完整路径
        #     file_path = self.file.trans_num_to_path(num)
        #     # 先判断是否有相应页号的文件，有，删除
        #     if e.is_exist(file_path):
        #         # 删除文件
        #         e.delete_file(file_path)
        #     # 传入页号，从指定页开始抓取
        #     run_from_one_page.start_crawl(num)

    def get_one_page(self, num):
        """
        当程序意外中断的时候需要调用此方法：
        根据页号完成跳转到指定页面,失败后回掉，重新进入翻页
        :param num:
        :return:
        """
        try:
            # 获取跳转页号的输入框,等待加载成功
            page_input = self.wait.until(EC.presence_of_element_located((By.ID, "skipValue1")))
            # 清空翻页输入框
            page_input.clear()
            # 传入页号
            page_input.send_keys(num)
            # 传入回车并搜索
            page_input.send_keys(Keys.ENTER)
            # 等待页面详情页链接加载完成
            self.wait.until(EC.presence_of_element_located((
                By.XPATH, '//table[@id="gridForsearch_pane"]/tbody/tr[@role="row"]')))
            # 等待页面图片加载完成
            self.wait.until(EC.presence_of_element_located((By.XPATH, self.pic_xpath)))
            # 此处需要增加一个条件判断语句，根据页号来判断是否已经完成页面的跳转
            # 此处需要根据 input 的 size 属性值来判断 注意获取的是字符串
        # 捕捉超时后重新进入翻页
        except TimeoutException:
            self.get_one_page(num)

    def get_cookies(self):
        """
        获取此页的Cookies，详情页的请求需要携带Cookies
        :return:
        """
        print("查看获取的原始Cookies：", self.browser.get_cookies(), type(self.browser.get_cookies()))
        return self.browser.get_cookies()

    def save_cookie(self, cookies):
        """
        可以选择将数据写入文件或者保存到数据库
        说明：scrapy中支持将selenium获取的原生cookies携带发起请求获取响应，但使用requests时，需要将列表套字典形式转换为
        字典的形式或者cookieJar的形式
        :param cookies:
        :return:
        """
        # 获取的cookies是一个列表套字典形式的数据结构：[ { }, { } ]
        # dict = {}
        # print("查看传递的原始Cookies：", cookies, "查看他的类型：", type(cookies))
        # for cookie in cookies:
        #     dict[cookie['name']] = cookie['value']
        # return dict
        pass

    def process_cookies(self, cookies):
        """
        处理Cookies
        创建session对象，将Cookies保存在session之中
        :param cookies:
        :return: 保存Cookies的session对象，用于后续的请求，或许页面的请求都需要使用这个对象来完成
        """
        # 创建一个session对象
        s = requests.Session()
        # 创建cookieJar对象
        jar = RequestsCookieJar()
        for cookie in cookies:
            # 判断JSESSIONID 将域名为 /branddb 的 进行添加,此域名下的才能请求到数据
            if cookie['name'] == 'JSESSIONID' and cookie['path'] == '/':
                print("此cookie暂时不做处理*********")
            else:
                jar.set(cookie['name'], cookie['value'])
        s.cookies.update(jar)
        print("查看获取的jar对象：", jar)
        # 将保存Cookies的session对象返回
        return s

    def next_successfully(self):
        """
        判断是否有下一页，此处出现一个问题，使用下标进行选择时，不知为何，会一直在第一页和第二页之间来回跳转
        现在更改为使用属性来获取，可以实现循环页数的采集详情页的链接
        :return:
        """
        try:
            return bool(WebDriverWait(self.browser, 40).until(
                EC.presence_of_element_located((
                    By.XPATH, '//div[@id="results"]/div[1]/div[2]/div[3]/a[@aria-label="next page"]'))))
        except TimeoutException:
            return False

    def get_next_page(self):
        """
        判断是否有下一页的请求，此处同样需要更改为使用属性来获取对应的a标签
        失败后重新翻页的逻辑需要再次确认，是否需要刷新页面，然后读取断点，传入指定页号
        :return:
        """
        try:
            # 获取下一页的点击按钮
            skip_next_page = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, '//div[@id="results"]/div[1]/div[2]/div[3]/a[@aria-label="next page"]')))
            skip_next_page.click()
            # 等待页面详情页链接加载完成
            self.wait.until(EC.presence_of_element_located((
                By.XPATH, '//table[@id="gridForsearch_pane"]/tbody/tr[@role="row"]')))
            # 等待页面图片加载完成
            self.wait.until(EC.presence_of_element_located((By.XPATH, self.pic_xpath)))
        # 翻页超时，重新翻页
        except TimeoutException:
            self.get_next_page()

    def push_to_redis(self, url):
        """
        将完整的详情页链接存入redis之中,之前是将cookie页拼接存入的，现在不保存
        :param url:
        :return:
        """
        # return self.db_.rpush("detail_page_url", url + "ÿ" + cookie)
        return self.db_.rpush("detail_page_url", url)   # 后期将其定义成初始化变量

    def delete_from_redis(self, key):
        """
        由于Cookies具有失效性，当程序意外中断时，已经存储在REDIS中的详情页链接已经失去意义，需要将其从数据库中移除
        :param key:
        :return:
        """
        if self.db_.exists("detail_page_url"):
            # 存在，将其删除
            self.db_.delete("detail_page_url")

    def get_detail_page(self):
        """
        获取每一分页上的关于详情页的链接
        在此处也不知道什么原因使用text方法并不能获取文本值，所以该使用获取title属性值的方式
        :return:
        """
        # detail_page_urls = self.browser.find_elements_by_xpath(
        #     '//table[@id="gridForsearch_pane"]/tbody/tr[@role="row"]')
        # 修改为等待页面加载完成
        detail_page_urls = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//table[@id="gridForsearch_pane"]/tbody/tr[@role="row"]')))
        # 遍历获取每一个对象
        for detail_page_url in detail_page_urls:
            # 获取title的属性值，title属性值就是需要的详情页链接
            detail_page = detail_page_url.find_element_by_xpath("./td[5]").get_attribute('title')
            # 判断是否为空，为空则抛弃
            if detail_page:
                detail = "https://www.wipo.int/branddb" + detail_page[2:]
                print("查看详情页的链接", detail)
                # 存入redis
                # self.push_to_redis(detail, json.dumps(cookie))
                self.push_to_redis(detail)

    def run(self):
        """
       一个测试程序运行的方法
        :return:
        """
        # 第一步先获取Global Brand Database
        self.open()
        # 采集第一页的详情页链接
        self.get_detail_page()
        # 判断本页当中是否有下一页
        while self.next_successfully():
            # 点击获取下一页
            self.get_next_page()
            # 在此处判断增加对消息队列的判断，做到同一页的采集使用同一个Cookies
            # 采集当前页的详情页链接
            self.get_detail_page()
            time.sleep(50)


if __name__ == "__main__":
    w = WipoLogin()
    w.run()
