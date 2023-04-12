# TelegramChatBot
- This is a chatbot powered by GPT3.5, which you can easily hypnotize into a specified character with simply one click. Using the latest 'system' parameter, It can effectively avoid forgetting the character settings during chatting. You can also conveniently manage and create new hypnosis spells. The latest version of this project has support for calling the stable diffusion API to generate images, you can describe the desired images in natural language, the image prompt will be generated by GPT3.5 automatic. Of course,  you can also use manually created image prompt
- If you want to deploy this bot, Don't forget to message [@BotFather](https://t.me/botfather) on Telegram to register your bot and receive its authentication token. Check https://core.telegram.org/bots#how-do-i-create-a-bot
- Try it right now by [@jokerController_bot ](https://t.me/jokerController_bot ) on Telegram !



## Setup

1. Create a new virtual environment with python 3.10, here is an example with anaconda

   ```shell
   conda create -n ChatBot python=3.10
   ```

2. Activate the virtual environment in anaconda

   ```shell
   activate ChatBot
   ```

3. Make sure you are in the project path, install all requirement lib by 

   ```shell
   pip install -r requirements.txt
   ```

   If the download process is too slow, Tsinghua Mirror source is recommended

   ```shell
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. Install MySQL 5.7




## State Machine

<img src="img/StateMachine.png" style="zoom: 67%;" />



----------------

搞科研就是遇到问题摸大鱼啦~~

