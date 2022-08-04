import base64
import os
from dotenv import load_dotenv
from algosdk.future import transaction
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *

load_dotenv()

ALGOD_API_KEY = os.getenv('ALGOD_API_KEY')
ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS')
WALLET = os.getenv('WALLET')

# ==== PLEASE POPULATE creator_mnemonic with the mnemonic of the address that is to be used for contract deployment + attribute population =====
# user declared account mnemonics
creator_mnemonic = WALLET
# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config

# ==== PLEASE POPULATE algod_address and api_key with relevant algorand testnet endpoint and key ====
algod_address = ALGOD_ADDRESS
algod_token = ""
headers = {
    "X-API-Key": ALGOD_API_KEY,
}


# helper function to compile program source
def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

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


"""Attribute Contract Pyteal"""

def approval_program(name, address, date, id):

    on_creation = Seq([
     Approve()
    ])

    global_name = Bytes("name")
    global_address = Bytes("address")
    global_date = Bytes("date")
    global_id = Bytes("id")

    # on_creation = Return(Int(0))

    handle_optin = Return(Int(0))

    handle_closeout = Return(Int(0))

    handle_updateapp = Return(Int(0))

    handle_deleteapp = Return(Int(0))


    addName = Seq([
      App.globalPut(global_name, Bytes(name)),
        Approve(),
    ])

    addAddress = Seq([
            App.globalPut(global_address, Bytes(address)),
        Approve(),
   ])

    addDate = Seq(
        App.globalPut(global_date, Bytes(date)),
        Approve(),
    )

    addId = Seq(
        App.globalPut(global_id, Bytes(id)),
        Approve(),
    )

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("addName")
        ), addName],
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("addAddress")
        ), addAddress],
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("addDate")
        ), addDate],
         [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("addId")
        ), addId],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=5)

def clear_state_program():
    program = Return(Int(1))
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=5)


# create new application
def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(sender, params, on_complete, \
                                            approval_program, clear_program, \
                                            global_schema, local_schema)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print("Created new app-id:", app_id)

    return app_id


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

def main() :

    input_name = input("Please enter a name: ")
    input_address = input("Please enter an address: ")
    input_date = input("Please enter a date: ")
    input_id = input("Please enter an ID: ")

    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    # define private keys
    creator_private_key = get_private_key_from_mnemonic(creator_mnemonic)

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 4
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = approval_program(input_name, input_address, input_date, input_id)
        f.write(approval_program_teal)


    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = clear_state_program()
        f.write(clear_state_program_teal)

    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, clear_state_program_teal)

    print("--------------------------------------------")
    print("Deploying Attribute Contract application......")

    # create new application
    app_id = create_app(algod_client, creator_private_key, approval_program_compiled, clear_state_program_compiled, global_schema, local_schema)

    # read global state of application, show contract has no initialised values
    print("Global state:", read_global_state(algod_client, app_id))

    # Make contract calls for storing onchain values.
    print("--------------------------------------------")
    print("Calling addName......")
    app_args = ["addName"]
    call_app(algod_client, creator_private_key, app_id, app_args)
    print("--------------------------------------------")
    print("Calling addAddress......")
    app_args = ["addAddress"]
    call_app(algod_client, creator_private_key, app_id, app_args)
    print("--------------------------------------------")
    print("Calling addDate......")
    app_args = ["addDate"]
    call_app(algod_client, creator_private_key, app_id, app_args)
    print("--------------------------------------------")
    print("Calling addId......")
    app_args = ["addId"]
    call_app(algod_client, creator_private_key, app_id, app_args)

    # read global state of application
    contractGlobalState = read_global_state(algod_client, app_id)
    print("Global state:", contractGlobalState)

    # Decode onchain attributes from base64 into utf-8
    print("--------------------------------------------")
    print(f"Decoded onchain attributes in contract with app-id: {app_id}")
    for attribute in contractGlobalState:
        print(f" {attribute}: {base64.b64decode(contractGlobalState[attribute]).decode('utf-8')}")



main()

