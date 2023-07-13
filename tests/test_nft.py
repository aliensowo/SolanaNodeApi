import requests

response = requests.get(
    "https://api.theblockchainapi.com/v1/solana/nft",
    params={"mint_address": "DPc4S4XPEAfmEoSJ4Fw74dEiz7pgnttqQu5HRypHhvYS", "network": "mainnet-beta"},
    headers={"APISecretKey": "z5t1l52HBqGoijI", "APIKeyId": "sXkPqMm9DPXTUOl"},
)

print(response.json())
