# -*- coding: utf-8 -*-
"""把 translations.json 的 65 条译文写进中文 StringTable，输出补丁后的 bundle 到工作区。
不修改游戏目录。完成后回读校验。
"""
import os, json, struct, shutil
import UnityPy
from rebuild import read_str, parse_entries, build

GAME = r"D:/SteamLibrary/steamapps/common/Shroom and Gloom/Shroom and Gloom_Data/StreamingAssets/aa/StandaloneWindows64"
WORK = os.path.dirname(os.path.abspath(__file__))
BUNDLE = "localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle"
# 始终以「未修改的原始包」为源：优先用 backup/，否则用游戏目录。
# 这样装上补丁后仍可反复重新构建（否则会把已打的补丁当成原始数据）。
_backup = os.path.join(WORK, "backup", BUNDLE)
SRC = _backup if os.path.exists(_backup) else os.path.join(GAME, BUNDLE)
print("源文件:", SRC, "(备份)" if SRC == _backup else "(游戏目录)")
OUTDIR = os.path.join(WORK, "patched")
os.makedirs(OUTDIR, exist_ok=True)
OUTPATH = os.path.join(OUTDIR, BUNDLE)

T = json.load(open(os.path.join(WORK, "translations.json"), encoding="utf-8"))

# ---- 从 shared bundle 构建 {表名: {entry_id: key}} ----
def parse_shared(raw):
    """SharedTableData: m_Name, m_TableCollectionName, guid, count, 之后为 (int64 id, string key) 序列。
    这里用带重同步的扫描提取，取前 count 条（该方法产出的 id 已与英文表 id 交叉验证过）。"""
    name = None
    for off in range(20, 40, 4):
        s, n = read_str(raw, off)
        if s: name, o1 = s, n; break
    coll, o2 = read_str(raw, o1)
    guid, o3 = read_str(raw, o2)
    count = struct.unpack_from("<i", raw, o3)[0]
    out, off = {}, o3 + 4
    while off + 12 <= len(raw) and len(out) < count:
        eid = struct.unpack_from("<q", raw, off)[0]
        s, nxt = read_str(raw, off + 8)
        if s is None: off += 4; continue
        out[eid] = s; off = nxt
    assert len(out) == count, "shared %s: got %d want %d" % (name, len(out), count)
    return coll, out

_senv = UnityPy.load(os.path.join(GAME, "localization-assets-shared_assets_all.bundle"))
ID2KEY = {}
for _o in _senv.objects:
    if str(_o.type) != "114": continue
    _coll, _m = parse_shared(_o.get_raw_data())
    ID2KEY[_coll] = _m
print("shared tables:", {k: len(v) for k, v in ID2KEY.items()})

def parse_obj(raw):
    name = None
    for off in range(20, 40, 4):
        s, n = read_str(raw, off)
        if s: name, o1 = s, n; break
    coll, o2 = read_str(raw, o1)
    start = o2 + 24
    count = struct.unpack_from("<i", raw, start)[0]
    entries, end = parse_entries(raw, start + 4, count)
    assert entries is not None, "parse failed for %s" % name
    return name, start, entries, end

env = UnityPy.load(SRC)
applied = {}
for o in env.objects:
    if str(o.type) != "114": continue
    raw = o.get_raw_data()
    name, start, entries, end = parse_obj(raw)
    assert build(raw[:start + 4], entries, raw[end:]) == raw, "roundtrip broke for %s" % name

    table = name  # e.g. "Card_zh-Hans"
    key = table.replace("_zh-Hans", "")
    wanted = T.get(key)
    if not wanted: continue

    # 需要 id -> key 的映射，从 shared bundle 取
    new_entries, n = [], 0
    for eid, val, meta in entries:
        if ID2KEY.get(key, {}).get(eid) in wanted:
            new = wanted[ID2KEY[key][eid]]
            assert val == "", "要改的条目原本非空! %s" % ID2KEY[key][eid]
            val = new; n += 1
        new_entries.append((eid, val, meta))
    applied[name] = n
    o.set_raw_data(build(raw[:start + 4], new_entries, raw[end:]))

data = env.file.save(packer="original")
if isinstance(data, str): data = data.encode()
open(OUTPATH, "wb").write(data)
print("written:", OUTPATH, len(data), "bytes")
print("applied per table:", applied)
print("total applied:", sum(applied.values()))
