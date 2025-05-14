
import random
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import At
from astrbot import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from .model import DuetGame, MultiGame

@register(
    "astrbot_plugin_roulette",
    "Zhalslar",
    "俄罗斯转盘赌，中枪者禁言",
    "1.0.0",
    "https://github.com/Zhalslar/astrbot_plugin_roulette",
)
class RoulettePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 双人游戏存储器
        self.duet_games: dict[str, DuetGame] = {}
        # 多人游戏存储器
        self.multi_games: dict[str, MultiGame] = {}
        # 禁言时间范围
        ban_duration: list[int] = [int(x) for x in config.get("ban_duration_str", "30-300").split("-")]
        self.min_duration: int = ban_duration[0]
        self.max_duration: int = ban_duration[1]
        # 禁言嘲讽语录
        self.BAN_ME_QUOTES: list = [
            "还真有人有这种奇怪的要求",
            "满足你",
            "静一会也挺好的",
            "是你自己要求的哈！",
            "行，你去静静",
            "好好好，禁了",
            "主人你没事吧？"
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
        # 空枪语录
        self.EMPTY_RESPONSES: list = [
            "第一枪空了！{target_nickname}，该你了！",
            "第二枪也空了！{target_nickname}，该你了！",
            "第三枪没响！{target_nickname}，该你了！",
            "第四枪还是没响！{target_nickname}，该你了！",
            "第五枪还是空的！{target_nickname}，该你了！",
            "第六枪还是空的！游戏结束！"
        ]


    async def get_nickname(
        self, event: AiocqhttpMessageEvent, user_id: str | int
    ) -> str:
        """获取指定群友的昵称"""
        client = event.bot
        group_id = event.get_group_id()
        all_info = await client.get_group_member_info(
            group_id=int(group_id), user_id=int(user_id)
        )
        nickname = all_info.get("card") or all_info.get("nickname")
        return nickname


    @filter.command("双人转盘")
    async def duet_wheel(self,event: AiocqhttpMessageEvent):
        """双人模式"""
        user_id = event.get_sender_id()
        target_id = next(
            (
                str(seg.qq)
                for seg in event.get_messages()
                if (isinstance(seg, At)) and str(seg.qq) != event.get_self_id()
            ),
            None,
        )
        if not target_id:
            yield event.plain_result("请@指定群友")
            return

        if user_id == target_id:
            yield event.plain_result("不能和自己玩哦！")
            return

        # 检查是否有正在进行的游戏
        for game in list(self.duet_games.values()):
            if user_id in game.players:
                yield event.plain_result("你有正在进行的游戏，请先发送“结束游戏”")
                return
            elif target_id in game.players:
                yield event.plain_result("对方在游戏中...")
                return

        # 创建新的游戏实例
        game = DuetGame(user_id, target_id)
        self.duet_games[game.id] = game

        player1_nick = await self.get_nickname(event, user_id)
        player2_nick = await self.get_nickname(event, target_id)
        yield event.plain_result(f"{player1_nick} VS {player2_nick}, 请开枪")
        logger.info(
            f"转盘游戏{game.id}创建成功：\n{player1_nick} VS {player2_nick}, \n子弹在第{game.bullet_position}轮"
        )


    @filter.command("认输", aliases={"玩不起", "结束游戏"})
    async def quit_game(self,event: AiocqhttpMessageEvent):
        """处理退出游戏命令"""
        user_id = event.get_sender_id()
        remove_id = None
        for game_id, game in list(self.duet_games.items()):
            if user_id in game.players:
                remove_id = game_id
                break
        if not remove_id:
            yield event.plain_result("你当前没有进行中的游戏")
        if remove_id:
            del self.duet_games[remove_id]
            yield event.plain_result("游戏已终止")


    @filter.command("多人转盘")
    async def multi_wheel(self, event: AiocqhttpMessageEvent):
        """多人模式"""

        group_id = event.get_group_id()

        game = MultiGame(group_id)
        self.multi_games[game.id] = game

        yield event.plain_result("本群俄罗斯轮盘已开启！\n弹夹有【6】发子弹,请开枪")
        logger.info(f"多人转盘游戏{game.id}创建成功\n子弹在第{game.bullet_position}轮")

    @filter.command("开枪")
    async def shoot(self, event: AiocqhttpMessageEvent):
        """处理开枪命令"""
        user_id = event.get_sender_id()
        group_id = event.get_group_id()

        # 查找参与的双人游戏
        if game := next((g for g in self.duet_games.values() if user_id in g.players), None):
            result = await self.duet_game_shoot(event, group_id, user_id, game)
            if result:
                yield event.plain_result(result)

        # 查找参与的多人游戏
        elif game := next((g for g in self.multi_games.values() if group_id == g.id), None):
            result = await self.multi_game_shoot(event, game)
            if result:
                yield event.plain_result(result)
        else:
            yield event.plain_result("你当前没有进行中的转盘游戏")


    async def duet_game_shoot(self, event: AiocqhttpMessageEvent, group_id: str, user_id: str, game: DuetGame) -> str | None:
        """处理双人游戏开枪"""
        if game.current_player_index and user_id != game.get_current_player():
            return "别急，对方局还没结束呢"

        if game.shoot(user_id):
            duration = random.randint(self.min_duration, self.max_duration)
            quote = random.choice(self.PERSUASION_QUOTES)
            del self.duet_games[game.id]
            await event.bot.set_group_ban(
                group_id=int(group_id), user_id=int(user_id), duration=duration
            )
            nickname = await self.get_nickname(event, user_id)
            return f"Bang！{nickname}被禁言{duration}秒！{quote}"

        elif game.current_player_index:
            current_nickname = await self.get_nickname(
                event, game.players[game.current_player_index]
            )
            response = self.EMPTY_RESPONSES[game.current_round - 1].format(
                target_nickname=current_nickname
            )
            return response

    async def multi_game_shoot(self, event: AiocqhttpMessageEvent, game: MultiGame) -> str | None:
        """处理多人游戏开枪"""
        user_id = event.get_sender_id()
        group_id = event.get_group_id()

        nickname = await self.get_nickname(event, user_id)

        if game.shoot():
            duration = random.randint(self.min_duration, self.max_duration)
            quote = random.choice(self.PERSUASION_QUOTES)
            del self.multi_games[game.id]
            await event.bot.set_group_ban(
                group_id=int(group_id), user_id=int(user_id), duration=duration
            )
            return f"Bang！{nickname}被禁言{duration}秒！{quote}"

        else:
            response = (
                f"【{nickname}】开了一枪，没响。\n还剩【{6 - game.current_round}】发子弹"
            )
            return response

