# here lieth ids
from dataclasses import dataclass


@dataclass
class ChannelBinding:
    name: str
    id: int


narrator = ChannelBinding("Narrator", 582988116135116809)
medrish = ChannelBinding("Medrish", 583037635975708672)
sevart = ChannelBinding("Sevart", 583037677692125216)
theobald = ChannelBinding("Theobald", 583037720440602624)

all_player_bindings = [
    sevart,
    theobald,
    medrish,
    narrator
]
