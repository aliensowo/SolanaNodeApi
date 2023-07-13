import re

import base58
from solana_client_pool import SolanaClientPool


class SolanaTokenParser:
    def __init__(self):
        self.pool_size = 32
        self.token_program = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"

        self.DEFAULT_LIMIT = 100
        self.last_signature: str = None
        self.signatures: list[str] = None

        self.client_pool = SolanaClientPool(pool_size=self.pool_size)

    async def create(self):
        await self.client_pool.create()

    async def get_latest_signatures(self):
        print(self.last_signature)
        response = await self.client_pool.get_signatures_for_address(
            self.token_program, until=self.last_signature, limit=self.DEFAULT_LIMIT
        )
        if not response:
            return None
        # print(response)
        self.last_signature = response[0]["signature"]
        self.signatures = response
        return response


async def parse_transaction(transaction):
    if not transaction:
        return None
    if not transaction.get("meta"):
        return None
    for inner_instruction in transaction["meta"]["innerInstructions"]:
        for instruction in inner_instruction["instructions"]:
            if not instruction.get("data"):
                continue
            hex_data = base58.b58decode(instruction.get("data")).hex()
            for hex in hex_data.split("00000"):
                try:
                    cleaned_hex = bytes.fromhex(hex.strip("0")).decode("utf-8", errors="ignore")
                except ValueError:
                    continue
                if re.match(r"(?P<url>https?://[^\s]+)", cleaned_hex):
                    return re.search(r"(?P<url>https?://[^\s]+)", cleaned_hex).group("url")
