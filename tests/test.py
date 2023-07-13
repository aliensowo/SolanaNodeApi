import base64
import io

import requests
from PIL import Image

url = "http://127.0.0.1:11503/get-account-info/TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
url = "http://127.0.0.1:11503/get-account-info/ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"


data = requests.get(url).json()["value"]["data"][0]

with open("../example.png", "rb") as f:
    data = base64.b64encode(f.read())

print(data)
# data = """iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="""
# data = base64.b64decode(data)
# img = Image.open(io.BytesIO(data))
# img.save("tests.png", "png")

with open("tests.jpg", "wb") as f:
    # print(data)
    # data = data.decode("base64")
    data = base64.b64decode(data)
    # print(data)
    f.write(data)
