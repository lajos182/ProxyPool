import redis
from proxypool.exceptions import PoolEmptyException
from proxypool.schemas.proxy import Proxy
from proxypool.setting import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, DB, REDIS_KEY, PROXY_SCORE_MAX, PROXY_SCORE_MIN, PROXY_SCORE_INIT
from random import choice
from typing import List
from loguru import logger
from proxypool.utils.proxy import is_valid_proxy, convert_proxy_or_proxies


REDIS_CLIENT_VERSION = redis.__version__
IS_REDIS_VERSION_2 = REDIS_CLIENT_VERSION.startswith('2.')


class RedisClient(object):
    """
    redis connection client of proxypool
    """
    
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=DB, **kwargs):
        """
        初始化
        :param host: Redis 地址
        :param port: Redis 端口
        :param password: Redis 密码
        """
        self.db = redis.StrictRedis(host=host, port=port, password=password, db=DB, decode_responses=True, **kwargs)
    
    def add(self, proxy: Proxy, score=PROXY_SCORE_INIT):
        """
        添加代理，设置分数为最高
        :param proxy: 代理
        :param score: 分数
        :return: 添加结果
        """
        if not is_valid_proxy(f'{proxy.host}:{proxy.port}'):
            logger.info(f'invalid proxy {proxy}, throw it')
            return
        if not self.exists(proxy):
            if IS_REDIS_VERSION_2:
                return self.db.zadd(REDIS_KEY, score, proxy.string())
            return self.db.zadd(REDIS_KEY, {proxy.string(): score})
    
    def random(self) -> Proxy:
        """
        随机获取有效代理，首先尝试获取最高分数代理，如果不存在，按照排名获取，否则异常
        :return: 随机代理
        """
        # try to get proxy with max score
        proxies = self.db.zrangebyscore(REDIS_KEY, PROXY_SCORE_MAX, PROXY_SCORE_MAX)
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else get proxy by rank
        proxies = self.db.zrevrange(REDIS_KEY, PROXY_SCORE_MIN, PROXY_SCORE_MAX)
        if len(proxies):
            return convert_proxy_or_proxies(choice(proxies))
        # else raise error
        raise PoolEmptyException
    
    def decrease(self, proxy: Proxy) -> int:
        """
        代理值减一分，小于最小值则删除
        :param proxy: 代理
        :return: 修改后的代理分数
        """
        score = self.db.zscore(REDIS_KEY, proxy.string())
        # current score is larger than PROXY_SCORE_MIN
        if score and score > PROXY_SCORE_MIN:
            logger.info(f'{proxy.string()} current score {score}, decrease 1')
            if IS_REDIS_VERSION_2:
                return self.db.zincrby(REDIS_KEY, proxy.string(), -1)
            return self.db.zincrby(REDIS_KEY, -1, proxy.string())
        # otherwise delete proxy
        else:
            logger.info(f'{proxy.string()} current score {score}, remove')
            return self.db.zrem(REDIS_KEY, proxy.string())
    
    def exists(self, proxy: Proxy) -> bool:
        """
        判断是否存在
        :param proxy: 代理
        :return: 是否存在
        """
        return not self.db.zscore(REDIS_KEY, proxy.string()) is None
    
    def max(self, proxy: Proxy) -> int:
        """
        将代理设置为 MAX_SCORE
        :param proxy: 代理
        :return: 设置结果
        """
        logger.info(f'{proxy.string()} is valid, set to {PROXY_SCORE_MAX}')
        if IS_REDIS_VERSION_2:
            return self.db.zadd(REDIS_KEY, PROXY_SCORE_MAX, proxy.string())
        return self.db.zadd(REDIS_KEY, {proxy.string(): PROXY_SCORE_MAX})
    
    def count(self) -> int:
        """
        获取数量
        :return: 数量
        """
        return self.db.zcard(REDIS_KEY)
    
    def all(self) -> List[Proxy]:
        """
        获取全部代理
        :return: 全部代理列表
        """
        return convert_proxy_or_proxies(self.db.zrangebyscore(REDIS_KEY, PROXY_SCORE_MIN, PROXY_SCORE_MAX))
    
    def batch(self, start, end) -> List[Proxy]:
        """
        get batch of proxies
        :param start: start index
        :param end: end index
        :return: list of proxies
        """
        return convert_proxy_or_proxies(self.db.zrevrange(REDIS_KEY, start, end - 1))


if __name__ == '__main__':
    conn = RedisClient()
    result = conn.random()
    print(result)
