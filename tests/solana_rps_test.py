import asyncio
import json
from queue import Queue
from time import time

from solana.rpc.async_api import AsyncClient
from solana_client_pool import SolanaClientPool

test_signature = "5JnpyCN4VLyEsccuZ3qAAPY8UEiWZjCco2uTLtPbLajNerVgaJLytwpRPKkwbkdFXzaNWYgUbeZCMnxcpqVUfdiG"
test_signatures = [test_signature] * 10


main_net = "https://api.mainnet-beta.solana.com"
project_serum = "https://solana-api.projectserum.com"

solana_client = AsyncClient(project_serum)
count_queue = Queue()


async def get_transaction(signature):
    response = await solana_client.get_transaction(signature)
    print(response["id"])
    return response


async def main():
    client_pool = SolanaClientPool(32)
    print("Creating client pool...")
    await client_pool.create()
    print("Client pool created...")
    # responses = await client_pool.get_transactions(test_signatures)
    # response = await client_pool.get_signatures_for_address("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", until="4aNjC9o5aYMv5cTJoB7LJr52GPKUmSf34Nz8bAwAuN4WvxmSmhv3vzakANkfBaW8wTv64p8xmbGcayy6D3DD5Awc")
    # response = await client_pool.get_nft_metadata("FKMutKVoG4JVivRXeqfV4jGRzu1GP38UZgsfr6RfDLgn")
    response = await client_pool.get_transaction(
        "4Yt1qV2zAPUY9ro3BFE9Eg4CkJkb514AefZSuMxjK3f2oFezifHLSj5HXanJQBhqVkA1YwjQ4DDLeY4vSnKvLUT9"
    )

    print(json.dumps(response, indent=4))
    # print(len(response))
    await client_pool.close()


if __name__ == "__main__":
    st_time = time()
    asyncio.run(main())
    print(f"{time() - st_time} seconds elapsed.")
