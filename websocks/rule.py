import os
import re
import base64
import typing
from urllib import request

IPV4_PATTERN = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

gfwlist_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'gfwlist.txt'
)

cache: set = set()


def is_ipv4(host: str) -> bool:
    """判断 host 是否为 IPV4 地址"""
    return IPV4_PATTERN.match(host) is not None


def is_local_ipv4(host: str) -> bool:
    if host.startswith("10.") or host.startswith("127."):
        # A类地址
        return True
    if host.startswith("169.254.") or \
            (host.startswith("172.") and 16 <= int(host.split(".")[1]) <= 31):
        # B类地址
        return True
    if host.startswith("192.168."):
        # C类地址
        return True
    return False


class FilterRule:

    def __init__(self) -> None:
        self.gfwlist_file = open(gfwlist_path)

    @staticmethod
    def download(url: str = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt") -> None:
        req = request.Request(url, method="GET")
        resp = request.urlopen(req)
        with open(gfwlist_path, 'wb+') as file:
            base64.decode(resp, file)

    def judge(self, host: str) -> typing.Optional[bool]:
        """
        匹配例外则返回 False, 匹配成功则返回 True.
        不在规则内返回 None.

        匹配一次大约 0.1 秒
        """
        self.gfwlist_file.seek(0, 0)
        while True:
            line = self.gfwlist_file.readline()
            if not line:
                return
            line = line.strip()
            if not line:
                continue
            result = self._judge(line, host)
            if result is not None:
                return result
        self.gfwlist_file.seek(0, 0)

    def _judge(self, line: str, host: str) -> typing.Optional[bool]:
        if line.startswith("!"):
            return None
        if line.startswith("||"):
            if host.startswith(line[2:]):
                return True
        elif line.startswith("|"):
            # 由于是 host 匹配, 所以暂不需要配置此种规则
            return None
        elif line[0] in ("*", "."):
            if host.endswith(line[1:]):
                return True
        elif line[0] == "/" and line[-1] == "/":
            if re.search(line[1:-1], host):
                return True
        elif line.startswith("@@"):
            _ = self._judge(line[2:], host)
            if _ is not None:
                return not _
        else:
            if host.startswith(line):
                return True


gfwlist = FilterRule()


def judge(host: str) -> typing.Optional[bool]:
    """检查是否需要走代理"""
    if is_ipv4(host):
        return not is_local_ipv4(host)

    if host in cache:
        return True

    result = gfwlist.judge(host)
    if result is True:
        cache.add(host)
    return result


def add(host: str) -> None:
    """增加新的 host 进加速名单"""
    cache.add(host)


if __name__ == "__main__":
    gfwlist.download()