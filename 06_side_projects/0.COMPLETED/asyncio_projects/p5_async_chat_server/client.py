"""Small asyncio TCP chat client for P5.

Run server.py first, then open two terminals and run this client in both.
"""

from __future__ import annotations

import asyncio


async def read_from_server(reader: asyncio.StreamReader) -> None:
    """Print every line received from the chat server."""
    while data := await reader.readline():
        print(data.decode().rstrip())


async def write_to_server(writer: asyncio.StreamWriter) -> None:
    """Read terminal input without blocking the event loop and send it to the server."""
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, input, "> ")
        writer.write((line + "\n").encode())
        await writer.drain()
        if line.lower() in {"/quit", "quit", "exit"}:
            break


async def main(host: str = "127.0.0.1", port: int = 8888) -> None:
    """Connect to the chat server and run reader and writer tasks together."""
    reader, writer = await asyncio.open_connection(host, port)
    reader_task = asyncio.create_task(read_from_server(reader))
    try:
        await write_to_server(writer)
    finally:
        reader_task.cancel()
        await asyncio.gather(reader_task, return_exceptions=True)
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
