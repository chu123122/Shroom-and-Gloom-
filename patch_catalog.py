# -*- coding: utf-8 -*-
"""修正 catalog.json 里中文 bundle 的 CRC，使补丁包能通过 Addressables 的校验。

背景：
    Addressables 对本地 bundle 同样会调用 AssetBundle.LoadFromFile(path, crc, offset)，
    crc 取自 catalog 里该 bundle 的 AssetBundleRequestOptions.m_Crc。
    替换 bundle 后文件内容变了，CRC 不再匹配，Unity 会拒绝加载：
        CRC Mismatch. Provided 2da1151c, calculated dfbb94ae from data. Will not load AssetBundle ...
    结果 zh-Hans 字符串表全部加载失败，界面整体回退英文。

做法：
    m_ExtraDataString 是 base64 的二进制块（长度前缀 + UTF-16LE 字符串混合），
    条目之间靠**字节偏移**互相引用，所以改动必须**保持字节长度完全一致**。
    这里把 `"m_Crc":765531420`（17 字符）替换成 `"m_Crc":0` + 8 个空格（同样 17 字符）。
    JSON 允许数值后跟空白，长度不变 → 偏移不移动。
    crc=0 时 Unity 跳过校验。
"""
import os, json, base64, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("SG_GAME_DIR",
    r"D:/SteamLibrary/steamapps/common/Shroom and Gloom")
CATALOG = os.path.join(GAME, "Shroom and Gloom_Data", "StreamingAssets", "aa", "catalog.json")

ORIG_CRC = 765531420          # 原中文包 CRC（0x2da1151c），替换后不再匹配
BUNDLE_SIZE_MARK = '"m_BundleSize":54938'   # 用于定位中文包那一条 options

def u16(s):
    # catalog 里的 JSON 字符串实测为 UTF-16BE
    return s.encode("utf-16-be")

def patch(data: bytes) -> bytes:
    # 定位中文包那一条 AssetBundleRequestOptions（用 m_BundleSize 作锚点）
    marker = u16(BUNDLE_SIZE_MARK)
    pos = data.find(marker)
    assert pos >= 0, "没找到中文包的 options（m_BundleSize 标记不存在）"
    assert data.find(marker, pos + 1) < 0, "中文包 options 标记不唯一"

    # 在同一条 options 内回退查找 m_Crc
    old = u16('"m_Crc":%d' % ORIG_CRC)
    start = data.rfind(old, 0, pos)
    assert start >= 0, "在中文包 options 内没找到 m_Crc"
    assert data.find(old, start + 1, pos) < 0, "该 options 内 m_Crc 出现多次"

    digits = str(ORIG_CRC)
    # crc=0 时 Unity 跳过校验；用空格补齐到原长度，保证后续偏移不移动
    new = u16('"m_Crc":0' + " " * (len(digits) - 1))
    assert len(new) == len(old), "替换串长度必须一致"
    return data[:start] + new + data[start + len(old):]

def main():
    text = open(CATALOG, encoding="utf-8").read()
    extra = base64.b64decode(json.loads(text)["m_ExtraDataString"])
    fixed = patch(extra)
    assert len(fixed) == len(extra), "extra 数据长度改变了：%d -> %d" % (len(extra), len(fixed))

    # 校验：解析出来确实变了、且只变了这一处
    before = extra.decode("utf-16-be", errors="replace")
    after = fixed.decode("utf-16-be", errors="replace")
    assert before.count('"m_Crc":%d' % ORIG_CRC) == 1
    assert after.count('"m_Crc":%d' % ORIG_CRC) == 0
    assert after.count('"m_Crc":0 ') == 1, "应恰好出现一次"
    # 改完的 JSON 仍可逐条解析
    for m in re.finditer(r'\{"m_Hash".*?\}', after):
        json.loads(m.group(0))

    # 只替换 base64 串本身，文件其余部分逐字节不动（base64 长度不变 → 文件长度也不变）
    old_b64 = base64.b64encode(extra).decode("ascii")
    new_b64 = base64.b64encode(fixed).decode("ascii")
    assert len(old_b64) == len(new_b64), "base64 长度必须一致"
    assert text.count(old_b64) == 1, "base64 串应恰好出现一次"
    out_text = text.replace(old_b64, new_b64)
    assert len(out_text) == len(text), "文件长度必须一致"

    out = os.path.join(HERE, "patched", "catalog.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="").write(out_text)
    print("原始 extra: %d 字节 -> 补丁 %d 字节（长度一致）" % (len(extra), len(fixed)))
    print("catalog.json: %d 字节 -> %d 字节（长度一致，仅 base64 串被替换）"
          % (len(text), len(out_text)))
    print("中文包 m_Crc: %d -> 0" % ORIG_CRC)

if __name__ == "__main__":
    sys.exit(main())
