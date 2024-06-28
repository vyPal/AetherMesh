import asyncio
class Message(asyncio.Event):
    def __init__(self):
        super().__init__()
        self._waiting_on_tsf = False
        self._tsf = asyncio.ThreadSafeFlag()
        self._data = None  # Message

    def clear(self):  # At least one task must call clear when scheduled
        super().clear()

    def __iter__(self):
        yield from self.wait()
        return self._data

    async def _waiter(self):  # Runs if 1st task is cancelled
        await self._tsf.wait()
        super().set()
        self._waiting_on_tsf = False

    async def wait(self):
        if self._waiting_on_tsf == False:
            self._waiting_on_tsf = True
            await asyncio.sleep(0)  # Ensure other tasks see updated flag
            try:
                await self._tsf.wait()
                super().set()
                self._waiting_on_tsf = False
            except asyncio.CancelledError:
                asyncio.create_task(self._waiter())
                raise  # Pass cancellation to calling code
        else:
            await super().wait()
        return self._data

    def set(self, data=None):  # Can be called from a hard ISR
        self._data = data
        super().set()
        self._tsf.set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self

    def value(self):
        return self._data