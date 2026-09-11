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

# 技术说明（给想改的人）

## 根因

中文 `StringTable` 有 65 条 entry 值为空字符串 `""`（不是 `_` 占位、也不是缺失）。
代码对空值不回退英文——`LocalizationExtensions.cs:69-80`：

```csharp
if (value != null && value.Trim() == "_") return string.Empty;   // 有意为空
if (!string.IsNullOrWhiteSpace(value))  return value;
return EmptyEntry(entryKey, value);   // 语言调试关闭时直接 return value => ""
```

5 个取值函数全部收口到 `FlagIfEmpty`（`LocalizationExtensions.cs:255 / 281 / 297 / 345 / 410`）：
`GetCardEntry` / `GetEnemyEntry` / `GetUIEntry` / `GetWorldEntry` / `GetCardNamesEntry`。

产出"整词消失"的位置是 `LocalizationHelpers.cs:520-597` 的 `ProcessCommonWordLinkKey`
（`:557` 卡名分支、`:568` Card/Enemy 词条分支**没有空值保护**）——空值会拼出
`<#hex><link=Card_TOOLTIP_XXX></link></color>`，即**零长度链接**，整词连同点击区一起不可见。
卡面还会因 `DescriptionBox.cs:81-88` 对空描述 `SetActive(false)` 而整个描述框消失。

## 为什么改数据而不是改取值函数

悬停 tooltip 走 `KeywordTooltipRegistry.cs:9-36`，它**直接读表**、绕过了那 5 个函数。
只补函数修不到 tooltip，所以必须把值写进表本身。

## 插件行为

```
Load()  读取 translations.json（静态字典）
  ↓
Update() 轮询，等两个条件同时成立：
          ① 当前语言是中文（LocalizationSettings.SelectedLocale 的 code 以 zh 开头）
          ② 5 张表都能取到（StringDatabase.GetTable != null）
  ↓
逐条写入：仅当表内该条目为空时才写，已有值一律不动（重复调用幂等）
  ↓
触发一次 LocalizationHelpers.OnLanguageChange 刷新界面
        （现成事件，10 个订阅者，不新增刷新机制）
```

> **为什么必须判语言**：`GetTable(集合)` 返回的是**当前 locale** 的表。
> 实测游戏启动时先是 `en`，约 0.7 秒后才切到 `zh-Hans`。若在 `en` 阶段就注入，
> 拿到的是英文表——每个 key 都有值，会被"只填空值"的逻辑全部跳过，一条都写不进去。
> 语言变化时会重新评估，所以「中→英→中」也能再次注入。

另注册 6 个 Harmony postfix 作兜底（5 个取值函数 + `KeywordTooltipRegistry`），
万一 `StringTableEntry.Value` 的写入在 Il2CppInterop 下没写穿，读取时仍能拦住空值。
**主路径不依赖任何补丁**，所以补丁不生效也不影响修复成立。

## 目录结构

| 路径 | 作用 |
|---|---|
| `translations.json` | **唯一译文数据源** |
| `plugin/` | BepInEx 插件工程（`dotnet build -c Release`） |
| `package.py` | 生成一键安装 zip |
| `rebuild.py` | 备用：StringTable 二进制解析/重序列化 |
| `apply_translations.py` `patch_catalog.py` `deploy.py` | 备用：直接改游戏文件的方案（见下） |

## 备用方案：直接改文件

不改代码、不装加载器，直接替换两个游戏文件亦可，但有坑：

Addressables 对本地 bundle 同样调 `AssetBundle.LoadFromFile(path, crc, offset)` 校验 CRC。
**只改 bundle 会让整个界面变英文**——bundle 被拒 → zh-Hans 语言表全部加载失败 →
`LocalizedFallbackText` 返回英文 fallback。Player.log 中的证据：

```
CRC Mismatch. Provided 2da1151c, calculated dfbb94ae from data.
Will not load AssetBundle '...localization-string-tables-chinese...bundle'
```

所以必须同时把 catalog 里该 bundle 的 `m_Crc` 置 0（`patch_catalog.py`，
改动保持字节长度一致，因为 catalog 内部靠偏移互引）。

代价：Steam「验证文件完整性」或游戏更新会覆盖，需重跑 `deploy.py install`。
插件方案没有这个问题，**推荐插件**。

```bash
pip install UnityPy
python apply_translations.py   # 生成 patched/*.bundle
python patch_catalog.py        # 生成 patched/catalog.json
python verify_patch.py         # 全量校验：仅 65 处变更
python deploy.py install       # 安装（自动备份）
python deploy.py restore       # 还原
```
