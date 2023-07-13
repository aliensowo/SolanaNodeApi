import asyncio

from solana_token_parser import SolanaTokenParser, parse_transaction


async def main():
    stp = SolanaTokenParser()
    await stp.create()
    trx = []
    for _ in range(100):
        resp = await stp.get_latest_signatures()

        if not resp:
            print("No new trxs... Sleeping...")
            await asyncio.sleep(5)
            continue

        transactions = await stp.client_pool.get_transactions([s["signature"] for s in resp])

        if not transactions:
            print("No new trxs... Sleeping...")
            await asyncio.sleep(5)
            continue

        for transaction in transactions:
            nft_url = await parse_transaction(transaction)
            if nft_url:
                print(nft_url)

        if resp:
            trx.extend(resp)
            print(len(resp))

    print(len(trx))


if __name__ == "__main__":
    asyncio.run(main())
