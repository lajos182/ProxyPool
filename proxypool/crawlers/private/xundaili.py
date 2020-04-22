import json
import requests
from proxypool.crawlers.base import BaseCrawler

class XundailiCrawler(BaseCrawler):
    """
    daili66 crawler, http://www.66ip.cn/1.html
    """
    url = 'http://www.xdaili.cn/ipagent/greatRecharge/getGreatIp?spiderId=da289b78fec24f19b392e04106253f2a&orderno=YZ20177140586mTTnd7&returnType=2&count=20'

    def parse(self, html):
        """
        parse html file to get proxies
        :return:
        """
        html = requests.get(url=self.url)
        if html:
            result = json.loads(html)
            proxies = result.get('RESULT')
            for proxy in proxies:
                yield proxy.get('ip') + ':' + proxy.get('port')


if __name__ == '__main__':
    crawler = XundailiCrawler()
    for proxy in crawler.crawl():
        print(proxy)
