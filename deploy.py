# -*- coding: utf-8 -*-
"""补丁部署 / 还原 / 状态检查。

需要同时替换**两个**文件：
  1. 中文 StringTable bundle —— 65 条译文
  2. catalog.json          —— 该 bundle 的 CRC 置 0

  第 2 步不可省：Addressables 对本地 bundle 同样调用
  AssetBundle.LoadFromFile(path, crc, offset) 校验 CRC，bundle 内容一变就不匹配，
  Unity 会拒绝加载（Player.log: "CRC Mismatch. Provided ..., calculated ... from data"），
  结果整个 zh-Hans 字符串表加载失败、界面回退英文。
  crc=0 时 Unity 跳过校验。catalog 内条目靠字节偏移互引，所以补丁保持字节长度不变。

用法:
    python deploy.py install    # 备份原文件并安装
    python deploy.py restore    # 从备份还原
    python deploy.py status     # 查看当前状态
"""
import os, sys, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("SG_GAME_DIR",
    r"D:/SteamLibrary/steamapps/common/Shroom and Gloom")
DATA = os.path.join(GAME, "Shroom and Gloom_Data")
AA = os.path.join(DATA, "StreamingAssets", "aa")

# (相对工作区的补丁路径, 游戏内目标路径, 显示名)
FILES = [
    ("localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle",
     os.path.join(AA, "StandaloneWindows64",
                  "localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle"),
     "中文表 bundle"),
    ("catalog.json", os.path.join(AA, "catalog.json"), "catalog.json"),
]

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None

def paths(rel):
    return (os.path.join(HERE, "patched", os.path.basename(rel)),
            os.path.join(HERE, "backup", os.path.basename(rel)))

def status():
    for rel, target, label in FILES:
        p, b = paths(rel)
        print("\n[%s]" % label)
        for name, path in (("游戏内", target), ("补丁包", p), ("备份", b)):
            if os.path.exists(path):
                print("  %-8s %8d 字节  sha256:%s" % (name, os.path.getsize(path), sha(path)))
            else:
                print("  %-8s 不存在" % name)
        if os.path.exists(target) and os.path.exists(b):
            st = ("已打补丁" if sha(target) == sha(p) else
                  "原始" if sha(target) == sha(b) else "未知(与补丁/备份均不符)")
            print("  当前状态:", st)

def install():
    missing = [rel for rel, _, _ in FILES if not os.path.exists(paths(rel)[0])]
    if missing:
        print("错误: 缺少补丁包，请先运行 apply_translations.py 和 patch_catalog.py")
        for m in missing: print("   ", m)
        return 1
    for rel, target, label in FILES:
        p, b = paths(rel)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        if not os.path.exists(b):
            shutil.copy2(target, b); print("[%s] 已备份原文件" % label)
        else:
            print("[%s] 备份已存在，跳过备份" % label)
        shutil.copy2(p, target); print("[%s] 已安装" % label)
    status()
    return 0

def restore():
    rc = 0
    for rel, target, label in FILES:
        _, b = paths(rel)
        if not os.path.exists(b):
            print("[%s] 错误: 没有备份，可用 Steam「验证文件完整性」恢复" % label); rc = 1; continue
        shutil.copy2(b, target); print("[%s] 已还原" % label)
    status()
    return rc

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    sys.exit({"install": install, "restore": restore, "status": status}
             .get(cmd, lambda: (print(__doc__), 1)[1])())
