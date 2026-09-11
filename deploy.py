# -*- coding: utf-8 -*-
"""补丁部署 / 还原 / 状态检查。

用法:
    python deploy.py install    # 备份原文件并安装补丁包
    python deploy.py restore    # 从备份还原
    python deploy.py status     # 查看当前状态
"""
import os, sys, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
# 游戏目录（Steam 默认安装路径，按需修改）
GAME = os.environ.get("SG_GAME_DIR",
    r"D:/SteamLibrary/steamapps/common/Shroom and Gloom")
AA = os.path.join(GAME, "Shroom and Gloom_Data", "StreamingAssets", "aa", "StandaloneWindows64")

BUNDLE = "localization-string-tables-chinese(simplified)(zh-hans)_assets_all.bundle"
PATCHED = os.path.join(HERE, "patched", BUNDLE)
BACKUP = os.path.join(HERE, "backup", BUNDLE)
TARGET = os.path.join(AA, BUNDLE)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None

def status():
    def row(label, p):
        if not os.path.exists(p):
            print(f"  {label:10s} 不存在")
        else:
            print(f"  {label:10s} {os.path.getsize(p):>8d} 字节  sha256:{sha(p)}")
    print("路径:", TARGET)
    row("游戏内", TARGET)
    row("补丁包", PATCHED)
    row("备份", BACKUP)
    if os.path.exists(TARGET) and os.path.exists(BACKUP):
        print("当前状态:", "已打补丁" if sha(TARGET) == sha(PATCHED)
              else ("原始" if sha(TARGET) == sha(BACKUP) else "未知(与补丁/备份均不符)"))

def install():
    if not os.path.exists(PATCHED):
        print("错误: 找不到补丁包，请先运行 apply_translations.py")
        return 1
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if not os.path.exists(BACKUP):
        shutil.copy2(TARGET, BACKUP)
        print("已备份原文件 ->", BACKUP)
    else:
        print("备份已存在，跳过备份")
    shutil.copy2(PATCHED, TARGET)
    print("已安装补丁 ->", TARGET)
    status()
    return 0

def restore():
    if not os.path.exists(BACKUP):
        print("错误: 没有备份，无法还原。可用 Steam「验证文件完整性」恢复。")
        return 1
    shutil.copy2(BACKUP, TARGET)
    print("已还原 ->", TARGET)
    status()
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    sys.exit({"install": install, "restore": restore, "status": status}
             .get(cmd, lambda: (print(__doc__), 1)[1])())
