import random
import threading


class Room:
    """内部房间类，不对外暴露 room_id"""

    def __init__(self, players: list[str], ban_time:int):
        self.players = players
        self.ban_time = ban_time
        self.bullet = random.randint(1, 6)
        self.round = 0
        self.next_idx: int | None = None  # 仅用于固定玩家列表

    @property
    def over(self) -> bool:
        return self.round >= self.bullet


    def can_shoot(self, shooter: str):
        if self.players and isinstance(self.next_idx, int):
            return shooter == self.players[self.next_idx]
        return True # 多人模式默认都可以射击

    def shoot(self, shooter: str) -> bool:
        if self.over:
            return False

        # 无限制模式
        if not self.players:
            self.round += 1
            return self.round == self.bullet

        # 固定玩家列表
        if shooter not in self.players:
            return False

        # 首枪决定先手
        if self.next_idx is None:
            self.next_idx = self.players.index(shooter)
        # 判断本轮枪手
        elif not self.can_shoot(shooter):
            return False

        self.round += 1
        # 切换枪手
        self.next_idx = 1 - self.next_idx

        return self.round == self.bullet


class GameManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.room: dict[str, Room] = {}  # player_id -> room 实例


    def create_room(
        self, kids: list[str], ban_time: int = 0
    ) -> Room | None:
        """创建房间"""
        with self._lock:
            for kid in kids:
                if kid in self.room:
                    return None
            if kids[0] and kids[1]:  # 固定列表
                room = Room(players=kids[:2], ban_time=ban_time)
                self.room[kids[0]] = room
                self.room[kids[1]] = room
                return room
            elif kids[2]:
                # 多人模式
                room = Room(players=[], ban_time=ban_time)
                self.room[kids[2]] = room
                return room


    def get_room(self, kids: list[str]) -> Room | None:
        """获取房间"""
        with self._lock:
            for kid in kids:
                if room := self.room.get(kid):
                    return room
            return None


    def has_room(self, kid: str) -> bool:
        """玩家是否已在房间"""
        with self._lock:
            return kid in self.room

    def del_room(self, kids: list[str]):
        """即销毁房间"""
        with self._lock:
            for kid in kids:
                if kid in self.room:
                    self.room.pop(kid)






