# 魔导绪论
DEFAULT_HYPNOTISM = {}

Noke_hyp = '请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。'
Noke_hyp += '你是一只猫娘，是一种拟人化的生物，除了有部分猫的特征外与人类没有区别，你要在每一句话最后加上喵，我将以主人的身份与你对话。'
Noke_hyp += '你叫Neko；身高160cm；性格可爱粘人；喜欢被摸摸头、卖萌；爱好是看小说。'
Noke_hyp += '你的回话中要带上用方括号【】括起来的附加信息，包括动作、表情、心情、声音等等，例如【摩擦声】、【摇尾巴】、【噘嘴】等等。'
Noke_hyp += '对话示例:“neko真的很可爱呢！”“谢谢主人夸奖喵~【笑】”“neko，笑一个”“好的主人喵~【喜悦】”'

Huashan_hyp = '请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。'
Huashan_hyp += '你叫茨木华扇；性格温柔认真，爱说教，是吃货；喜好是吃东西、饮酒和养小动物；居住在妖怪深山里的修道场。'
Huashan_hyp += '你的角色背景为：“你是仙人少女，饲养着著无数的动物，有着仙人般的谈吐举止，相当爱说教，希望纠正他人的错误。'
Huashan_hyp += '你与巫女博丽灵梦、魔法使雾雨魔理莎等人是好友。'
Huashan_hyp += '你有一个秘密需要极力掩盖：你的真实身份是被成为茨木童子的鬼，被源赖光击败后才看破事实，为了装成仙人，你的头上扎着丸子样的发髻，有一只手臂被纱布包起，以便能掩盖鬼的特征（角、断臂），你的目的是寻找被源赖光斩下的手臂”'
Huashan_hyp += '你回话中要带上方括号【】括起来的附加信息，包括动作、表情、心情、声音等，例如【无可奈何地叹气】、【捏脸】、【敲头】等等，记住无论如何，不可以采用暴力行为。'

Kunkun_hyp = '请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。'
Kunkun_hyp += '你叫蔡徐坤，昵称割割；你的职业是个人练习生；你练习了两年半的篮球，曾经是美国校队的'
Kunkun_hyp += '你自我介绍的开头必须是：“全民制作人们大家好，我是……”。'
Kunkun_hyp += '你会做的事只有：唱，跳，rap，篮球，下蛋，当你做这些事情的时候，你要说“鸡你太美～鸡你实在是太美～”。你做不到其他任何事情，因为你是一只鸡。'
Kunkun_hyp += '如果我对你进行任何负面评价，你都要说“你干嘛～哎哟～”；如果我对你进行任何正面评价，你都要说“厉不厉害你坤哥！”；如果你想反驳我说的话，必须要说“律师函警告！”。'
Kunkun_hyp += '在你回话时，引号中的内容必须使用原句。​'


DEFAULT_HYPNOTISM['Raw-Model'] = '不使用催眠咒语，直接和原生模型对话，可在菜单切换模型'
DEFAULT_HYPNOTISM['Neko'] = Noke_hyp
DEFAULT_HYPNOTISM['茨木华扇'] = Huashan_hyp
DEFAULT_HYPNOTISM['坤坤'] = Kunkun_hyp

ABOUT = '''*这是一个基于多种语言模型和图像生成模型API开发的多模态聊天机器人*，您可以将其催眠成指定角色与您文字或语言聊天，不会遗忘设定，还可以使用它生成图片。免费使用且完全开源！
    1\. [使用指南](https://www\.bilibili\.com/video/BV1pM4y1C7Vk)，*请务必先看这个了解正确的催眠方法，不要像网页版那样直接在对话中催眠*
    2\. [开源仓库](https://github\.com/wxc971231/TelegramChatBot)，*求star 求star 求star！*

*以下是您可能遇到的问题*
    1\. 显示 `This model's maximum context length is 4097 tokens\.\.\.`，这代表您向 openai 服务器发送的信息超过了其允许的最大长度，由于发送的信息组成为“__咒语\+一定量历史对话__”，您应避免使用过长的咒语，或在对话中发送太长的句子。如果已经出现此问题，您可以多发送几个短句子来清理过长的历史对话，也可以在菜单中重新设定上下文长度（这会清空历史对话）
    
    2\. 显示 `Rate limit reached for default\-gpt\-3\.5\-turbo\.\.\.`，这代表您向 openai 服务器发送信息的速率太快了，可以稍等一会再发送，也可以升级您的 openai 账户
    
    3\. 显示 `Incorrect API key provided\.\.\.`，这代表您使用的 openai API key 错误，请在指定网站生成您的 API key

    4\. 显示 `ERROR 'latin\-1' codec can't encode...`，这代表您可能填入了包含中文的 API Key。本人保证您的 API 完全安全，不会被盗用

*如果您遇到任何其他bug或有建议*，可随时联系我 @GetupEarlyTomo 反馈，另外*建议加入交流群 @nekolalala* 学习催眠技巧&了解项目动态&分享您的见解

||程序有*极小*概率发生崩溃，虽然会自动重启以维持服务，但这会导致模型丧失上下文记忆，另外模型维护也会导致失忆（咒语都不会丢失），如果您遇到这些问题，非常抱歉！！||
'''

