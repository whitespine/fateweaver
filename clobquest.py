from discord.ext import commands
import const
import pipettes


def check_channel_player(ctx):
    """Checks if a channel is in the venture"""
    return ctx.channel.id in (binding.id for binding in const.all_player_bindings)

def check_channel_admin(ctx):
    """Checks if a channel is the admin zone"""
    return ctx.channel.id == const.narrator.id

class Clobquest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Make spigots/spouts for each, keyed by player name
        self.player_ears = {}
        self.player_mouths = {}

        # Gen them
        for player in const.all_player_bindings:
            self.player_ears[player.name] = self.player_ear(player)
            self.player_mouths[player.name] = self.player_mouth(player)

        # Fit them all together sorta messy like
        self.all_pipe = pipettes.Pipe()
        self.all_pipe.set_outputs([spout for spout in self.player_ears.values()])
        for mouth in self.player_mouths.values():
            mouth.add_outputs(self.all_pipe)

    def player_ear(self, binding: const.ChannelBinding):
        """
        Makes a standardized "ear" for a player,
        including all the fixings such as language comprehension, distance handling, deafening, etc.
        :return:
        """
        final = pipettes.ChannelOutput(self.bot, binding.id)

        # Filter out messages we sent out
        # self_filter = pipettes.PredicatePipe(lambda m: m.origin_channel.id != binding.id)
        return final

    def player_mouth(self, binding: const.ChannelBinding):
        """
        Makes a standardized "mouth" for a player,
        including all the fixings such as currently spoken language, volume, curses, etc.
        :return:
        """
        base = pipettes.SpeakerSource(binding.name)
        return base

    # @commands.check(is_good_channel)
    @commands.command()
    @commands.check(check_channel_player)
    async def say(self, ctx, *, what: str):
        # Get the appropriate character spout
        for binding in const.all_player_bindings:
            if ctx.channel.id == binding.id:
                # This is our binding - find the mouthpiece for it
                mouth = self.player_mouths[binding.name]
                await mouth.process("says", what, ctx.channel)
                return

        # If we reach here, haven't found an appropriate character
        await ctx.channel.send("Unable to find an appropriate binding. Tell clobbo to fix things")
