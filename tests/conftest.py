from typing import AsyncIterator, Coroutine, AsyncContextManager, Callable
import asyncio
from pathlib import Path
from typing import Generator
from contextlib import asynccontextmanager

import pytest

from ovshell import testing


@pytest.fixture()
def ovshell(
    tmp_path: Path, event_loop
) -> Generator[testing.OpenVarioShellStub, None, None]:
    ovshell = testing.OpenVarioShellStub(str(tmp_path))
    yield ovshell
    ovshell.stub_teardown()
    event_loop.run_until_complete(asyncio.sleep(0))


@pytest.fixture()
def task_running() -> Callable[[Coroutine], AsyncContextManager[None]]:
    @asynccontextmanager
    async def runner(coro: Coroutine) -> AsyncIterator[None]:
        task = asyncio.create_task(coro)
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    return runner