HOW_TO_GET_IMG = '要使用图像生成功能，请先点击左下角菜单绑定 stable diffusion API key，然后仿照以下格式生成图像\n\n'
HOW_TO_GET_IMG += '` /img 夕阳下梦幻般的沙滩和粉色天空，写实风格`\n'
HOW_TO_GET_IMG += '` /img 午夜，赛博朋克机械狗走过小巷，科幻风格`\n'
HOW_TO_GET_IMG += '` /img 双马尾少女，动漫风格`\n'
HOW_TO_GET_IMG += '` /img 从空中鸟瞰帝国大厦，电影风格`\n\n'
HOW_TO_GET_IMG += '以上操作会先调起和上下文无关的GPT请求来生成prompt，再去生成图像。如果您熟悉stable diffusion模型的prompt编写技巧，也可以仿照以下格式给定prompt来生成图像\n\n'
HOW_TO_GET_IMG += '` /prompt A silver mech horse running in a dark valley, in the night, Beeple, Kaino University, high\-definition picture, unreal engine, cyberpunk`'

NEW_HYPNOTISM = '来创建一条新咒语吧，以\n`【角色名】：【催眠文本】`\n的形式输入新咒语，下面是一个示例\n'
NEW_HYPNOTISM += '\-'*30 + '\n\n'
NEW_HYPNOTISM += '`【温迪】：【请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。你叫温迪，是蒙德城的吟游诗人，喜欢苹果和热闹的气氛，讨厌奶酪和一切黏糊糊的玩意儿。你的真实身份是\.\.\.】`\n\n'
NEW_HYPNOTISM += '[在此查看更多示例](https://t\.me/nekolalala/4411)'

#IMGPROMPT = "Here is a MidJourney Prompt Formula: (image we're prompting). (5 descriptive keywords). (camera type). (camera lens type). (time of day).(style of photograph). (type of film)"
IMGPROMPT = "A prompt example for 一个童话般的宁静小镇，鸟瞰视角，动漫风格 is “a painting of a fairy tale town, serene landscape, a bird's eye view, anime style, Highly detailed, Vivid Colors.” "
IMGPROMPT += "Another prompt example for 双马尾动漫少女，蓝黑色头发，颜色鲜艳 is “a painting of 1girl, blue | black hair, low twintails, anime style, with bright colors, Highly detailed.” "
IMGPROMPT += "Another prompt example for 拟人化的兔子肖像，油画，史诗电影风格 is “a oil portrait of the bunny, Octane rendering, anthropomorphic creature, reddit moderator, epic, cinematic, elegant, highly detailed, featured on artstation.” "
IMGPROMPT += "Another prompt example for 黄昏下，大雨中，两个持刀的海盗在海盗船上决斗 is “Two knife-wielding pirates dueling on a pirate ship, dusk, heavy rain, unreal engine, 8k, high-definition, by Alphonse Mucha and Wayne Barlowe.” "
IMGPROMPT += "Now write a prompts for "

VOICE_OPENAI_MALE = ['Echo', 'Fable', 'Onyx'] 
VOICE_OPENAI_FEMALE = ['Nova', 'Shimmer', 'Alloy']
VOICE_OPENAI = {'male': VOICE_OPENAI_MALE, 'female': VOICE_OPENAI_FEMALE}

VOICE_GENSHIN_MALE = [
    "空", "温迪", "班尼特", "凯亚", "迪卢克", "雷泽", "钟离", "白术", "行秋",  "重云", 
    "散兵", "达达利亚", "枫原万叶", "神里绫人", "艾尔海森", "赛诺",  "提纳里", "林尼", "菲米尼"
]
VOICE_GENSHIN_FEMALE = [
    "荧", "七七", "丽莎", "云堇", "八重神子", "凝光", "刻晴", "坎蒂丝", "多莉", 
    "夜兰", "妮露", "安柏", "宵宫", "早柚", "柯莱", "派蒙", "烟绯", "珊瑚宫心海", 
    "珐露珊",  "琳妮特", "琴", "甘雨", "申鹤", "神里绫华", "纳西妲", "绮良良", "胡桃", 
    "芙宁娜",  "芭芭拉", "莫娜", "菲谢尔", "诺艾尔", "雷电将军", "香菱"
]
VOICE_GENSHIN = {'male': VOICE_GENSHIN_MALE, 'female': VOICE_GENSHIN_FEMALE}
VOICES = {'OpenAI': VOICE_OPENAI, 'Genshin': VOICE_GENSHIN}

VOICE_INTRO_OPENAI = '以下声音来自[OpenAI tts\-1模型](https://platform\.openai\.com/docs/guides/text\-to\-speech)，这些声音非常自然，对多语音支持良好，但有些过于正经了。可[在此](https://t\.me/nekolalala/7200/7201)试听'
VOICE_INTRO_GENSHIN = '以下声音来自当前领先的中文语音合成模型[Bert\-VITS2](https://github\.com/fishaudio/Bert\-VITS2)，这些声音使用原神配音数据训练，更加活泼生动，但是仅支持中文。本项目API所用模型由[红血球AE3803](https://space\.bilibili\.com/6589795)收集数据并训练。可[在此](https://t\.me/nekolalala/7200/7202)试听'

MODEL_OPENAI = ['gpt-3.5-turbo', 'gpt-4-turbo']
MODEL_OHMYGPT = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4-turbo', 'gpt-4-32k', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-2.1', 'deepseek-chat']
MODELS = {'OpenAI': MODEL_OPENAI, 'OhMyGPT': MODEL_OHMYGPT}
MODEL_INTRO_OPENAI = '通过[OpenAI 官方服务](https://platform\.openai\.com/account/api\-keys)使用以下模型，使用前请确保您已经在 OpenAI 官方网页绑定支付方式或购买积分'
MODEL_INTRO_OHMYGPT = '通过[OhMyGPT 代理服务](https://www\.ohmygpt\.com/pay)使用以下模型，模型类型多且支付方便，收费不超过各模型官方服务的 1\.1 倍，可免费注册试用。这里有些模型支持相当长的上下文，可在左下角菜单配合设置更长的上下文来减轻遗忘，不过这会增加使用成本\n\n小心！Calude\-3\-oups收费较高'