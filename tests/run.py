import random
import sys

import asyncio

sys.path.insert(0, '..')

# import os
# os.environ['PYTHONASYNCIODEBUG'] = '1'

import datetime

from asyncworkers.processor import BaseProcessor
from asyncworkers.workers import LocalWorker, RemoteWorker


class EchoWorker(LocalWorker):
    async def on_pack(self, pack):
        print('{}: kuku!'.format(datetime.datetime.now()))


class CrashWorker(LocalWorker):
    async def on_pack(self, pack):
        print('ready?')
        print(1 / 0)
        print('impossible message')


class SumWorker(LocalWorker):
    class Pack(LocalWorker.Pack):
        def __init__(self, *, a, b, delay):
            self.__dict__.update(vars())
            self.__dict__.pop('self', None)

    async def on_pack(self, pack):
        await asyncio.sleep(pack.delay)
        self.logger.info(
            '%s: %r+%r=%r (with delay %.03f s)',
            self,
            pack.a,
            pack.b,
            pack.a + pack.b,
            pack.delay,
        )


class RemoteSumWorker(RemoteWorker):
    class Pack(RemoteWorker.Pack):
        def __init__(self, *, a, b, delay=0):
            self.__dict__.update(vars())
            self.__dict__.pop('self', None)

    async def on_pack(self, pack):
        if pack.delay:
            await asyncio.sleep(pack.delay)
        self.logger.info(
            '%s: %r+%r=%r (with delay %.03f s)',
            self,
            pack.a,
            pack.b,
            pack.a + pack.b,
            pack.delay,
        )


class TestProcessor(BaseProcessor):
    async def setup(self):
        await super().setup()

        self.touch_every(self.new_worker(EchoWorker), seconds=1)
        self.touch_every(self.new_worker(CrashWorker), seconds=30)
        self.new_worker(RemoteSumWorker, n=5)

        sum_worker = self.new_worker(SumWorker, n=5)
        for i in range(10):
            for j in range(10):
                self.logger.info('%s: PUT: %s %s', self, i, j)
                await sum_worker.put(sum_worker.Pack(
                    a=i,
                    b=j,
                    delay=random.random(),
                ))
                await RemoteSumWorker.put(self.redis, RemoteSumWorker.Pack(
                    a=i,
                    b=j,
                ))


def test():
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)-8s [%(asctime)s] %(message)s',
    )
    test_processor = TestProcessor()
    test_processor.start()


if __name__ == '__main__':
    test()
