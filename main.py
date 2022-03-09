import os
from dotenv import load_dotenv
import requests
from web3 import Web3
import abis
import time
load_dotenv()
import re
import sys
import json

bsc = 'https://speedy-nodes-nyc.moralis.io/88f9e10ecc7056e5ba53e173/bsc/mainnet'    
web3 = Web3(Web3.HTTPProvider(bsc))
print(web3.isConnected())
#Pancakeswap Factory & Router contracts for pancakeswap

routerMainnet = web3.toChecksumAddress('0x10ED43C718714eb63d5aA57B78B54704E256024E')
factoryMainnet = web3.toChecksumAddress('0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73')

#Token WBNB Main & Testnet 

wbnbMainnet = web3.toChecksumAddress('0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c')


#UserAddress to buy token with
sender_address = web3.toChecksumAddress('')  #address that buys the token

#input tokenaddress which you want to check
contractAddress = web3.toChecksumAddress(input('enter contract address: '))
BASE_URL = 'https://api.bscscan.com/api'
API_KEY = os.getenv('etherAPI')
privateKey = os.getenv('privateKey')

score = 0

url = BASE_URL + "?module=contract&action=getabi&address=" + contractAddress + "&apikey=" + API_KEY
check = requests.get(url).json()

if check['status'] == '1':
    abi = check['result']
    print('contract verified')
    score += 1
else:
    print('contract not verified')
    exit()

contract = web3.eth.contract(address=contractAddress, abi=abi)
name = contract.functions.name().call()
decimals = contract.functions.decimals().call()
DECIMAL = 10 ** decimals
totalSupply = contract.functions.totalSupply().call() / DECIMAL 
symbol = contract.functions.symbol().call()
print(name, symbol, totalSupply)


# get LP pair contract
factoryContract = web3.eth.contract(factoryMainnet,abi=abis.panFacAbi)
getLpAddress = factoryContract.functions.getPair(contractAddress,wbnbMainnet).call()
print('LP Pair Address: ' + str(getLpAddress))

#initialize LP contract to get Lp token balance 
lpContract = web3.eth.contract(address=getLpAddress, abi=lpAbi)
lpdecimals = lpContract.functions.decimals().call()
lpDECIMAL = 10 ** lpdecimals
totalLpBalance = lpContract.functions.totalSupply().call() / lpDECIMAL
print('Total Lp Balance: ' + str(totalLpBalance))

#buy and sell functions
def testSell():
   
    contractRouter = web3.eth.contract(address=routerMainnet, abi=abis.routerAbi)
    #Token to buy 
    tokenToBuy = contractAddress
    spend = wbnbMainnet
    balanceOfSenderAddress = contract.functions.balanceOf(sender_address).call()
    nonce = web3.eth.get_transaction_count(sender_address)
    
    #Buy token with bnb use 'swapExactETHForTokens' or if you want to buy with busd or token use 
    # swapExactTokenForTokensSupportingFeeOnTransferTokens for rebase token or use swapExactETHForTokens
    pancakeswap2_txn = contractRouter.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
    #tokenA, tokenB when buying with 2 token   
    balanceOfSenderAddress -1, 0,
    [tokenToBuy, spend],
    sender_address,
    (int(time.time()) + 10000)
    ).buildTransaction({
    'from': sender_address,
    'gas': 2100000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    #Sign transaction with priavte key here
    signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=privateKey)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("testBuy was succesfull, bought & sold: " + web3.toHex(tx_token))
    time.sleep(10)

#approve
def approve():
    contract2 = web3.eth.contract(address=contractAddress, abi=abi)
    nonce = web3.eth.get_transaction_count(sender_address)
    global balanceOf
    balanceOf = contract2.functions.balanceOf(sender_address).call()
    print(balanceOf)
    approve = contract2.functions.approve(routerMainnet,balanceOf).buildTransaction({
    'from': sender_address,
    'gas': 210000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    signed_txn = web3.eth.account.sign_transaction(approve, private_key=privateKey)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print('approved ' + web3.toHex(tx_token))
    time.sleep(15)
    testSell()  
score += 5
print('total Score: ' + str(score))

# testBuy
def testBuy():
    contractRouter = web3.eth.contract(address=routerMainnet, abi=abis.routerAbi)
    #Token to buy 
    tokenToBuy = contractAddress
    spend = wbnbMainnet
    nonce = web3.eth.get_transaction_count(sender_address)

    #Buy token with bnb use 'swapExactETHForTokens' or if you want to buy with busd or token use 
    # swapExactTokenForTokensSupportingFeeOnTransferTokens for rebase token or use swapExactETHForTokens
    pancakeswap2_txn = contractRouter.functions.swapExactETHForTokens(
    #tokenA, tokenB when buying with 2 token   
    0, #tokenB, 
    [spend,tokenToBuy],
    sender_address,
    (int(time.time()) + 10000)
    ).buildTransaction({
    'from': sender_address,
    'value': web3.toWei(0.0001,'ether'),#This is the Token(BNB) amount you want to Swap from  | Comment out for token
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    #Sign transaction with priavte key here
    signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=privateKey)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Buying token: " + web3.toHex(tx_token))
    time.sleep(15)
    approve()



try:
    if 'owner' in abi:
        owner = contract.functions.owner().call()
        if owner != web3.toChecksumAddress('0x0000000000000000000000000000000000000000'):
            print(owner)
            balanceOf = contract.functions.balanceOf(owner).call()
            
            if balanceOf > 0:
                print('owner holds : ' + balanceOf  + '' + symbol)
            else:
                print('owner holds no token') 
        
             
            
            #check owner Lp token
            balanceLp = lpContract.functions.balanceOf(owner)
            
            if balanceLp > 0:
                ownerPerLp = (totalLpBalance/ balanceLp) * 100
                print('owner holds ' + balanceOf + 'lptoken')
                print('owner holds ' + ownerPerLp + ' % Lp token')
            else:
             print(owner + ' holds no LP token')    
             score += 2
              
        else:
            print(owner + ' ownership renounced')
            score += 2
except:
    print('no owner')
    score += 2


#check for buy and sell Fee

if 'charityFee' in abi:
    charityFee = contract.functions._charityFee().call()
    print('Charity Fee: '+ str(charityFee))
    if 'liquidityFee' in abi:
        liquidityFee = contract.functions._liquidityFee().call()
        print('liquidityFee:' + str(liquidityFee))
        if 'taxFee' in abi:
            taxFee = contract.functions._taxFee().call()
            print('TaxFee: ' + str(taxFee))
            if 'maxTxAmount' in abi:
                maxTx = contract.functions._maxTxAmount().call()
                print('Max tx: ' + str(maxTx))
                totalFee = charityFee + liquidityFee + taxFee
                print('TotalFee: ' + str(totalFee) )
else:
    print('no buy or sell fee detected')
    score +=2

    
#starting test buy
testBuy()







