# tradingView-signal-to-binance-future
 
 <h1 align="center">Project title</h1>
 
 This is Server Site Script Which takes webhook from trading view and order on Binance


Before run this : <br>
  Changes : <br>
      1. Add "Token" field in "userData.json" : which matches with your webhook <br>
      2. Add API and SECRET API of your binance account to "userData.json" <br>
      3. Change "userName" and "pass" in "userData.json" <br>
 <br><br>
 Example of Webhook Syntex:<br>
     In plain test:
    
     TOKEN=abcd
     SYMBOL=BTCUSDT
     SIGNAL=LONG
     QTY=0.01
     EXCHANGE=BINANCE
  
  SIGNAL Fields: 
     
     LONG        (Buy)
     SHORT       (Sell)
     CLOSE_LONG  (Close Buy Position)
     CLOSE_SHORT (Close Sell Position)
     
