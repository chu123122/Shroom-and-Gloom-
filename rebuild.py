# -*- coding: utf-8 -*-
"""StringTable 定位 + 严格解析 + 重序列化（带字节级往返自测）。

对象布局: 固定头 + m_Name(str) + m_TableCollectionName(str) + 前导块 + count(int32) + count*(int64 id, str value)
前导块长度因对象而异，用「严格解析恰好吃掉整个对象」来定位，不硬编码偏移。
"""
import os, struct

def align4(n): return (n + 3) & ~3

def read_str(b, o):
    if o + 4 > len(b): return None, o
    n = struct.unpack_from("<I", b, o)[0]
    if o + 4 + n > len(b): return None, o
    try: s = b[o+4:o+4+n].decode("utf-8")
    except UnicodeDecodeError: return None, o
    if any(ord(c) < 32 and c not in "\n\r\t" for c in s): return None, o
    return s, o + align4(4 + n)

def write_str(s):
    data = s.encode("utf-8")
    out = struct.pack("<I", len(data)) + data
    return out + b"\x00" * (align4(len(out)) - len(out))

META_ITEM_SIZE = 8   # 每个元数据项固定 8 字节，原样保留不解释其语义

def parse_entries(raw, start, count):
    """严格解析 count 条。每条 = int64 id + string value + int32 metaCount + metaCount*8 字节元数据。
    返回 (entries, end_off) 或 (None, None)。entries 元素为 (id, value, meta_blob)。"""
    entries, off = [], start
    for _ in range(count):
        if off + 8 > len(raw): return None, None
        eid = struct.unpack_from("<q", raw, off)[0]
        s, nxt = read_str(raw, off + 8)
        if s is None: return None, None
        if nxt + 4 > len(raw): return None, None
        mc = struct.unpack_from("<i", raw, nxt)[0]
        if not (0 <= mc <= 64): return None, None
        end = nxt + 4 + mc * META_ITEM_SIZE
        if end > len(raw): return None, None
        entries.append((eid, s, raw[nxt:end])); off = end
    return entries, off

def locate(raw, max_tail=64):
    """返回 (name, coll, entries_start, entries, end_off) 或 None"""
    # m_Name
    name = coll = None; o1 = None
    for off in range(20, 40, 4):
        s, n = read_str(raw, off)
        if s: name, o1 = s, n; break
    if name is None: return None
    s, o2 = read_str(raw, o1)
    if s is None: return None
    coll = s
    # 固定布局: 表名之后 12 字节 PPtr + 4 + 8 = 24, 然后 count
    start = o2 + 24
    if start + 4 > len(raw): return None
    count = struct.unpack_from("<i", raw, start)[0]
    if not (0 <= count <= 50000): return None
    entries, end = parse_entries(raw, start + 4, count)
    if entries is None: return None
    return name, coll, start, entries, end

def build(prefix, entries, suffix=b""):
    out = bytearray(prefix)
    for eid, val, meta in entries:
        out += struct.pack("<q", eid) + write_str(val) + meta
    out += suffix
    return bytes(out)

if __name__ == "__main__":
    import UnityPy
    BASE = r"D:/SteamLibrary/steamapps/common/Shroom and Gloom/Shroom and Gloom_Data/StreamingAssets/aa/StandaloneWindows64"
    for fn in ["localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle",
               "localization-string-tables-english(en)_assets_all.bundle"]:
        print("=" * 66); print(fn)
        env = UnityPy.load(os.path.join(BASE, fn))
        for o in env.objects:
            if str(o.type) != "114": continue
            raw = o.get_raw_data()
            r = locate(raw)
            if r is None:
                print("  LOCATE FAIL pathid=%d len=%d" % (o.path_id, len(raw))); continue
            name, coll, start, entries, end = r
            prefix = raw[:start + 4]          # 含 count
            suffix = raw[end:]
            rebuilt = build(prefix, entries, suffix)
            print("  %-22s coll=%-8s start=%3d count=%4d tail=%d roundtrip=%s"
                  % (name, coll, start, len(entries), len(suffix),
                     "OK" if rebuilt == raw else "FAIL(%d vs %d)" % (len(raw), len(rebuilt))))
