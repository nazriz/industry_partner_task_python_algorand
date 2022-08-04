import base64
import os
from dotenv import load_dotenv
from algosdk.future import transaction
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *

load_dotenv()

ALGOD_API_KEY = os.getenv('ALGOD_API_KEY')

creator_mnemonic = "rifle snake educate gasp whisper discover tattoo shell ancient neither layer excuse protect menu hard sadness monster comic pony give champion hospital payment absorb author"
# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = ""
headers = {
    "X-API-Key": ALGOD_API_KEY,
}


# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn) :
    private_key = mnemonic.to_private_key(mn)
    return private_key


# helper function that formats global state for printing
def format_state(state):
    formatted = {}
    for item in state:
        key = item['key']
        value = item['value']
        formatted_key = base64.b64decode(key).decode('utf-8')
        if value['type'] == 1:
            # byte string
            if formatted_key == 'voted':
                formatted_value = base64.b64decode(value['bytes']).decode('utf-8')
            else:
                formatted_value = value['bytes']
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted

# helper function to read app global state
def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = app['params']['global-state'] if "global-state" in app['params'] else []
    return format_state(global_state)


# call application
def call_app(client, private_key, index, app_args) :
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])


    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 4)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return
    print("Application called")



def main():
    app_id = 103011091
    creator_private_key = "zU0zjQJG/fvIe8VECKX88FTWLCbtvXqUy08nBpO3NdRie6C4FH7mRLqODBhLzyvq1wkFNPVL8sCFVipL8Wxc0A=="
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    print("Calling Counter application......")
    app_args = ["add_name"]
    call_app(algod_client, creator_private_key, app_id, app_args)
    # app_args = ["add_address"]
    # call_app(algod_client, creator_private_key, app_id, app_args)
    # app_args = ["add_date"]
    # call_app(algod_client, creator_private_key, app_id, app_args)
    # app_args = ["add_id_num"]
    # call_app(algod_client, creator_private_key, app_id, app_args)


    # read global state of application
    print("Global state:", read_global_state(algod_client, app_id))

main()