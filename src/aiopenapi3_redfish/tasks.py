import asyncio
import logging


class AsyncTask:
    log = logging.getLogger("aiopenapi3_redfish.AsyncTask")

    async def produce(self):
        pass

    async def consume(self, *args, **kwargs):
        pass


class AsyncTaskSet:
    """
    inspiration https://pymotw.com/3/asyncio/synchronization.html#queues
    """

    log = logging.getLogger("aiopenapi3_redfish.AsyncTaskSet")

    def __init__(self, task, num_consumers=3):
        assert isinstance(task, AsyncTask), task
        self.task = task
        self.tasks: asyncio.Queue = asyncio.Queue(maxsize=num_consumers)

    async def producer(self):
        self.log.debug("producer: starting")
        async for i in self.task.produce():
            await self.tasks.put(i)
            self.log.debug(f"producer: added task {i} to the queue")

        # Add Stop signals / None entries in the queue
        self.log.debug("producer: adding stop signals to the queue")
        for i in range(self.tasks.maxsize):
            await self.tasks.put(None)
        self.log.debug("producer: waiting for queue to empty")
        await self.tasks.join()
        self.log.debug("producer: ending")

    async def consumer(self, n):
        self.log.debug(f"consumer {n}: starting")
        item = await self.tasks.get()
        while item is not None:
            self.log.debug(f"consumer {n}: has item {item}")
            try:
                async with asyncio.TaskGroup() as tg:
                    task = tg.create_task(self.task.consume(item))
            except* Exception as e:
                self.log.warning(f"Error processing %s" % item)
                self.log.exception(e)
            else:
                self.log.debug(f"consumer {n}: finished item")
            self.tasks.task_done()
            self.log.debug(f"consumer {n}: waiting for item")
            item = await self.tasks.get()

        # None is the signal to stop.
        self.tasks.task_done()
        self.log.debug(f"consumer {n}: ending")

    async def run(self):
        async with asyncio.TaskGroup() as tg:
            # Scheduled the consumer tasks.
            consumers = [tg.create_task(self.consumer(i)) for i in range(self.tasks.maxsize)]

            # Schedule the producer task.
            prod = tg.create_task(self.producer())
