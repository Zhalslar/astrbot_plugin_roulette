import random
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot import logger
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from .utils import ban, get_at_id, get_name
from .model import GameManager


@register(
    "astrbot_plugin_roulette",
    "Zhalslar",
    "俄罗斯转盘赌，中枪者禁言",
    "1.0.1"
)
class RoulettePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 游戏管理器
        self.gm = GameManager()
        # 禁言时间范围
        self.ban_duration: list[int] = [
            int(x) for x in config.get("ban_duration_str", "30-300").split("-")
        ]
        # 禁言劝诫语录
        self.PERSUASION_QUOTES: list = [
            "赌博一时爽，一直赌博一直爽，但最后爽的只有赌场老板！",
            "别再赌了，回头是岸！",
            "赌博是无底洞，早回头早安心。",
            "赌一时，悔一世！",
            "别让赌博毁了你的未来！",
            "赌博是毒药，沾染不得！",
            "别再赌了，你的家人需要你！",
            "别让赌博成为你人生的绊脚石！",
            "小赌怡情，大赌伤身，强赌灰飞烟灭",
            "赌狗赌到最后一无所有，你确定要继续吗？",
            "十赌九输，清醒点",
            "'赌'字上'贝'下'者'，'贝者'即背着债务的人",
            "常在河边走，哪有不湿鞋?",
            "赌博之害，你岂能不知",
            "一次戒赌，终生受益",
            "手握一手好牌，切莫做那糊涂的赌徒",
            "听我一言，捷径虽诱人，赌路却凶险，慎行",
            "放手一搏,不如稳健前行",
        ]

    @filter.command("转盘", alias={"轮盘", "开启转盘"})
    async def start_wheel(self, event: AstrMessageEvent):
        """转盘@某人 不@表示进入多人模式"""
        args = event.message_str.split()
        duration = (
            int(args[-1]) if args[-1].isdigit() else random.randint(*self.ban_duration)
        )

        target_id = get_at_id(event)
        sender_id = event.get_sender_id()
        group_id = event.get_group_id()

        if sender_id == target_id:
            yield event.plain_result("不能和自己玩哦！")
            return

        kids = [sender_id, target_id, group_id]
        room = self.gm.create_room(kids=kids, ban_time=duration)
        if not room:
            reply = ""
            if self.gm.has_room(sender_id):
                reply = "你在游戏中..."
            if self.gm.has_room(target_id):
                reply = "对方游戏中..."
            if self.gm.has_room(group_id):
                reply = "本群游戏中..."
            yield event.plain_result(reply)
            return

        # 开盘提示
        if room.players:
            user_name = await get_name(event, sender_id)
            target_name = await get_name(event, target_id) if target_id else ""
            yield event.plain_result(f"{user_name} VS {target_name}, 请开枪")
        else:
            yield event.plain_result("本群转盘开始，请开枪！")
        logger.info(
            f"转盘游戏创建成功：子弹在第{room.bullet}轮，禁言时长为{room.ban_time}秒"
        )
        return

    @filter.command("开枪")
    async def shoot_wheel(self, event: AstrMessageEvent):
        reply = ""
        target_id = ""
        sender_id = event.get_sender_id()
        group_id = event.get_group_id()
        kids = [sender_id, target_id, group_id]

        room =self.gm.get_room(kids)
        if not room:
            yield event.plain_result("请先开启转盘")
            return

        if not room.can_shoot(sender_id):
            yield event.plain_result("本轮不是你的回合")
            return

        user_name = await get_name(event, sender_id)

        if room.shoot(sender_id):
            await ban(event, room.ban_time)
            reply = f"Bang！{user_name}被禁言{room.ban_time}秒！{random.choice(self.PERSUASION_QUOTES)}"
            self.gm.del_room(kids)
        else:
            reply = f"【{user_name}】开了一枪没响，还剩【{6 - room.round}】发"
            if room.next_idx is not None:
                player_name = await get_name(event, user_id=room.players[room.next_idx])
                reply += f", {player_name}，该你了！"

        yield event.plain_result(reply)


    @filter.command("认输", alias={"玩不起", "结束游戏"})
    async def quit_game(self, event: AstrMessageEvent):
        """处理退出游戏命令"""
        user_id = event.get_sender_id()
        if not self.gm.has_room(user_id):
            yield event.plain_result("你没有正在进行的转盘游戏")
        else:
            self.gm.del_room(kids=[user_id])
            yield event.plain_result("已退出游戏")
