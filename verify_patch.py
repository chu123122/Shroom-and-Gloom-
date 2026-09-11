# -*- coding: utf-8 -*-
"""回读补丁后的 bundle：确认能加载、条目数不变、65 条已填、其余一条未动。"""
import os, json, struct
import UnityPy
from rebuild import read_str, parse_entries

GAME = r"D:/SteamLibrary/steamapps/common/Shroom and Gloom/Shroom and Gloom_Data/StreamingAssets/aa/StandaloneWindows64"
WORK = os.path.dirname(os.path.abspath(__file__))
BUNDLE = "localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle"
T = json.load(open(os.path.join(WORK, "translations.json"), encoding="utf-8"))

def tables(path):
    env = UnityPy.load(path)
    out = {}
    for o in env.objects:
        if str(o.type) != "114": continue
        raw = o.get_raw_data()
        name = None
        for off in range(20, 40, 4):
            s, n = read_str(raw, off)
            if s: name, o1 = s, n; break
        coll, o2 = read_str(raw, o1)
        start = o2 + 24
        count = struct.unpack_from("<i", raw, start)[0]
        entries, end = parse_entries(raw, start + 4, count)
        out[name] = dict((e[0], e[1]) for e in entries)
    return out

# 基线用未修改的原始包（优先 backup/），而不是游戏目录——游戏目录此时已装上补丁
_bk = os.path.join(WORK, "backup", BUNDLE)
orig = tables(_bk if os.path.exists(_bk) else os.path.join(GAME, BUNDLE))
new = tables(os.path.join(WORK, "patched", BUNDLE))

print("表数量: 原=%d 新=%d" % (len(orig), len(new)))
assert set(orig) == set(new), "表集合不一致!"

total_changed = 0
for name in sorted(orig):
    a, b = orig[name], new[name]
    assert set(a) == set(b), "%s id 集合不一致" % name
    changed = [i for i in a if a[i] != b[i]]
    total_changed += len(changed)
    print("  %-20s 条目=%4d 变更=%d" % (name, len(a), len(changed)))

print("\n总变更条目数: %d (期望 65)" % total_changed)
assert total_changed == 65, "变更数不符!"

# 逐条确认新值 == 译文，且旧值 == ""
bad = 0
for table, items in T.items():
    t = new[table + "_zh-Hans"]; o = orig[table + "_zh-Hans"]
    inv = {v: k for k, v in t.items()}
    for key, zh in items.items():
        hits = [i for i, v in t.items() if v == zh]
        if not hits: print("  !! 未找到:", table, key); bad += 1; continue
        i = hits[0]
        if o.get(i, "") != "":
            print("  !! 原值非空:", table, key, repr(o.get(i))); bad += 1
print("逐条校验失败数:", bad)
print("\n=== 抽样 ===")
for table, key in [("Card", "PROPERTY_ANY"), ("Card", "INTENT_GROUP_UP"),
                   ("Card", "TOOLTIP_PROPERTY_COUPON"), ("Card", "WORD_FAT_GRUB"),
                   ("Enemy", "ENEMY_INTENT_GROUP_UP"), ("World", "TRAINING_TYPE_DETAIL_ASS_MULTIPLY_DAMAGE_INCREASE_GUNKLY"),
                   ("UI", "PLAYER_STORED_GUNK_ORB_TOOLTIP")]:
    t = new[table + "_zh-Hans"]
    vals = [v for v in t.values() if v == T[table][key]]
    print("  %-45s -> %r" % (key, vals[0] if vals else "<缺失>"))
