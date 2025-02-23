# 🤖 Discord Bot  

This repository contains a **Discord bot** built using `discord.py`. The bot includes multiple functionalities such as **cryptocurrency tracking** and **competition management** using a modular **cog-based structure**.  

## 🚀 Features  
- ✅ **Cryptocurrency Tracking** – Get live crypto prices.  
- ✅ **Competition Management** – Manage and track competitions.  
- ✅ **Custom Commands** – Easily extend functionality using cogs.  
- ✅ **Environment Variable Support** – Uses `.env` for token management.  

## 📂 Files in this Repository  
### 🔹 Core Files  
- `main.py` – The core bot script that initializes and loads cogs.  
- `.env` (included in .zip) – Stores the bot token securely.  

### 🔹 Cogs (Modular Extensions)  
- `cogs/crypto.py` – Handles cryptocurrency-related commands.  
- `cogs/competition.py` – Manages competition events.  

### 🔹 Other Files  
- `requirements.txt` – List of dependencies for easy setup.  
- `discord_bot.zip` – A compressed version of the project with all necessary files in it as well as tokens and all.  

## 🛠️ Installation & Setup  
### **1️⃣ Clone the Repository**  
    git clone https://github.com/mr-coder07/DISCORD_BOT.git
    cd project_1

### **2️⃣ Install Dependencies**  
    pip install -r requirements.txt
    
### **3️⃣ Run the bot**  
    python main.py

### **⚙️ Bot Commands**
!crypto <coin>  - Fetches the latest price of a cryptocurrency.  
!competition start  - Starts a new competition.  
!competition end  - Ends the current competition.  
!help  - Displays the custom help command.  

### **📜 Requirements**
discord.py==2.0.0  
cryptography==39.0.1  
python-dotenv==0.20.0  

