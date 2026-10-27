"""P5: Async TCP chat server.

Start the server, then connect multiple clients with telnet, netcat, or the
included client.py. Every connected client is handled by its own coroutine.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class Client:
    """Represents one connected chat client."""

    name: str
    writer: asyncio.StreamWriter


class ChatRoom:
    """Tracks connected clients and broadcasts messages to them."""

    def __init__(self) -> None:
        """Create an empty chat room protected by an async lock."""
        self._clients: dict[asyncio.StreamWriter, Client] = {}
        self._lock = asyncio.Lock()

    async def join(self, client: Client) -> None:
        """Add a client and announce that they joined."""
        async with self._lock:
            self._clients[client.writer] = client
        await self.broadcast("server", f"{client.name} joined")

    async def leave(self, writer: asyncio.StreamWriter) -> None:
        """Remove a client and announce that they left."""
        async with self._lock:
            client = self._clients.pop(writer, None)
        if client:
            await self.broadcast("server", f"{client.name} left")

    async def broadcast(self, sender: str, message: str) -> None:
        """Send a message to every currently connected client."""
        async with self._lock:
            clients = list(self._clients.values())
        line = f"[{sender}] {message}\n".encode()
        disconnected: list[asyncio.StreamWriter] = []
        for client in clients:
            try:
                client.writer.write(line)
                await client.writer.drain()
            except ConnectionError:
                disconnected.append(client.writer)
        for writer in disconnected:
            await self.leave(writer)


async def handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, room: ChatRoom
) -> None:
    """Handle one connected TCP client until it disconnects."""
    writer.write(b"Welcome. Type your name: ")
    await writer.drain()
    raw_name = await reader.readline()
    name = raw_name.decode().strip() or "anonymous"
    client = Client(name=name, writer=writer)
    await room.join(client)

    try:
        while data := await reader.readline():
            message = data.decode().strip()
            if message.lower() in {"/quit", "quit", "exit"}:
                break
            await room.broadcast(name, message)
    finally:
        await room.leave(writer)
        writer.close()
        await writer.wait_closed()


async def main(host: str = "127.0.0.1", port: int = 8888) -> None:
    """Start the chat server and serve clients forever."""
    room = ChatRoom()
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, room), host, port
    )
    addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"chat server listening on {addresses}")
    print("connect with: python client.py")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nserver stopped")
