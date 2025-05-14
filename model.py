import random
import uuid

class DuetGame:
    """双人轮盘赌游戏类，管理游戏状态和逻辑"""

    def __init__(self, player1: str, player2: str):
        """初始化游戏"""
        self.id = str(uuid.uuid4())  # 游戏ID
        self.players: list[str] = [player1, player2]  # 玩家列表（存储为整数）
        self.current_player_index: int | None = None  # 当前玩家索引（初始为None，表示尚未决定）
        self.bullet_position: int = random.randint(1, 6)  # 子弹位置随机设定在1到6之间
        self.current_round: int = 0  # 当前进行的轮数，初始化为0

    def get_current_player(self) -> str | None:
        """获取当前玩家的ID"""
        if self.current_player_index:
            return self.players[self.current_player_index]
        else:
            return None

    def shoot(self, shooter: str) -> bool:
        """开枪逻辑，判断本轮是否中弹"""

        # 如果是第一次射击，设置当前玩家索引
        if self.current_player_index is None:
            self.current_player_index = 0 if shooter == self.players[0] else 1

        self.current_round += 1 # 增加当前轮数
        self.current_player_index = 1 - self.current_player_index # 切换玩家
        return self.current_round == self.bullet_position  # 判断是否中弹



class MultiGame:
    """多人轮盘赌游戏类，管理游戏状态和逻辑"""

    def __init__(self, game_id: str):
        """初始化游戏"""
        self.id = game_id  # 游戏ID
        self.bullet_position = random.randint(1, 6)  # 子弹位置随机设定在1到6之间
        self.current_round = 0  # 当前进行的轮数，初始化为0

    def shoot(self) -> bool:
        """开枪逻辑，判断本轮是否中弹"""
        self.current_round += 1 # 增加当前轮数
        return self.current_round == self.bullet_position  # 判断是否中弹
