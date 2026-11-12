from typing import Any

import numpy as np
from numpy.typing import NDArray


def apply_display_lut(image: NDArray[Any], minimum: float, maximum: float,
                      brightness: int = 50, contrast: int = 50,
                      ) -> NDArray[np.float32]:
    """
    Apply the segmentation viewer's display adjustments without changing raw pixels.
    """
    pixels = image.astype(np.float32)
    if maximum > minimum:
        pixels = np.clip((pixels - minimum) / (maximum - minimum), 0, 1)
    else:
        pixels = np.clip(pixels / 65535, 0, 1)
    pixels = np.clip(pixels + (brightness - 50) / 50 * 0.3, 0, 1)
    return np.clip((pixels - 0.5) * (contrast / 50) + 0.5, 0, 1)
