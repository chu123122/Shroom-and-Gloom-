# -*- coding: utf-8 -*-
"""生成一键安装包：解压到游戏根目录即可用。

产出 dist/ShroomAndGloom_ChineseFix_v<版本>.zip，内含：
    winhttp.dll / doorstop_config.ini / .doorstop_version / changelog.txt
    dotnet/                   BepInEx 运行时
    BepInEx/core|patchers/    BepInEx 本体
    BepInEx/plugins/SGZhFix.dll        本插件
    BepInEx/plugins/translations.json  译文
    安装说明.txt

BepInEx 采用 LGPL-2.1，随包分发需保留其许可证与出处，见 THIRD-PARTY.txt。
"""
import os, sys, zipfile, shutil, json

HERE = os.path.dirname(os.path.abspath(__file__))
BEPINEX_ZIP = os.path.join(HERE, "bepinex_dl", "be.zip")
PLUGIN_DLL = os.path.join(HERE, "plugin", "bin", "Release", "SGZhFix.dll")
TRANSLATIONS = os.path.join(HERE, "translations.json")
DIST = os.path.join(HERE, "dist")
VERSION = "1.0.0"

BEPINEX_URL = ("https://builds.bepinex.dev/projects/bepinex_be/788/"
               "BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.788%2B5b766a3.zip")

README_TXT = """\
Shroom and Gloom 中文显示修复 v{ver}
================================================

安装
----
把本压缩包里的所有文件解压到游戏根目录，即：

    ...\\steamapps\\common\\Shroom and Gloom\\

（压缩包内已经是 winhttp.dll / BepInEx/ / dotnet/ 的结构，
  直接覆盖过去即可，不需要再手动建目录。）

然后正常启动游戏，语言保持「中文 (简体)」即可。

首次启动会有一会儿黑屏/停顿，那是在生成 IL2CPP 的互操作程序集，
属正常现象，通常几分钟内完成。之后每次启动都很快。

本补丁做了什么
--------------
修复中文界面下部分文字「整词消失」的问题——
中文语言表里有 65 条条目是空字符串，游戏代码遇到空值不回退英文，
导致这些词在卡牌描述、敌人意图、悬停提示里直接不见。
本补丁在运行时把这 65 条补回中文，不修改游戏任何文件。

卸载
----
删掉游戏根目录下的这些即可：

    winhttp.dll
    doorstop_config.ini
    .doorstop_version
    changelog.txt
    BepInEx\\  （整个目录）
    dotnet\\   （整个目录）

或执行 Steam「验证游戏文件完整性」（会把上述文件一并清掉）。

已知限制
--------
- 仅修复上述 65 条空条目，不改变其他任何文本
- 游戏更新后若新增/改动语言表，补丁可能失效或部分失效
- 若日志（BepInEx\\LogOutput.log）中出现 "注入完成：写入 0 条"，
  说明游戏已自行修好这些条目，此时补丁无副作用

日志与排错
----------
BepInEx\\LogOutput.log 中搜索 "SGZhFix" 可看到载入条数与注入结果。

许可
----
本补丁的译文与工具代码采用 MIT 许可证。
随包分发的 BepInEx 采用 LGPL-2.1，版权归 BepInEx 团队，出处见 THIRD-PARTY.txt。
游戏及其文本、素材版权归 Team Lazerbeam 所有。
本补丁不包含任何游戏资产、官方译文或第三方破解组件。
仅供学习交流，请支持正版游戏。
""".format(ver=VERSION)

THIRD_PARTY = """\
本安装包内含以下第三方组件：

BepInEx 6 (bleeding edge, build 788) — Unity IL2CPP 插件加载器
    许可证: LGPL-2.1
    来源:   {url}
    说明:   仅做原样分发，未作修改。其完整许可证见包内 changelog.txt 与项目主页。
""".format(url=BEPINEX_URL)


def build():
    missing = [p for p in (BEPINEX_ZIP, PLUGIN_DLL, TRANSLATIONS) if not os.path.exists(p)]
    if missing:
        print("缺少以下文件，无法打包：")
        for m in missing: print("   ", m)
        if PLUGIN_DLL in missing:
            print("\n提示: 先编译插件 —— cd plugin && dotnet build -c Release")
        return 1

    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "ShroomAndGloom_ChineseFix_v%s.zip" % VERSION)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        # 1) BepInEx 运行时（原样搬运，跳过它自带的空 plugins 目录占位）
        with zipfile.ZipFile(BEPINEX_ZIP) as src:
            for it in src.infolist():
                if it.is_dir(): continue
                z.writestr(it.filename, src.read(it.filename))
        # 2) 我们的插件与译文
        z.write(PLUGIN_DLL, "BepInEx/plugins/SGZhFix.dll")
        z.write(TRANSLATIONS, "BepInEx/plugins/translations.json")
        # 3) 说明与声明
        z.writestr("安装说明.txt", README_TXT)
        z.writestr("THIRD-PARTY.txt", THIRD_PARTY)

    n = len(json.load(open(TRANSLATIONS, encoding="utf-8")))
    size = os.path.getsize(out) / 1024 / 1024
    print("已生成: %s" % out)
    print("  大小: %.1f MB   译文: %d 条" % (size, sum(len(v) for v in
          json.load(open(TRANSLATIONS, encoding="utf-8")).values())))
    return 0


if __name__ == "__main__":
    sys.exit(build())
