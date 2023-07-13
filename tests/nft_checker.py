import asyncio
import os
import random

import httpx
from dotenv import load_dotenv

load_dotenv()

"""
requests example:

response = requests.get(
    "https://api.theblockchainapi.com/v1/solana/nft",
    params={
        'mint_address':
            'DPc4S4XPEAfmEoSJ4Fw74dEiz7pgnttqQu5HRypHhvYS',
        'network': 'mainnet-beta'
    },
    headers={
        'APISecretKey': 'z5t1l52HBqGoijI',
        'APIKeyId': 'sXkPqMm9DPXTUOl'
    })
"""


def create_tor_session(headers=None) -> httpx.AsyncClient:
    creds = str(random.randint(10000, 0x7FFFFFFF)) + ":" + "password"
    tor_addr = f"socks5://{creds}@{os.environ.get('PROXY_HOST')}:9050"

    proxies = {
        "http://": tor_addr,
        "https://": tor_addr,
    }

    client = httpx.AsyncClient(proxies=proxies, timeout=5, headers=headers)
    return client


class NFTChecker:
    def __init__(self):
        self.nft_api_url = os.environ.get("NFT_API_URL")
        self.params_template = {"mint_address": "0", "network": "mainnet-beta"}
        self.headers = {"APISecretKey": "z5t1l52HBqGoijI", "APIKeyId": "sXkPqMm9DPXTUOl"}
        self.session = httpx.AsyncClient(headers=self.headers)

    async def close(self):
        await self.session.aclose()

    async def get_nft(self, mint_address: str):
        params = self.params_template
        params["mint_address"] = mint_address
        response = await self.session.get(self.nft_api_url, params=params)
        if response.status_code == 429:
            self.session = create_tor_session(headers=self.headers)
        return response


async def main():
    nft_checker = NFTChecker()
    tasks = []
    for _ in range(100):
        task = asyncio.ensure_future(nft_checker.get_nft("FKMutKVoG4JVivRXeqfV4jGRzu1GP38UZgsfr6RfDLgn"))
        tasks.append(task)
    responses: list[httpx.Response] = await asyncio.gather(*tasks)
    ok = 0
    bad = 0
    for resp in responses:
        if resp.status_code == 200:
            ok += 1
        else:
            bad += 1
    print(responses)
    print(ok, bad)


if __name__ == "__main__":
    asyncio.run(main())
