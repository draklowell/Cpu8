from simulator.base import WaveformChunk


class Waveform:
    chunks: list[WaveformChunk]
    component_pin_networks: dict[str, dict[str, str]]
    component_pin_aliases: dict[str, list[tuple[str, str]]]

    def __init__(
        self,
        chunks: list[WaveformChunk],
        component_pin_networks: dict[str, dict[str, str]],
        component_pin_aliases: dict[str, list[tuple[str, str]]],
    ):
        self.chunks = chunks
        self.component_pin_networks = component_pin_networks
        self.component_pin_aliases = component_pin_aliases

    def add_chunk(self, chunk: WaveformChunk):
        self.chunks.append(chunk)

    def get_chunk(self, index: int) -> WaveformChunk:
        return self.chunks[index]

    @classmethod
    def from_file(cls, path: str) -> "Waveform":
        # TODO
        pass

    def to_file(self, path: str) -> None:
        # TODO
        pass
