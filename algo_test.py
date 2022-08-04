import os
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic

<<<<<<< HEAD
load_dotenv() # Load env variables
=======
load_dotenv()
>>>>>>> 29d53714e0a2343ba5899d647ace0ea501758f1a

ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS')
ALGOD_API_KEY = os.getenv('ALGOD_API_KEY')


algod_address = ALGOD_ADDRESS
algod_token = ""
headers = {
    "X-API-Key": ALGOD_API_KEY,
}

# Initialize an algod client
algod_client = algod.AlgodClient(algod_token, algod_address, headers)

def generate_algorand_keypair():
    private_key, address = account.generate_account()
    print("My address: {}".format(address))
    print("My private key: {}".format(private_key))
    print("My passphrase: {}".format(mnemonic.from_private_key(private_key)))

# generate_algorand_keypair()

accAddr = "QHB6WEO3OTVDCJFPS76P7VNAEOFXJX6URXTGRTYL4DYBJ6UCTDLOMBHO3I"
accPk = "EpxRP8av9Ubej7NgBY6Wu37vvnq8yJSvphp32Rj71K6Bw+sR23TqMSSvl/z/1aAji3Tf1I3maM8L4PAU+oKY1g=="

account_info = algod_client.account_info(accAddr)

print(account_info)
print("Account balance: {} microAlgos".format(account_info.get('amount')) + "\n")
