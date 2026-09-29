from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger, AstrBotConfig

import random as rd
from pathlib import Path as pt

# 常量，配置文件相关
MODE_DAILY = 1
MODE_RANDOM = 2

ROLL_7D2 = 1
ROLL_3D6 = 2
ROLL_D128 = 3

CURRENT_PATH = pt(__file__).parent


def draw_7d2():
    # 模拟书中的7硬币法
    lt = []
    res = 0
    for i in range(7):
        lt.append(rd.randint(0, 1))
    for i in range(7):
        res += lt[6 - i] * (2 ** i)
    return lt, res


def draw_3d6():
    # 模拟书中的六面骰法
    roll2 = 0
    roll3 = 0
    while (roll1 := rd.randint(1, 6)):
        if roll1 <= 4:
            roll2 = rd.randint(1, 6)
            roll3 = rd.randint(1, 6)
            break
    lt = [roll1, roll2, roll3]
    if (res := roll1 * 36 + roll2 * 6 + roll3 - 42) >= 128:
        return draw_3d6()
    else:
        return lt, res


def draw_d128():
    return rd.randint(1, 128)


@register("astrbot_plugin_touhou_genzon_mikuji", "dingxy-hikari",
          "A plugin that makes bot can draw a mikuji and send to chat", "1.1.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str  # 用户发的纯文本消息字符串
        message_chain = event.get_messages()  # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!")  # 发送一条纯文本消息

    @filter.command("draw_daily_mikuji", alias={"抽今日幻存神签", "今日幻存神签", "抽取今日幻存神签"})
    async def draw_daily_mikuji(self):
        pass

    @filter.command("draw_random_mikuji", alias={"抽随机幻存神签", "随机幻存神签", "抽取随机幻存神签"})
    async def draw_random_mikuji(self, event: AstrMessageEvent):
        """抽随机幻存神签"""
        lt, res = draw_3d6()
        chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Plain(f"您抽到的是：{lt[0]}*36+{lt[1]}*6+{lt[2]}-42={res}"),
            Comp.Image.fromFileSystem(str(CURRENT_PATH/"resource"/"mikuji"/f"{res:03d}.png"))
        ]
        yield event.chain_result(chain)

    @filter.command("draw_mikuji", alias={"抽幻存神签", "幻存神签", "抽取幻存神签"})
    async def draw_mikuji(self,event: AstrMessageEvent):
        self.draw_random_mikuji(event)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
