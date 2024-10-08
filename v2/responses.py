import random
import discord

from fishing import fish
from shop import shop

def handle_message(message: discord.Message, content:str, channel_id, user_id:int, server:int, **kwargs) -> list[dict]:
    if not content:
        return None
    m_list:list = content.split()
    m_list[0] = m_list[0].lower()
    m_list.append(content)
    response:list = []
    response += single_args_m(m_list[0], message, channel_id, user_id, server)
    response += multi_args_m(m_list, message, channel_id, user_id, server)
    response += message_responses(m_list, message, channel_id, user_id, server)
    return response

def single_args_m(command:str, message:discord.Message, channel_id:int, user_id:int, server:int) -> list[dict]:
    response:list = []
    match command:
        case '>test':
            response.append({"type": "message", "message": "Hello World!"})
        case '>test1':
            response.append({"type": "message", "message": "Hello World!"})

        case '>test2':
            response.append({"type": "message", "message": "Starting..."})
            response.append({"type": "wait", "time": 5})
            response.append({"type": "message", "message": "Finished!"})

        case '>test3':
            response.append({"type": "message", "message": "Okay!"})
            response.append({"type": "react", "react": "👍", "message":message})
        
        case '>test4':
            response.append({"type":"reply", "message":"Hello World!", "reply":message})
        case '>test5':
            embedVar = discord.Embed(title="Title", description="Desc", color=0x00ff00)
            embedVar.add_field(name="Field1", value="hi", inline=False)
            embedVar.add_field(name="Field2", value="hi2", inline=False)
            return([{"type":"message", "message":"", "embed":embedVar}])
        case ">test6":
            response.append({"type":"message","message":"Throwing exception and entering standby mode..."})
            response.append({"type":"error","error":Exception("Error for testing")})
    return response

def multi_args_m(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int) -> list[dict]:
    response:list = []
    match command:
        case command if command[0] == ">fish":
            response += fish.handle(command, user_id, str(message.author), message)
        case command if command[0] == ">shop":
            # if len(command) == 2:
            #     response += shop.read_shop(user_id, "test")
            # else:
            #     response += shop.read_shop(user_id, command[1])
            response += shop.read_shop(user_id, "test")
        case command if command[0] == ">mode":
            if user_id != 630837649963483179:
                return
            response += [{"type":"mode","mode":command[1].upper()},{"type":"message","message":f"Switching to {command[1].upper()} mode..."}]           
    return response

def message_responses(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int) -> list[dict]:
    response:list = []
    return response

def handle_react(message:discord.Message, emoji:discord.PartialEmoji, count, channel_id:int, user_id:int, server:int) -> list[dict]:
    if not emoji:
        return None
    
    response = []
    response += make_sale(message, emoji, channel_id, user_id, server)

    return response


def make_sale(message:discord.Message, emoji:discord.PartialEmoji, channel_id, user_id, server) -> list[dict]:
    if not shop.is_sale(user_id, message.id):
        return []
    
    if emoji == "❎":
        return []