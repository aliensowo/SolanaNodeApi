import asyncio
import itertools
import os
import random

import httpx
from dotenv import load_dotenv
from solana.rpc.api import MemcmpOpt
from solana.rpc.async_api import AsyncClient
from solana.rpc.providers import async_http

load_dotenv()

project_serum = os.environ.get("PROJECT_SERUM")
main_net = os.environ.get("MAIN_NET")


def create_tor_session() -> httpx.AsyncClient:
    creds = str(random.randint(10000, 0x7FFFFFFF)) + ":" + "password"
    tor_addr = f"socks5://{creds}@{os.environ.get('PROXY_HOST')}:9050"

    proxies = {
        "http://": tor_addr,
        "https://": tor_addr,
    }

    client = httpx.AsyncClient(proxies=proxies, timeout=5)
    return client


class ProxiedAsyncHTTPProvider(async_http.AsyncHTTPProvider):
    def __init__(self, endpoint=None, timeout=10, *args, **kwargs):
        super().__init__(endpoint)
        self.session = httpx.AsyncClient(timeout=60)


class ProxiedAsyncClient(AsyncClient):
    def __init__(self, endpoint=None, commitment=None, blockhash_cache=False, timeout=10, *args, **kwargs):
        super().__init__(commitment, blockhash_cache)
        self._provider = ProxiedAsyncHTTPProvider(endpoint, timeout=timeout)


class SolanaClientPool:
    def __init__(self, pool_size):
        self.rpc_endpoint = project_serum
        self.pool_size = pool_size
        self.client_pool: list[AsyncClient] = None
        self.client_pool_cycle: itertools.cycle = None
        self.last_signature: str = None

    async def create(self):
        self.client_pool = [ProxiedAsyncClient(self.rpc_endpoint) for _ in range(self.pool_size)]
        self.client_pool_cycle = itertools.cycle(self.client_pool)

    async def close(self):
        for client in self.client_pool:
            await client.close()

    async def get_signatures_for_address(self, address, before: str = None, until: str = None, limit: int = None):
        client: AsyncClient = next(self.client_pool_cycle)
        response = await client.get_signatures_for_address(address, before=before, until=until, limit=limit)
        return response["result"]

    async def get_transactions(self, signatures: list[str]):
        tasks = []
        for signature in signatures:
            task = asyncio.ensure_future(self.get_transaction(signature))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses

    async def get_transaction(self, signature: str):
        client: AsyncClient = next(self.client_pool_cycle)
        # print("-----Before await-----")
        response = await client.get_transaction(signature)
        # print("-----After await-----")

        # print(response["id"])
        return response["result"]

    async def get_nft_metadata(self, address: str):
        token_metadata_program = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
        client: AsyncClient = next(self.client_pool_cycle)
        memcmp_opts = [MemcmpOpt(offset=33, bytes=address)]
        response = await client.get_program_accounts(token_metadata_program, memcmp_opts=memcmp_opts)
        return response
