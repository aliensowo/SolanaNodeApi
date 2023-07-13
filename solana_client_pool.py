import asyncio
import itertools
import os
import random

import httpx
from httpx_socks import AsyncProxyTransport
from solana.exceptions import SolanaRpcException
from solana.rpc.async_api import AsyncClient
from solana.rpc.providers import async_http


def create_session() -> tuple[httpx.AsyncClient, str]:
    credentials = str(random.randint(10000, 0x7FFFFFFF)) + ":" + "password"
    tor_address = f'socks5://{credentials}@{os.environ.get("PROXY_HOST")}:{os.environ.get("PROXY_PORT")}'
    transport = AsyncProxyTransport.from_url(tor_address)
    client = httpx.AsyncClient(transport=transport, timeout=30)
    return client, tor_address


async def check_ip(client):
    res = await client.get("https://ifconfig.me/ip")
    return res.read().decode("utf-8")


class ProxyAsyncHTTPProvider(async_http.AsyncHTTPProvider):
    def __init__(self, endpoint=None, *args, **kwargs):
        super().__init__(endpoint)
        self.session, tor_address = create_session()
        self.tor_address = tor_address


class ProxyAsyncClient(AsyncClient):
    def __init__(self, endpoint=None, commitment=None, blockhash_cache=False, timeout=30, *args, **kwargs):
        super().__init__(commitment, blockhash_cache)
        self._provider = ProxyAsyncHTTPProvider(endpoint=endpoint, timeout=timeout)
        self.pair = {"endpoint": endpoint, "proxy": self._provider.tor_address}
        self.endpoint = endpoint
        self.timeout = timeout

    async def change_proxy(self):
        await asyncio.sleep(10)
        self._provider = ProxyAsyncHTTPProvider(endpoint=self.endpoint, timeout=self.timeout)
        self.pair = {"endpoint": self.endpoint, "proxy": self._provider.tor_address}
        # ip = await check_ip(self._provider.session)
        print(f"change session with client {self.pair}")


class SolanaClientPool:
    def __init__(self, pool_size=None):
        self.rpc_endpoints = [
            os.environ.get("MAIN_NET"),
            # os.environ.get("ANKR")
        ]
        self.pool_size = pool_size
        self.client_pool: list[ProxyAsyncClient] = None
        self.client_pool_cycle: itertools.cycle = None
        self.last_signature: str = None

    @property
    async def client(self) -> ProxyAsyncClient:
        # await asyncio.sleep(3)
        client = next(self.client_pool_cycle)
        # ip = await check_ip(client._provider.session)
        print(f"start working with client {client.pair}")
        return client

    async def create(self):
        self.client_pool = []
        check_dict = dict()
        for rpc_endpoint in self.rpc_endpoints:
            check_dict.update({rpc_endpoint: False})
            while True:
                await asyncio.sleep(3)
                client = ProxyAsyncClient(endpoint=rpc_endpoint)
                try:
                    await client.get_account_info("G34GvbBrz3X2ax2qsQKKWKWE2CkSnorDmbKuTkxfbRQ5")
                    self.client_pool.append(client)
                    # ip = await check_ip(client._provider.session)
                    print("success pair", client.pair)
                except SolanaRpcException:
                    print("bad pair")
                    continue
                if not check_dict.get(rpc_endpoint) and len(self.client_pool) % 1 == 0:
                    check_dict.update({rpc_endpoint: True})
                    break
        self.client_pool_cycle = itertools.cycle(self.client_pool)

    async def close(self):
        for client in self.client_pool:
            await client.close()
