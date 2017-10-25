import discord
from discord.ext import commands

class welcome():
    def __init__(self, bot):
        self.bot = bot
        self.sessions = set()

    async def on_member_join(self, member):
        try:
            await member.send(
                '''Welcome to Kairos Kingdom!
                
You can only chat in a few channels now, to gain access in the rest of the channels, please ensure you have read the <#244125181746872320> and get a profile picture!

After you are done, type agree in <#244114075716419584> and you will be all ready to explore the server!

If you are from a Kairos Kingdom Clan, drop a message in <#287328907160715265> to get your roles settled!'''
            )
        except:
            pass

    async def on_message(self, message):
        if message.channel.id == 244114075716419584:
            if message.author.bot: return 
            #if message.author.bot and message.author.id != 372748944448552961: await message.delete()
            if message.content == 'agree':
                if message.author.avatar_url.startswith('https://cdn.discordapp.com/embed/avatars/'):
                    try:
                        await message.author.send('Please get a profile picture on discord first! You can refer to this support article: https://support.discordapp.com/hc/en-us/articles/204156688-How-do-I-change-my-avatar-')
                    except:
                        await discord.utils.get(message.guild.channels, id=244114075716419584).send(f'{message.author.mention}, please get a profile picture on discord first! You can refer to this support article: https://support.discordapp.com/hc/en-us/articles/204156688-How-do-I-change-my-avatar-')
                    return
                await message.author.add_roles(discord.utils.get(message.guild.roles, id=243812023085826048), discord.utils.get(message.guild.roles, id=337301153622654976), reason='Member said agree') #vg, cr
                await discord.utils.get(message.guild.channels, id=238743527515750400).send(f'Welcome {message.author.mention} to the Kairos Kingdom! Have fun! :)')
                await discord.utils.get(message.guild.channels, id=249608247697211392).send(embed=discord.Embed(title=f'{message.author} has been verified', description = f'User Verified', color=0xf1c40f))
                await message.channel.purge(limit=50, before=None, after=None, check=lambda e: e.author == message.author)
            else:
                try:
                    await message.author.send("Hello from the Kairos Kingdom Discord! Make sure you've read the rules in <#244125181746872320> and then type `agree` in the <#244114075716419584> channel so we know you've read them!")
                except:
                    await discord.utils.get(message.guild.channels, id=244114075716419584).send(f"Hello {message.author.mention} from the Kairos Kingdom Discord! Make sure you've read the rules in <#244125181746872320> and then type `agree` in the <#244114075716419584> channel so we know you've read them!")

def setup(bot):
    bot.add_cog(welcome(bot))
