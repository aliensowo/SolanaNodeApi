import os
import httpx
import asyncio
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import BackgroundTasks, FastAPI, status
from solana_client_pool import SolanaClientPool
from solana.exceptions import SolanaRpcException

app = FastAPI()

solana_pool: SolanaClientPool
http_client: httpx.AsyncClient

load_dotenv()
ogre_magi = os.environ.get("OGRE_MAGI")


@app.on_event("startup")
async def startup_event():
    global http_client, solana_pool
    solana_pool = SolanaClientPool()
    await solana_pool.create()
    http_client = httpx.AsyncClient(timeout=60)


@app.on_event("shutdown")
async def shutdown_event():
    global http_client, solana_pool
    await solana_pool.close()
    await http_client.aclose()


@app.get("/get-balance/{wallet_address}")
async def get_balance(wallet_address: str):
    """
    {"balance":21678898314}
    :param wallet_address:
    :return:
    """
    global solana_pool
    solana_client = await solana_pool.client
    response = await solana_client.get_balance(wallet_address)
    return {"balance": response["result"]["value"]}


@app.get("/transactions/{wallet_address}/{limit}")
async def parse_signatures(wallet_address: str, limit: int, *, background_tasks: BackgroundTasks):
    global solana_pool
    solana_client = await solana_pool.client
    while True:
        try:
            signatures = await solana_client.get_signatures_for_address(wallet_address, limit=limit)
            break
        except SolanaRpcException:
            await solana_client.change_proxy()
    signatures_list = [signature["signature"] for signature in signatures["result"]]
    transactions = await prepare_transactions(signatures_list, "end")
    for transaction in transactions:
        background_tasks.add_task(
            send_signatures, wallet_address, transaction
        )
    return JSONResponse(status_code=status.HTTP_200_OK)

# utils


async def get_transactions(signatures_list: list):  # asynchronous
    global solana_pool
    solana_client = await solana_pool.client
    tasks = []
    for i in range(0, len(signatures_list), 10):
        while True:
            try:
                for el in signatures_list[i: i + 10]:
                    task = asyncio.ensure_future(solana_client.get_transaction(el, encoding="jsonParsed"))
                    tasks.append(task)
                result = await asyncio.gather(*tasks)
                tasks = []
                break
            except SolanaRpcException:
                await solana_client.change_proxy()
                # solana_client = await solana_pool.client
                tasks = []
        # for signature_result in result:
        yield [signature_result["result"] for signature_result in result]


async def prepare_transactions(signatures_list: list, direction: str):
    global http_client
    result = []
    transaction_chunk = get_transactions(signatures_list)
    async for transaction_list in transaction_chunk:
        if direction == "start":
            transaction_list.reverse()
        result.extend(transaction_list)
    return result


async def send_signatures(wallet_address: str, transaction: dict):
    results = []
    for instruction in transaction["transaction"]["message"]["instructions"]:
        try:
            if instruction["parsed"]["type"].lower().find("transfer") == 0:
                if wallet_address in (
                        instruction["parsed"]["info"]["destination"], instruction["parsed"]["info"]["source"]
                ):
                    element = {
                        "block_time": transaction["blockTime"],
                        "fee": transaction["meta"]["fee"],
                        "slot": transaction["slot"],
                        "wallet_address_from": instruction["parsed"]["info"]["destination"],
                        "wallet_address_to": instruction["parsed"]["info"]["source"],
                        "amount": instruction["parsed"]["info"]["lamports"],
                        "coin_name": instruction["parsed"]["info"].get("mint", "sol"),
                        "signature": transaction["transaction"]["signatures"][0]
                    }
                    if instruction["parsed"]["info"].get("lamports"):
                        element["amount"] = instruction["parsed"]["info"]["lamports"]
                    else:
                        element["amount"] = instruction["parsed"]["info"]["tokenAmount"]["amount"]
                    results.append(element)
        except KeyError:
            pass
        except TypeError:
            # TODO: logs needed
            # example:
            # {'parsed': 'Donation war efforts', 'program': 'spl-memo', 'programId': 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'}
            pass
    for inner in transaction["meta"]["innerInstructions"]:
        try:
            if wallet_address in (
                    inner["instructions"][0]["parsed"]["info"]["destination"],
                    inner["instructions"][0]["parsed"]["info"]["source"]
            ):
                element = {
                    "block_time": transaction["blockTime"],
                    "fee": transaction["meta"]["fee"],
                    "slot": transaction["slot"],
                    "wallet_address_from": inner["instructions"][0]["parsed"]["info"]["destination"],
                    "wallet_address_to": inner["instructions"][0]["parsed"]["info"]["source"],
                    "amount": inner["instructions"][0]["parsed"]["info"]["lamports"],
                    "coin_name": inner["instructions"][0]["parsed"]["info"].get("mint", "sol"),
                    "signature": transaction["transaction"]["signatures"][0]
                }
                if inner["instructions"][0]["parsed"]["info"].get("lamports"):
                    element["amount"] = inner["instructions"][0]["parsed"]["info"]["lamports"]
                else:
                    element["amount"] = inner["instructions"][0]["parsed"]["info"]["tokenAmount"]["amount"]
                results.append(element)
        except KeyError:
            pass
    for transaction in results:
        try:
            await http_client.post(
                f"{ogre_magi}/add-transaction/sol/{wallet_address}", json=transaction, timeout=60
            )
            # if response.status_code != 422:
            #     print(f'unprocessable transaction {transaction}')
        except httpx.ReadTimeout:
            print("ogre maggi timeout error 5 seconds sleep and retry")
            await asyncio.sleep(5)
