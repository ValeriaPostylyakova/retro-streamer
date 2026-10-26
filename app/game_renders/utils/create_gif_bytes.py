import io

import imageio


def create_gif_bytes(frames: list, fps: int = 5) -> bytes:
    with io.BytesIO() as gif_io:
        imageio.mimsave(gif_io, frames, format="GIF", fps=fps, loop=0)
        return gif_io.getvalue()
