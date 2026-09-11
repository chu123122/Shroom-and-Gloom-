# Shroom and Gloom 中文显示修复补丁（Chinese Display Fix）

《Shroom and Gloom》（Steam 版，Unity 2022.3.62f3 / IL2CPP）的中文显示修复。

修复中文界面下**部分文字整词消失**、**部分文字鼠标悬停后才出现**的问题。
共 **65 条**译文（卡牌描述 57 / 生态与商店 5 / 敌人意图 2 / 界面 1），
词条用词对齐游戏内既有官方中文（黏糊、幽暗、精力、黏稠、留存…），非另行发明。

> 原版中文语言表里有 65 条条目的值是空字符串，而游戏代码遇到空值**不回退英文**
> （`LocalizationExtensions.FlagIfEmpty`），于是这些词在卡面、敌人意图、悬停提示里直接不见。
> 详见文末「技术说明」。

## 安装（解压即用）

1. 下载 `ShroomAndGloom_ChineseFix_vX.Y.Z.zip`
2. 解压到游戏根目录，即 `steamapps\common\Shroom and Gloom\` 下
   （包内已是 `winhttp.dll` / `BepInEx\` / `dotnet\` 结构，直接覆盖过去即可）
3. 正常启动游戏，语言保持「中文 (简体)」

首次启动会停顿一会儿——那是在生成 IL2CPP 互操作程序集，属正常现象，之后启动很快。

**不修改游戏任何原文件**，纯运行时注入。

## 卸载

删除游戏根目录下这几项即可：

```
winhttp.dll
doorstop_config.ini
.doorstop_version
changelog.txt
BepInEx\
dotnet\
```

或执行 Steam「验证游戏文件完整性」。

## 兼容性

- 适配 Steam 版 Unity 2022.3.62f3（IL2CPP x64）
- 随包附带 BepInEx 6 (bleeding edge, build 788)，无需另行安装
- 游戏更新后若语言表有变动，补丁可能部分失效，等待补丁更新

## 已知限制

- **只修这 65 条空条目**，不改动其他任何文本
- 中文语言表另有约 8 条英文/开发占位符残留（如 `Further Detail Here`、`Unity.Localization`），**不在本次范围**
- 若 `BepInEx\LogOutput.log` 显示「写入 0 条」，说明游戏已自行修好这些条目，补丁无副作用

## 反馈

发现问题请提交 GitHub Issues，并附：**游戏版本、出现场景、截图或译文条目**。

## 许可

本补丁的译文与工具代码采用 MIT 许可证（见 LICENSE）。
游戏及其文本、素材版权归 Team Lazerbeam 所有。
本补丁不包含任何游戏资产、官方译文或第三方破解组件。
随包分发的 BepInEx 采用 LGPL-2.1，出处见包内 `THIRD-PARTY.txt`。
仅供学习交流，请支持正版游戏；使用本补丁即表示接受上述条款。

---
