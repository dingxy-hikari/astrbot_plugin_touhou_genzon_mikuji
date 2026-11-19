from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger, AstrBotConfig
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

import json
import random as rd
import datetime as dt
from pathlib import Path

# 常量，定位图片资源
CURRENT_PATH = Path(__file__).parent


def draw_7d2():
    # 模拟书中的7硬币法
    lt = []
    res = 0
    for i in range(7):
        lt.append(rd.randint(0, 1))
    for i in range(7):
        res += lt[6 - i] * (2 ** i)
    return f"您抽到的是：{lt[0]}*64+{lt[1]}*32+{lt[2]}*16+{lt[3]}*8+{lt[4]}*4+{lt[5]}*2+{lt[6]}*1={res}",res


def draw_3d6():
    # 模拟书中的六面骰法
    roll2 = 0
    roll3 = 0
    while roll1 := rd.randint(1, 6):
        if roll1 <= 4:
            roll2 = rd.randint(1, 6)
            roll3 = rd.randint(1, 6)
            break
    lt = [roll1, roll2, roll3]
    if (res := roll1 * 36 + roll2 * 6 + roll3 - 42) >= 128:
        return draw_3d6()
    else:
        return f"您抽到的是：{lt[0]}*36+{lt[1]}*6+{lt[2]}-42={res}",res



def draw_d128():
    res = rd.randint(1, 128)
    return f"您抽到的是：r1d128={res}",res


@register("astrbot_plugin_touhou_genzon_mikuji", "dingxy-hikari",
          "A plugin that makes bot can draw a mikuji and send to chat", "1.1.1")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.config = config
        self.plugin_data_path = (
                Path(get_astrbot_data_path()) / "plugin_data" / self.name
        )
        if not self.plugin_data_path.exists():
            self.plugin_data_path.mkdir(parents=True, exist_ok=True)
        self.record_path = self.plugin_data_path / "record.json"
        self._date = self.date_update()

    def draw(self):
        match (self.config["drawing_method"]):
            case "d128":
                return draw_d128()
            case "7d2":
                return draw_7d2()
            case _:
                return draw_3d6()

    async def random_mikuji(self, event: AstrMessageEvent):
        """抽随机幻存神签的底层实现"""
        lt, res = self.draw()
        chain = [
            Comp.Plain(lt),
            Comp.Image.fromFileSystem(str(CURRENT_PATH / "resource" / "mikuji" / f"{res:03d}.png"))
        ]
        if event.get_group_id() == "":
            chain.insert(0,Comp.At(qq=event.get_sender_id()))
        yield event.chain_result(chain)

    async def daily_mikuji(self, event: AstrMessageEvent):
        """抽每日幻存神签的底层实现"""
        data = self.record_read()
        receive = event.get_sender_id()
        if data is None or receive not in data.keys():
            lt, res = self.draw()
            chain = [
                Comp.Plain(lt),
                Comp.Image.fromFileSystem(str(CURRENT_PATH / "resource" / "mikuji" / f"{res:03d}.png"))
            ]
            if event.get_group_id() != "":
                chain.insert(0,Comp.At(qq=event.get_sender_id()))
            data[receive] = res
            self.record_save(data)
        else:
            chain = [
                Comp.Plain(f"您今天抽过了，抽到的是：{data[receive]}"),
                Comp.Image.fromFileSystem(str(CURRENT_PATH / "resource" / "mikuji" / f"{data[receive]:03d}.png"))
            ]
            if event.get_group_id() != "":
                chain.insert(0,Comp.At(qq=receive))
        yield event.chain_result(chain)

    def date_update(self):
        """日期更新函数"""
        td = dt.date.today()
        return f"{td.year}{td.month:02d}{td.day:02d}"

    def record_read(self):
        """从数据文件读取今日抽取数据"""
        self.date_update()
        try:
            with open(self.record_path, "r", encoding="utf-8") as rf:
                record = json.load(rf)
        except FileNotFoundError:
            self.record_save(dict())
            with open(self.record_path, "r", encoding="utf-8") as rf:
                record = json.load(rf)
        finally:
            if record["date"] != self._date:
                self.record_save(dict())
                return None
            else:
                return record["data"]

    def record_save(self, record: dict):
        """将今日抽取数据保存至数据文件"""
        pdata = None
        with open(self.record_path, "r", encoding="utf-8") as rf:
            pdata = json.load(rf)
        with open(self.record_path, "w", encoding="utf-8") as rf:
            pdata["date"] = self._date
            pdata["record"].update(record)
            json.dump(pdata, rf)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    @filter.command("draw_daily_mikuji", alias={"抽今日幻存神签", "今日幻存神签", "抽取今日幻存神签","今日神签"})
    async def draw_daily_mikuji(self, event: AstrMessageEvent):
        """抽每日幻存神签"""
        async for i in self.daily_mikuji(event):
            yield i

    @filter.command("draw_random_mikuji", alias={"抽随机幻存神签", "随机幻存神签", "抽取随机幻存神签","随机神签"})
    async def draw_random_mikuji(self, event: AstrMessageEvent):
        """抽随机幻存神签"""
        async for i in self.random_mikuji(event):
            yield i

    @filter.command("draw_mikuji", alias={"抽幻存神签", "幻存神签", "抽取幻存神签","神签"})
    async def draw_mikuji(self, event: AstrMessageEvent):
        """根据Config的配置抽随机幻存神签(默认)或者抽每日幻存神签"""
        match(self.config["default_draw_mikuji_behavior"]):
            case "Daily":
                async for i in self.daily_mikuji(event):
                    yield i
            case "Random":
                async for i in self.random_mikuji(event):
                    yield i

    @filter.command("help_mikuji", alias={"幻存神签帮助", "神签帮助"})
    async def help_mikuji(self, event: AstrMessageEvent):
        chain = [
            Comp.Plain("幻存神签插件帮助："),
            Comp.Plain("本插件所使用东方幻存神签汉化图片均来自「吃不飽」汉化组"),
            Comp.Plain("源发布页面："),
            Comp.Plain("https://www.bilibili.com/opus/1184664409608290304"),
            Comp.Plain("https://www.bilibili.com/opus/1184896638522490897"),
            Comp.Plain("使用/今日神签,/抽今日幻存神签, /今日幻存神签, /抽取今日幻存神签以获取今日内唯一神签"),
            Comp.Plain("使用/随机神签,/抽随机幻存神签, /随机幻存神签, /抽取随机幻存神签以随机抽取一张"),
            Comp.Plain("使用/神签,/抽幻存神签, /幻存神签, /抽取幻存神签以根据插件默认行为抽取"),
        ]
        match(self.config["default_draw_mikuji_behavior"]):
            case "Daily":
                chain.insert(len(chain)-1,Comp.Plain("当前/神签默认行为：/今日神签"))
            case "Random":
                chain.insert(len(chain)-1,Comp.Plain("当前/神签默认行为：/随机神签"))
        if event.get_group_id() != "":
            chain.insert(0,Comp.At(qq=event.get_sender_id()))
        yield event.chain_result(chain)



    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
