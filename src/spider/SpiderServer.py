import time

from src.spider.TXSpider import TXSpider
from src.util.constant import TIME_SPLIT


def start_tx_spider():
    tx = TXSpider()
    tx.log.logging.info("start tx spider success-----")
    while True:
        tx.main()
        time.sleep(TIME_SPLIT)

if __name__=='__main__':
    pass