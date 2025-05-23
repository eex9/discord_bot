import random
import discord
import math

from shop import shop
from inventories import inventories

with open("fishing/meta/fish.txt", "r") as fish_f:
    fish:list = [line.strip("\n") for line in fish_f.readlines()]

with open("fishing/meta/treasure.txt", "r") as treasure_f:
    treasure:list = [line.strip("\n") for line in treasure_f.readlines()]

def handle(command:list[str], user_id:int, username, message:discord.Message) -> list[dict]:
    print(command)
    if len(command) <= 2:
        return go_fish(user_id, username)
    match command[1]:
        case "inv":
            return [{"type":"message","message":"The inventory command has been permanently moved to >inv fish."}]
        case "sell":
            if len(command) <= 3:
                return [{"type":"message","message":"Sorry, I can't tell what fish you're trying to sell. Try >fish sell 1"}]
            try:
                return shop.sell_fish(user_id, (int(command[2])-1))
            except ValueError:
                return([{"type":"message","message":"Sorry, I can't tell what fish you're trying to sell. Try >fish sell 1"}])
        case _:
            return([{"type":"message","message":"Sorry, I don't recognize that subcommand."}])

def create_wait(user_id:int) -> list[dict]:
    reduction = inventories.get_fish_time_reduction(user_id)
    time = (7 - math.floor(reduction * .5))
    if time <= 0:
        return []
    return [{"type":"message", "message":"The waters are stirring..."}, {"type":"wait","time":time}]

def go_fish(user_id:int, username) -> list[dict]:
    response:list[dict] = create_wait(user_id)
    roll:float = random.random()
    roll += (inventories.get_total_fish_buffs(user_id) * .1)
    item:str

    print(roll)
    match (roll):
        case roll if roll >= .99:
            idx = random.randrange(0, len(treasure)-1)
            item = treasure[idx]
            item.replace("{{USERNAME}}", username)
        case roll if roll < .15:
            item = None
        case _:
            idx = random.randrange(0, len(fish)-1)
            item = fish[idx]
    if item is None:
        response.append({"type":"message","message":"Not even a nibble..."})
        return response
    inventories.add_fish_to_inventory(user_id, item)
    response.append({"type":"message","message":f"<@{user_id}> got a {item}!"})
    return response