## <h1 align="center">A license handler to sell your code.</h1>
This is my first project involving making my own API so feel free to suggest changes.  
Also half-working etc stopped developing it after a while.

## **Why:**
One fine day when I was free-lancing, I had the sudden urge to make something that would allow me to track the usage of any piece of code that I make.  
These API endpoints allow you to do just that, and more!  

With this, you can easily see who ran which script when and where, etc
  
It has 2 versions, first on `flask` and the second one on `FastAPI`

## **I should have...?**
I probably should have made the bot request to the endpoint rather than do the work itself?  

### **Features:**
- My first thought, slap it in a discord bot.
    - bot.py gives an discord bot interface for the develoepr to activate and delete a key, as well as make a new one.
    - only and only the owner of the bot, or, the owner_ids passed in config are allowed to use the bot commands.
- The API host
    - Several (3) endpoints for... registering a new license and verifying it I guess?
    - The "register this new license for me" endpoint requiers a password, which is checked against config.api_owner_pass
    - the API requires payload data.

### **Requirements:**
- Modules:
    - aiosqlite
    - nextcord
    - flask (for v1)
    - FastAPI (for v2)

### **Self-hosting:**
- Pre-requisites
    - Basic python knowledge
    - and python installed! (needs version python3.8+)
    - also install git :)
- [Make a new bot account](https://nextcord.readthedocs.io/en/latest/discord.html#discord-intro) and [invite it to your server](https://nextcord.readthedocs.io/en/latest/discord.html#discord-invite-bot)
- [Clone(download) this repository!](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

- Rename config.py.example to config.py and fill in the values accordingly.
- Rename licenses.sqlite3.example to licenses.sqlite3
- Time to go live!
    - To start the api host:
        - V1: with flask: `python3.8 api_host_v1.py`
        - V2: with FastAPI: `uvicorn api_host_v2.py:app --host 0.0.0.0 --port 505050` # or your choice of host and port.

#### **Me:**
Hey! glad you scrolled this far, I'm koala usually. Nothing much here, if you face any issues, feel free to DM me on discord (koala#9712)
If you liked this or helped you out even in the slightest, Buy me a coffee and make my day!
- BTC (BTC): 35oNx7C6YDNfgxNoXvhZwJydQ3Bpu3746c
- LTC (LTC): MVC2viP8vZrKsgzds3juSnfySvCGi3yPMf
- USDT (ERC20): 0x8c82b8887ef114f9b6e2841f014ed21fef705b69
