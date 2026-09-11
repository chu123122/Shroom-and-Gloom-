# -*- coding: utf-8 -*-
"""生成 translations.json（65 条中文译文）并输出对照审核文件。
译法依据：sg-debug/terminology.txt、models.txt、style_baseline.txt 中已有的官方中文。
约束：token 原样保留且顺序与英文一致；换行用真实换行符。
"""
import os, re, json, struct
import UnityPy

BASE = r"D:/SteamLibrary/steamapps/common/Shroom and Gloom/Shroom and Gloom_Data/StreamingAssets/aa/StandaloneWindows64"
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 译文 ----------------
T = {
"Card": {
 "TOOLTIP_CLASS_NONE": "没有特定的卡牌类别。",
 "TRIGGER_IF_STORED_GUNK_CONSUMED": "[HEXCODE][LINKKEY]若储存的黏糊被销毁</link></color>，",
 "TRIGGER_IF_GUNK_REMOVED_ON_TARGET_CARD": "[HEXCODE][LINKKEY]若目标身上的黏糊被移除</link></color>，",
 "TRIGGER_IF_PET_IS_DRAWN": "当宠物被抽到时，",
 "TRIGGER_IF_PET_IS_CREATED": "当宠物被创造时，",
 "WORD_STORE_PROTEIN": "存储蛋白质",
 "WORD_CALL_A_PET": "召唤宠物",
 "WORD_FAT_GRUB": "肥胖蠕虫",
 "INTENT_CREATE_PET_SINGLE": "在[MULTIPLICITY_ENEMY]上创造宠物",
 "INTENT_CREATE_PET_MULTI": "在[MULTIPLICITY_ENEMY]上创造 [PNUM] 个宠物",
 "INTENT_EATEN_DAMAGE": "[HEXCODE]蛋白质 [PNUM]</color>",
 "INTENT_STORE_GUNK": "存储 [PNUM] 层[LINKKEY=PROPERTY_GUNK][JOINER=WORD_OFF][MULTIPLICITY_CARD]",
 "INTENT_INCREASE_STORED_GUNK": "[LINKKEY=WORD_STORE] [PNUM] 层[LINKKEY=PROPERTY_GUNK]",
 "INTENT_USE_STORED_GUNK": "使用 [PNUM] [LINKKEY=WORD_STORED_GUNK]",
 "INTENT_DRAW_STORE_GUNK_CARD_SINGLE": "抽取一张储存黏糊的牌",
 "INTENT_DRAW_STORE_GUNK_CARD_MULTI": "抽取 [PNUM] 张储存黏糊的牌",
 "INTENT_APPLY_INFESTED": "施加 [PNUM] [LINKKEY=STATUS_INFEST][JOINER=WORD_IN][MULTIPLICITY_ENEMY]",
 "INTENT_GAIN_ARE_ROLL_MULTI": "获得 [PNUM] 次重掷",
 "INTENT_MAKE_CARD_DAMAGE_EQUAL_TO_PROTEIN": "创造 [PNUM][HEXCODE][CARD_NAME]</color>，伤害等同于蛋白质",
 "INTENT_BLEED": "流血并承受 [PNUM] 点伤害",
 "INTENT_CREATE_CARD_ENCOUNTER_VAT": "培养缸",
 "INTENT_ENCOURAGE_PET": "鼓励你的宠物",
 "INTENT_FETCH_PET": "召回你的宠物",
 "INTENT_GROUP_UP": "聚群",
 "INTENT_MAKE_VOLATILE": "变得易爆",
 "INTENT_MOVE_TOWARDS_FRIEND": "向同伴移动",
 "INTENT_RAISE_GHOSTS": "唤起幽灵",
 "INTENT_REDUCE_COUNTDOWN": "降低倒计时",
 "INTENT_SHIELD_DONTUSE": "请勿使用：护盾",
 "INTENT_DIG_OLD": "挖掘（旧）",
 "PROPERTY_AMPLIFY_GLOOM": "[HEXCODE][LINKKEY]增幅幽暗</link></color> <b>X[PNUM].</b>",
 "PROPERTY_ANY": "任意",
 "PROPERTY_NERVOUS": "紧张",
 "PROPERTY_SINGED": "炙烤",
 "PROPERTY_WEIRD": "诡异",
 "PROPERTY_WILD": "狂野",
 "PROPERTY_STORED_GUNK": "储存的黏糊",
 "PROPERTY_THIRSTY": "干渴",
 "PROPERTY_ODD_USE_FREE": "奇数免费",
 "PROPERTY_PET": " 是你的宠物。",
 "TOOLTIP_PROPERTY_ANY": "任意特性",
 "TOOLTIP_PROPERTY_COUPON": "可以在商店中\n当作货币使用",
 "TOOLTIP_PROPERTY_DEATHLESS": "不死有什么用？",
 "TOOLTIP_PROPERTY_NERVOUS": "挖掘<i>紧张</i>的卡牌",
 "TOOLTIP_PROPERTY_SHROOM": "挖掘<i>菌菇</i>的卡牌",
 "TOOLTIP_PROPERTY_SINGED": "挖掘<i>炙烤</i>的卡牌",
 "TOOLTIP_PROPERTY_WEIRD": "挖掘<i>诡异</i>的卡牌。",
 "TOOLTIP_PROPERTY_WILD": "挖掘<i>狂野</i>的卡牌。",
 "TOOLTIP_PROPERTY_GOLD": "由早已消亡的文明使用。\n闪闪发亮。",
 "TOOLTIP_PROPERTY_THIRSTY": "完全不知道这是做什么用的。",
 "TOOLTIP_PROPERTY_ODD_USE_FREE": "如果将要打出的牌张数为奇数，\n此牌消耗 0 点精力。",
 "TOOLTIP_PROPERTY_PET": " 是你的宠物。",
 "TOOLTIP_WORD_STORE": "将手牌上的黏糊\n移入你的黏糊袋。",
 "TOOLTIP_WORD_STORED_GUNK": "储存的黏糊在探索时使用，\n在战斗中收获。",
 "TOOLTIP_WORD_CALL_A_PET": "召唤一个宠物并将其置入你的手牌。",
 "WORD_STORED_GUNK": "储存的黏糊",
 "INTENT_GAIN_A_REROLL_SINGLE": "获得 [PNUM] 次重掷",
},
"World": {
 "TRAINING_TYPE_DETAIL_ASS_ADD_GUNK_PERSISTENT_IF_FATAL_GAIN_ENERGY":
   "添加 [LINKKEY=WORD_GUNK]。持久。[LINKKEY=TRIGGER_IF_FATAL] 获得能量",
 "TRAINING_TYPE_DETAIL_ASS_GUNKY_TO_DAMAGE":
   "为手牌中每张[LINKKEY=WORD_GUNKY]牌添加“销毁 1 层[LINKKEY=PROPERTY_GUNK]”",
 "TRAINING_TYPE_DETAIL_ASS_INCREASE_GUNKY_ADD_DAMAGE_PER_GUNK_IN_HAND":
   "手牌中每层[LINKKEY=WORD_GUNKY]增加伤害",
 "TRAINING_TYPE_DETAIL_ASS_MULTIPLY_DAMAGE_INCREASE_GUNKLY":
   "翻倍[LINKKEY=WORD_GUNKY]",
 "TRAINING_TYPE_DETAIL_ASS_REDUCE_GUNKY_AND_DAMAGE":
   "降低[LINKKEY=WORD_GUNKY]和伤害",
},
"Enemy": {
 "ENEMY_INTENT_GROUP_UP": "[HEXCODE]会聚群</color>",
 "HAZARD_REWARD_TITLE_PATIENT_ZERO_2": "x",
},
"UI": {
 "PLAYER_STORED_GUNK_ORB_TOOLTIP": "储存的黏糊\n<#88AA77>用于科学研究</color>",
},
}

