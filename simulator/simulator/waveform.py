from simulator.base import WaveformChunk


class Waveform:
    chunks: list[WaveformChunk]
    component_pins: dict[str, dict[str, str]]

    def __init__(
        self,
        chunks: list[WaveformChunk],
        component_pins: dict[str, dict[str, str]],
    ):
        self.chunks = chunks
        self.component_pins = component_pins

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
