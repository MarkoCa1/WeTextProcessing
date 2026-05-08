# Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""English weather temperature range preprocessing.

Converts common weather report notations into standard range format
that can be handled by existing Range + Measure rules:

- 24/13℃ → 24 to 13 ℃
- 25℃~29℃ → 25 to 29 ℃
- 25℃ ~ 29℃ (with spaces) → 25 to 29 ℃

This avoids FST state errors caused by malformed tokens in Measure.
"""

import re

# Matches patterns like: 24/13℃, 24/13 °C, 26/15℃
# Captures: (high) / (low) (unit)
_TEMP_SLASH = re.compile(
    r"(\d{1,2})\s*/\s*(\d{1,2})\s*(℃|℉|°C|°c|ºC|ºc|°C|°c)",
    flags=re.IGNORECASE,
)

# Matches patterns like: 25℃~29℃, 25℃ ~ 29℃, 25~29℃
# Captures: (low) (unit) ~ (high) (unit) or (low) ~ (high) (unit)
_TEMP_TILDE = re.compile(
    r"(\d{1,2})\s*(℃|℉|°C|°c|ºC|ºc)\s*~\s*(\d{1,2})\s*(℃|℉|°C|°c|ºC|ºc)",
    flags=re.IGNORECASE,
)

# Also handle "25℃ ~ 29℃" with explicit space around tilde
_TEMP_TILDE_SPACED = re.compile(
    r"(\d{1,2})\s*(℃|℉|°C|°c|ºC|ºc)\s+~\s+(\d{1,2})\s*(℃|℉|°C|°c|ºC|ºc)",
    flags=re.IGNORECASE,
)


def expand_weather_temp_ranges(text: str) -> str:
    """Expand weather temperature range notations.

    Examples:
        "24/13℃" → "24 to 13 ℃"
        "25℃~29℃" → "25 to 29 ℃"
        "Today: 26/15℃" → "Today: 26 to 15 ℃"
    """
    if not text:
        return text

    # 1. Handle slash notation: 24/13℃ → 24 to 13 ℃
    def repl_slash(m: re.Match) -> str:
        high, low, unit = m.group(1), m.group(2), m.group(3)
        return f"{high} to {low} {unit}"

    text = _TEMP_SLASH.sub(repl_slash, text)

    # 2. Handle tilde notation: 25℃~29℃ → 25 to 29 ℃
    def repl_tilde(m: re.Match) -> str:
        low, unit1, high, unit2 = m.group(1), m.group(2), m.group(3), m.group(4)
        # Prefer the first unit if they differ (rare)
        unit = unit1 if unit1 else unit2
        return f"{low} to {high} {unit}"

    text = _TEMP_TILDE.sub(repl_tilde, text)

    # 3. Handle spaced tilde: 25℃ ~ 29℃ → 25 to 29 ℃
    def repl_tilde_spaced(m: re.Match) -> str:
        low, unit1, high, unit2 = m.group(1), m.group(2), m.group(3), m.group(4)
        unit = unit1 if unit1 else unit2
        return f"{low} to {high} {unit}"

    text = _TEMP_TILDE_SPACED.sub(repl_tilde_spaced, text)

    return text