# ---------------- 读取游戏表做校验 ----------------
def astr(b, o):
    if o + 4 > len(b): return None, o
    n = struct.unpack_from("<I", b, o)[0]
    if n == 0: return "", (o + 4 + 3) & ~3
    if n > 200000 or o + 4 + n > len(b): return None, o
    try: s = b[o+4:o+4+n].decode("utf-8")
    except UnicodeDecodeError: return None, o
    if any(ord(c) < 32 and c not in "\n\r\t" for c in s): return None, o
    return s, (o + 4 + n + 3) & ~3

def extract(raw, st):
    out, off = [], st
    while off + 12 <= len(raw):
        i = struct.unpack_from("<q", raw, off)[0]
        s, n = astr(raw, off + 8)
        if s is None: off += 4; continue
        out.append((i, s)); off = n
    return out

def load(fn):
    env = UnityPy.load(os.path.join(BASE, fn)); r = {}
    for o in env.objects:
        if str(o.type) != "114": continue
        raw = o.get_raw_data(); nm, o1 = astr(raw, 28)
        s1, o2 = astr(raw, o1); s2, o3 = astr(raw, o2)
        e = extract(raw, o3)
        if len(e) < 5: e = extract(raw, o2)
        r[nm] = dict(e)
    return r

ZH = load("localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle")
EN = load("localization-string-tables-english(en)_assets_all.bundle")
SH = load("localization-assets-shared_assets_all.bundle")

TOKEN = re.compile(r"\[[A-Z0-9_]+(?:=[A-Za-z0-9_]+)?\]")
TAG = re.compile(r"</?(?:color|i|b|link|nobr)[^>]*>", re.I)

report, errors = [], []
for table, items in T.items():
    z = ZH[table + "_zh-Hans"]; e = EN[table + "_en"]; sh = SH[table + " Shared Data"]
    key2id = {k: i for i, k in sh.items() if k}
    for key, zh in items.items():
        i = key2id.get(key)
        if i is None:
            errors.append(f"[{table}] key 不存在: {key}"); continue
        ev = e.get(i)
        if ev is None:
            errors.append(f"[{table}] {key} 英文表无此 id"); continue
        if z.get(i, "") != "":
            errors.append(f"[{table}] {key} 中文表非空(={z.get(i)!r})，不该被改动")
        et, zt = TOKEN.findall(ev), TOKEN.findall(zh)
        if sorted(et) != sorted(zt):
            errors.append(f"[{table}] {key} token 不一致\n    EN={et}\n    ZH={zt}")
        if et != zt:
            report.append(f"[{table}] {key}  token 顺序不同(EN 顺序已保留的前提下不应发生)\n    EN={et}\n    ZH={zt}")
        report.append(f"[{table}] {key}\n    EN: {ev!r}\n    ZH: {zh!r}")

json.dump(T, open(os.path.join(OUT, "translations.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

with open(os.path.join(OUT, "translations_review.txt"), "w", encoding="utf-8") as f:
    f.write(f"共 {sum(len(v) for v in T.values())} 条\n")
    f.write("=" * 70 + "\n")
    f.write("\n".join(report))

print(f"译文条数: {sum(len(v) for v in T.values())}")
print(f"校验错误: {len(errors)}")
for x in errors: print("  !!", x)
