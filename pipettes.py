from __future__ import annotations

import copy
from typing import List, Union, Optional, Callable, Iterable

# Dummy superclass, for reasons
import character


class Plumbing:
    pass


class Source(Plumbing):
    """That which has outputs, and might send things to them"""

    def __init__(self):
        super().__init__()
        self.output: List[Intake] = []

    def add_outputs(self, output: Union[Intake, Iterable[Intake]]) -> None:
        """Add outputs to this pipe section"""
        # Force-fit to list
        if isinstance(output, Plumbing):
            output = [output]
        else:
            output = list(output)

        # Append it
        self.output = self.output + output

    def set_outputs(self, output: Union[Intake, Iterable[Intake]]) -> None:
        # Clear then set
        self.output = []
        self.add_outputs(output)

    def get_endpoints(self, stop_at_branches: bool = True) -> Iterable[Source]:
        """
        Traverses the tree of pipes and returns all endpoints, across all branches if allowed.
        It is advisable that this is used prior to connecting the big pieces.
        May just return self
        """
        if len(self.output) == 0 or (len(self.output) >= 2 and stop_at_branches):
            # This is the endpoint
            yield self
        else:
            for out in self.output:
                if isinstance(out, Source):
                    yield from out.get_endpoints(stop_at_branches)


class Intake(Plumbing):
    """That which has inputs (nebulously), and can in theory get things from them"""

    async def give(self, msg: character.Message) -> None:
        raise NotImplementedError()


class Pipe(Source, Intake):
    """Just passes stuff through unmolested"""

    async def give(self, msg: character.Message) -> None:
        msg_copy = copy.copy(msg)
        msg_copy = self.process(msg_copy)
        if msg_copy is not None:
            for out in self.output:
                await out.give(msg_copy)

    def process(self, msg: character.Message) -> Optional[character.Message]:
        return msg


class PredicatePipe(Pipe):
    def __init__(self, predicate: Callable[[character.Message], bool]):
        super().__init__()
        self.predicate = predicate

    def process(self, msg: character.Message):
        if self.predicate(msg):
            return msg


# Puts a message to a channel
class ChannelOutput(Intake):
    """
    Spouts a message into a channel proper

    The channel is lazily evaluated the first time a message needs to be sent
    """

    def __init__(self, client, channel_id):
        super().__init__()
        self.client = client
        self.channel_id = channel_id
        self.channel = None

    async def give(self, msg: character.Message) -> None:
        if self.channel is None:
            self.channel = self.client.get_channel(self.channel_id)
        if self.channel == msg.origin_channel:
            # Don't self-mirror messages
            return
        await self.channel.send("{0.speaker.name} {0.verb}: \"{0.sentence}\"".format(msg))


# Reads everything a player says in a channel, and pumps out appropriately prefixed messages
class SpeakerSource(Source):
    def __init__(self, character_name: str):
        super().__init__()
        self.name = character_name

    async def process(self, command, sentence, channel) -> None:
        # He speaks!
        msg = character.Message(sentence,
                                command,
                                character.get_character_by_name(self.name),
                                channel)

        for out in self.output:
            await out.give(msg)
