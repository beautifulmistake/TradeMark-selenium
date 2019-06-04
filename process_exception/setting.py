"""
异常处理模块主要负责三方面的功能：
1、判断代理库是否有代理，有删除（这一步如果从中断到重启时间较短的话，可以不做此步）
2、判断数据库中是否有数据
3、获取中断的页号，判断是否有相应页号的文件，有，删除
"""

# Redis Host
# REDIS_HOST = '127.0.0.1'
# # redis port
# REDIS_PORT = 6379   # 注意端口为整数
# # redis password
# REDIS_PASSWORD = None   # 如果有，在此配置，为字符串格式
# # redis db
# REDIS_DB = 0
# # 代理的键
# PROXY_KEY = "wipo"
# # 详情页的链接
# DETAIL_PAGE_KEY = "detail_page_url"
# 以上的配置信息有些冗余
# 文件存放的路径
# FILE_PATH = r'D:\工作\商标数据\\'
