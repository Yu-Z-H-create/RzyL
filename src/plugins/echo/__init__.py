from nonebot import on_command, on_message
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg, EventType

'''
echo = on_message()
#echo = on_command("echo", priority=5)

@echo.handle()
async def handle_echo(id=Event.get_user_id, message=Event.get_message, type=EventType()):
    await echo.send(type)
    await echo.send(f"user id: {id}")

    await echo.send()
'''