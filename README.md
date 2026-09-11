# Shroom and Gloom 中文显示修复补丁

修复《Shroom and Gloom》中文界面下**部分文字整词消失**、**部分文字鼠标悬停后才出现**的问题。

## 问题根因

游戏用 Unity Localization。中文 `StringTable` 里有 **65 条 entry 的值是空字符串 `""`**
（Card 57 / World 5 / Enemy 2 / UI 1），而代码对空值**不回退英文**：

`LocalizationExtensions.cs:69-80` 的 `FlagIfEmpty` 在语言调试关闭时直接返回空串。
5 个取值函数全部收口到这里（`LocalizationExtensions.cs:255 / 281 / 297 / 345 / 410`）：

```
GetCardEntry / GetEnemyEntry / GetUIEntry / GetWorldEntry / GetCardNamesEntry
```

产出"整词消失"的具体位置是 `LocalizationHelpers.cs:520-597` 的 `ProcessCommonWordLinkKey`
（`:557` 卡名分支、`:568` Card/Enemy 词条分支**没有空值保护**）——空值会拼出
`<#hex><link=Card_TOOLTIP_XXX></link></color>`，即**零长度链接**，整词连同点击区一起不可见。

卡面还会因 `DescriptionBox.cs:81-88` 对空描述 `SetActive(false)` 而整个描述框消失。

丢失的是高频词：`PROPERTY_ANY/WILD/NERVOUS/SINGED/WEIRD/STORED_GUNK/THIRSTY`、
`INTENT_GROUP_UP/STORE_GUNK/RAISE_GHOSTS/...`、`TOOLTIP_PROPERTY_*`、`WORD_STORED_GUNK`。

## 修复方式

把这 65 条补成中文译文，**直接写进中文 StringTable bundle**。
不改代码、不装 mod 加载器、不动游戏本体任何其它文件。

> Addressables 的 catalog 虽然为每个 bundle 存了 CRC，但 `m_UseUWRForLocalBundles=false`
> 且全部 bundle 都在本地 StreamingAssets，走 `AssetBundle.LoadFromFile`——**本地加载不校验 CRC**，
> 所以替换 bundle 是安全的。

## 用法

依赖 Python 3 + `UnityPy`：

```bash
pip install UnityPy
```

```bash
python apply_translations.py   # 由 translations.json 生成 patched/*.bundle
python verify_patch.py         # 全量校验：只改这 65 条，其余一条未动
python deploy.py install       # 备份原文件并安装
python deploy.py status        # 查看当前状态
python deploy.py restore       # 还原
```

游戏目录默认 `D:/SteamLibrary/steamapps/common/Shroom and Gloom`，
可用环境变量 `SG_GAME_DIR` 覆盖。

## 文件说明

| 文件 | 作用 |
|---|---|
| `translations.json` | **唯一的译文数据源**。改译文只需改这里再重跑脚本 |
| `rebuild.py` | StringTable 二进制解析/重序列化（含字节级往返自测） |
| `gen_translations.py` | 由内置译文表生成 `translations.json`，并校验 token 与空值前提 |
| `apply_translations.py` | 生成补丁包。**始终从 `backup/` 的原始包读取**，可反复重建 |
| `verify_patch.py` | 全量 diff 校验，确认只有 65 处变更 |
| `deploy.py` | 安装 / 还原 / 状态 |

## 已知限制

- **Steam「验证文件完整性」或游戏更新会覆盖补丁**，需重跑 `deploy.py install`
- 只修了这 65 条空值。另有未翻译条目、`GetLocalizedToolTipPropertyWithCommonTokens`
  丢弃 token（`LocalizationExtensions.cs:118-127`）、`ChooseRandomNonEmpty` 越界
  （`GlobalLocalization.cs:200-211`）等**未在本次修复范围内**
- 图层错位问题未调查

## 声明

本仓库只包含**译文数据与处理脚本**，不包含游戏本体任何资产。
游戏版权归 Team Lazerbeam 所有。使用者需自行拥有正版游戏。
