## <h1 align="center">A license handler to sell your code.</h1>
This is my first project involving making my own API so feel free to suggest changes.  
SO! I stopped developing this mid-way, hence the name `Archive`. However, I have rewrote everything as the need arises and the latest code is now housed in `src`

## **Why:**
Well, sometimes ye wanna sell code, this allowes you to do just that!
Currently, most of the codes I saw request to a pastebin, which seemed like a horrible way. This is obviously not as good as a licenser should be, but good enough I say.

### **Features:**
- My first thought, slap it in a discord bot.
    - `bot.py` gives a bot interface for develoeprs to make, update, and delete new license keys.
    - Only configured users are allowed to use the bot commands.
- The API host
    - The few endpoints that exist, help in somewhat granual requests for smooth functioning

### **Requirements:**
- Modules:
    - aiosqlite
    - nextcord
    - flask (for v1)
    - FastAPI (for v2/v3)

### **Self-hosting:**
- Pre-requisites
    - Basic python knowledge
    - and python installed! (needs version python3.8+)
    - also install git :)
- [Make a new bot account](https://nextcord.readthedocs.io/en/latest/discord.html#discord-intro) and [invite it to your server](https://nextcord.readthedocs.io/en/latest/discord.html#discord-invite-bot)
- [Clone(download) this repository!](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

- Rename `config.json.example` to `config.json` and fill in the required values.
- Rename `licenses.sqlite3.example` to `licenses.sqlite3`
- Time to go live!
    - To start the api host:
        - V1: with flask: `python3.8 api_host_v1.py`
        - V2: with FastAPI: `uvicorn api_host_v2:app --host 0.0.0.0 --port 5050` # or your choice of host and port.
        - V3: with FastAPI: `uvicorn api_host_v3:app --host 0.0.0.0 --port 5050` # or your choice of host and port.

#### **Me:**
Hey! glad you scrolled this far, I'm koala usually. Nothing much here, if you face any issues, feel free to DM me on discord! They keep changing my name so just find me [here](https://thekoalaco.in)
