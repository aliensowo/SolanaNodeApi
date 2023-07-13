import os

from dotenv import load_dotenv
from solana.publickey import PublicKey
from solana.rpc.api import Client

load_dotenv()

solana_client = Client(os.environ.get("MAIN_NET_BETA"))
print(solana_client.is_connected())
address = "J7nSEX8ADf3pVVicd6yKy2Skvg8iLePEmkLUisAAaioD"
# address = "FMZpRCtDwbGui79TsztM6M7f4WVcPaYgaZbZZwXnq6Ji"
# resp = solana_client.get_account_info(address)
resp = solana_client.get_balance(PublicKey(address))
print(resp)
