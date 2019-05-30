from __future__ import annotations

from discord.ext import commands

import dice
import clobquest

# Make the bot
bot = commands.Bot(command_prefix='', description="uhhhhh")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def reload(ctx):
    """Reload cogs"""
    # Re import
    import importlib
    importlib.reload(dice)
    importlib.reload(clobquest)

    bot.remove_cog("DiceRoller")
    bot.add_cog(dice.DiceRoller(bot))
    bot.remove_cog("Clobquest")
    bot.add_cog(clobquest.Clobquest(bot))

    await ctx.send("Reloaded")


# Init the cog
bot.add_cog(dice.DiceRoller(bot))
bot.add_cog(clobquest.Clobquest(bot))

# Run the client
with open("token") as token_file:
    discord_token = token_file.read().strip()
bot.run(discord_token)
