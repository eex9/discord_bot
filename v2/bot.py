import discord
from discord.ext import commands
import asyncio
import responses
from inventories import inventories
from console import console

class Bot(discord.Client):
    def __init__(self, intents:discord.Intents):
        super().__init__(intents=intents)
        self.starting_mode = "CONSOLE"
        self.modes:tuple = ("ACTIVE", "CONSOLE", "STANDBY", "TESTING", "HYBRID")
        self.console_modes:tuple = ("CONSOLE", "HYBRID")
        self.mode:str = self.starting_mode
        self.ignore_errors:bool = True
        self.author:discord.User
        self.last_sent_message:discord.Message

    async def on_ready(self):
        self.author = await self.fetch_user(630837649963483179)
        if self.mode == "TESTING":
            self.ignore_errors = True
        await self.change_presence(activity=discord.Game("with code"))
        print(f"{self.user} is now running!")

    async def send_dm(self, user:discord.User, content:str) -> None:
        channel = await user.create_dm()
        await channel.send(content)
    
    async def on_error(self, event:str, *args, **kwargs):
        import sys
        extype, ex, trace = sys.exc_info()
        print(f"{extype.__name__} exception in {event}: {ex}\n{trace}")
        await self.send_dm(self.author, f"{extype.__name__} exception in {event}: {ex}\n{trace}")
        if self.ignore_errors:
            return
        print("Entering Standby mode...")
        await self.send_dm(self.author, "Entering Standby mode...")
        self.mode = self.modes[2]
    
    def switch_mode(self, mode) -> None:
        if mode not in self.modes:
            raise TypeError(f"Mode not found in mode list: {mode}")
        print(f"Switching to mode {mode}")
        self.mode = mode
    
    def verify_mode(self, server:int, channel:int, user:int) -> bool:
        restricted:bool = channel == 1041508830279905280 or server == 677632068041310208 or user == 630837649963483179
        match self.mode:
            case "ACTIVE":
                return True
            case "CONSOLE":
                return restricted
            case "HYBRID":
                return True
            case "STANDBY":
                return restricted
            case "TESTING":
                return restricted
    
    async def handle_response(self, response:list[dict]|None, channel:discord.TextChannel) -> None:
        if response is None:
            return
        for item in response:
            if not item or item is None:
                continue
            match item.get("type", None):
                case "message":
                    self.last_sent_message = await channel.send(item.get("message","No message provided"), embed=item.get("embed", None))
                    print(f"Said {item.get('message','No message provided')} in {channel.name} in {channel.guild.name}")
                case "reply":
                    await channel.send(item.get("message","No message provided"), reference=item.get("reply"), embed=item.get("embed", None))
                    print(f"Replied to {item.get('reply').content} with {item.get('message','No message provided')} in {channel.name} in {channel.guild.name}")
                case "react":
                    message:discord.Message = item.get("message", self.last_sent_message)
                    if type(item.get("react")) == discord.PartialEmoji:
                        await message.add_reaction(item.get("react"))
                    else:
                        for char in item.get("react"):
                            await message.add_reaction(char)
                    print(f"Reacted to {message.content} (by {message.author}) in {message.channel} in {message.channel.guild} with {item.get('react')}")
                case "role":
                    try:
                        role = channel.guild.get_role(int(item.get("role").strip("@&<>")))
                        user = await channel.guild.fetch_member(int(item.get("user").strip("@<>")))
                        if user is None:
                            await channel.send("No user found!")
                        await user.add_roles(role)
                        await channel.send(f"Added role with ID {role.id} to user <@{user.id}>")
                    except discord.errors.PrivilegedIntentsRequired:
                        await channel.send("You do not have permission to add roles to users")
                    except ValueError:
                        await channel.send("That is not a valid ID!")
                case "wait":
                    print(f"Sleeping for {item.get('time', 0)} seconds...")
                    await asyncio.sleep(item.get("time"))
                case "store":
                    path = item.get("path")
                    store = item.get("extra")
                    store["id"] = self.last_sent_message.id
                    inventories.add_meta(item.get("id"), item.get("name"), store)
                case "error":
                    error = item.get("error")
                    print(f"Raising error {error}")
                    raise error
                case "mode":
                    self.switch_mode(item.get("mode"))
                case "call":
                    response += await item.get("call")()
                case None:
                    raise TypeError("No type provided for response")
                case _:
                    raise TypeError("Unexpected type for response")
    
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):

        server:discord.Guild = await self.fetch_guild(payload.guild_id)
        channel = await self.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user:discord.User = await server.fetch_member(int(payload.user_id))

        # Don't respond to our own reacts
        if user == self.user:
            return

        emoji = payload.emoji
        print(message.reactions)
        count = discord.utils.get(message.reactions, emoji=emoji.name).count
        username = user.name
        
        # Print to console
        print(f"{username} ({user.id}) reacted to {message.content} (by {message.author}) with {emoji} in #{channel} in {server}")

        if not self.verify_mode(server.id, channel.id, user.id):
            return False

        response = responses.handle_react(message, emoji, count, channel.id, user.id, server.id)
        print(response)
        await self.handle_response(response, channel)
        return True

    async def on_message(self, message:discord.Message):
        # Don't respond to our own messages
        if message.author == self.user:
            return

        # Get data from the message
        username = str(message.author)
        content = str(message.content)
        channel = message.channel
        channel_id = channel.id
        server = message.guild
        if server is not None:
            server_id = int(message.guild.id)
        else:
            server_id = -1
        user_id = int(message.author.id)

        # Print to console
        print(f"{username}/{message.author.nick} ({user_id}) said {content} in #{channel} in {server}")

        if not self.verify_mode(server_id, channel_id, user_id):
            return False

        response = responses.handle_message(message, content, channel_id, user_id, server_id)
        await self.handle_response(response, channel)

        return True

    def startup(self) -> None:
        with open("meta/TOKEN.txt", "r") as token:
            TOKEN = token.readline().strip()
        async def run():
            discord.utils.setup_logging(root=False)
            await asyncio.gather(
                self.start(TOKEN),
                console.run(self)
            )
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            print("\nGoodbye!")
        
if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    eclipse = Bot(intents=intents)
    eclipse.startup()