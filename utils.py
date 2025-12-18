
from astrbot.core.message.components import At
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


async def get_name(event: AstrMessageEvent, user_id: str|int) -> str:
    """获取指定群友的昵称"""
    if event.get_platform_name() == "aiocqhttp" and str(user_id).isdigit():
        assert isinstance(event, AiocqhttpMessageEvent)
        group_id = event.get_group_id()
        if group_id:
            member_info = await event.bot.get_group_member_info(
                group_id=int(group_id), user_id=int(user_id)
            )
            nickname = member_info.get("card") or member_info.get("nickname")
            return nickname.strip() or str(user_id)
        else:
            stranger_info = await event.bot.get_stranger_info(user_id=int(user_id))
            return stranger_info.get("nickname") or str(user_id)
    else:
        return str(user_id)

def get_at_id(event: AstrMessageEvent) -> str:
    """获取@的 QQ 号"""
    return next(
        (
            str(seg.qq)
            for seg in event.get_messages()
            if (isinstance(seg, At)) and str(seg.qq) != event.get_self_id()
        ),
        "",
    )


async def ban(event: AstrMessageEvent, duration: int):
    if event.get_platform_name() == "aiocqhttp":
        assert isinstance(event, AiocqhttpMessageEvent)
        try:
            await event.bot.set_group_ban(
                group_id=int(event.get_group_id()),
                user_id=int(event.get_sender_id()),
                duration=duration,
            )
        except Exception:
            pass
