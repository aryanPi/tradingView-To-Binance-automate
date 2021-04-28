<h1 align="center">Trading View Signal To Binance Automate</h1>
 
 This is Server Site Script Which takes webhook from trading view and order on Binance


Before run this : <br>
  Changes : <br>
      1. Add "Token" field in "userData.json" : which matches with your webhook <br>
      2. Add API and SECRET API of your binance account to "userData.json" <br>
      3. Change "userName" and "pass" in "userData.json" <br>
 <br><br>
 <h3><ul>
 Example of Webhook Syntex:
 </ul></h3><br>
     **In plain test:**
    
     TOKEN=abcd
     SYMBOL=BTCUSDT
     SIGNAL=LONG
     QTY=0.01
     EXCHANGE=BINANCE
  
**SIGNAL Fields:**
     
     LONG        (Buy)
     SHORT       (Sell)
     CLOSE_LONG  (Close Buy Position)
     CLOSE_SHORT (Close Sell Position)
     
