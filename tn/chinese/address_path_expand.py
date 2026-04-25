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

"""在 TN 之前将 http(s):// 与 Windows 盘符路径整段替换为口语读法（冒号、斜杠、IP 逐位等）。"""

from __future__ import annotations

import re

_ZH_DIGIT = "零一二三四五六七八九"


def _ascii_digit(ch: str) -> str | None:
    if "0" <= ch <= "9":
        return ch
    o = ord(ch)
    if 0xFF10 <= o <= 0xFF19:
        return str(o - 0xFF10)
    return None


def _digits_seq(s: str) -> str:
    out = []
    for ch in s:
        d = _ascii_digit(ch)
        if d is None:
            continue
        out.append(_ZH_DIGIT[int(d)])
    return "".join(out)


def _small_zh_digit(d: str) -> str:
    x = _ascii_digit(d)
    if x is None:
        return d
    return _ZH_DIGIT[int(x)]


def _ipv4_zh(host: str) -> str:
    parts = host.split(".")
    if len(parts) != 4:
        return host
    for p in parts:
        if not p or not all(_ascii_digit(c) is not None for c in p):
            return host
        v = int("".join(_ascii_digit(c) for c in p))
        if v > 255:
            return host
    return "点".join(_digits_seq(p) for p in parts)


def _split_host_port(authority: str) -> tuple[str, str | None]:
    if not authority:
        return "", None
    if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", authority):
        return authority, None
    if ":" in authority:
        i = authority.rfind(":")
        host, port = authority[:i], authority[i + 1 :]
        if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", host) and port.isdigit():
            return host, port
    return authority, None


def _verbalize_http_url(url: str) -> str:
    m = re.fullmatch(r"(https?)(://)([^/\s，。；]+)(/.*)?", url, flags=re.IGNORECASE)
    if not m:
        return url
    proto, _, authority, tail = m.group(1), m.group(2), m.group(3), m.group(4) or ""
    proto = proto.lower()
    out = [proto, "冒号", "斜杠", "斜杠"]
    host, port = _split_host_port(authority)
    if host and re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", host):
        out.append(_ipv4_zh(host))
    else:
        out.append(authority.replace(":", "冒号").replace(".", "点"))
    if port is not None:
        out.append("冒号")
        out.append(_digits_seq(port))
    if tail and tail != "/":
        out.append("斜杠")
        out.append(tail.lstrip("/").replace("/", "斜杠"))
    return "".join(out)


def _verbalize_win_path(path: str) -> str:
    if len(path) < 3 or path[1] != ":" or path[2] not in "\\/":
        return path
    drive = path[0].upper()
    body = path[3:].replace("/", "\\")
    parts = [p for p in body.split("\\") if p != ""]
    out = [drive, "冒号", "斜杠"]
    first = True
    for p in parts:
        if not first:
            out.append("斜杠")
        first = False
        if all(_ascii_digit(c) is not None for c in p):
            out.append(_digits_seq(p))
            continue
        m = re.fullmatch(r"(.+?)_v(\d+)\.(\d+)\.([A-Za-z0-9]+)", p)
        if m:
            pre, a, b, ext = m.groups()
            frac = "".join(_small_zh_digit(x) for x in b)
            out.append(f"{pre}_v{_small_zh_digit(a)}点{frac}{ext}")
            continue
        out.append(p)
    return "".join(out)


_RE_URL = re.compile(r"https?://[^\s，。；]+", flags=re.IGNORECASE)
_RE_WIN_PATH = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]):\\(?:[^，。\r\n]+?)(?=[，。\s]|$)")


def expand_address_path_spans(text: str) -> str:
    if not text:
        return text

    def repl_url(m: re.Match[str]) -> str:
        return _verbalize_http_url(m.group(0))

    text = _RE_URL.sub(repl_url, text)

    def repl_win(m: re.Match[str]) -> str:
        return _verbalize_win_path(m.group(0).rstrip())

    text = _RE_WIN_PATH.sub(repl_win, text)
    return text
