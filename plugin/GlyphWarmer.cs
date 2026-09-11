using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using Il2CppInterop.Runtime;
using TMPro;
using UnityEngine;

namespace SGZhFix
{
    /// <summary>
    /// 中文动态字体图集的字形预热。
    ///
    /// 背景：游戏里所有中文字体（WDXLLubrifontSC / NotoSansSC）的图集在序列化数据里
    /// 都是 0×0、零图像数据 —— 这是 TMP **Dynamic** 字体资产的特征：图集运行时才分配，
    /// 用到哪个字才往图集里加。对比之下拉丁文用的 ShroomScript 是 1024×1024 完整烘焙的静态图集。
    ///
    /// 后果：某个中文字形在被加入图集之前渲染为**空白**。同一个字，
    /// 别的界面先用过 → 卡名能显示；没用过 → 空白。表现为「有时显示有时不显示」。
    /// 游戏设置卡名文字后不会主动触发 TMP 重建，所以时机完全不受控。
    ///
    /// 做法：语言切到中文后，把游戏全部中文文本用到的字符一次性预热进图集，
    /// 让界面渲染之前字形就已就位。
    /// 字符集由离线脚本从 5 张中文 StringTable 提取，随插件分发（charset.txt）。
    /// </summary>
    internal static class GlyphWarmer
    {
        private static string _chars;

        public static bool LoadCharset(Action<string> log, Action<string> logErr)
        {
            try
            {
                var path = Path.Combine(Paths.PluginPath, "charset.txt");
                if (!File.Exists(path)) { logErr($"[SGZhFix] 找不到 {path}，跳过字形预热"); return false; }
                _chars = File.ReadAllText(path, System.Text.Encoding.UTF8)
                              .Replace("\r", "").Replace("\n", "");
                if (string.IsNullOrEmpty(_chars)) { logErr("[SGZhFix] charset.txt 为空"); return false; }
                log($"[SGZhFix] 载入字符集 {_chars.Length} 字");
                return true;
            }
            catch (Exception e) { logErr($"[SGZhFix] 载入字符集失败：{e}"); return false; }
        }

        public static void Warm(Action<string> log, Action<string> logErr)
        {
            if (string.IsNullOrEmpty(_chars)) return;
            try
            {
                // 枚举所有已加载的字体资产（含未激活对象），避免使用泛型重载以规避 interop 问题
                var objs = Resources.FindObjectsOfTypeAll(Il2CppType.Of<TMP_FontAsset>());
                var seen = new HashSet<int>();
                int total = 0, dynamicCount = 0;

                foreach (var o in objs)
                {
                    var fa = o.TryCast<TMP_FontAsset>();
                    if (fa == null || !seen.Add(fa.GetInstanceID())) continue;
                    total++;
                    if (WarmOne(fa, log)) dynamicCount++;

                    // 顺带处理 fallback 链：中文字形往往是通过 fallback 命中 CJK 字体的
                    var fb = fa.fallbackFontAssetTable;
                    if (fb != null)
                    {
                        foreach (var f in fb)
                        {
                            if (f == null || !seen.Add(f.GetInstanceID())) continue;
                            total++;
                            if (WarmOne(f, log)) dynamicCount++;
                        }
                    }
                }
                log($"[SGZhFix] 字形预热完毕：扫描 {total} 个字体资产，其中动态 {dynamicCount} 个");
            }
            catch (Exception e)
            {
                logErr($"[SGZhFix] 字形预热出错（不影响游戏）：{e}");
            }
        }

        /// <returns>是否为动态字体</returns>
        private static bool WarmOne(TMP_FontAsset fa, Action<string> log)
        {
            try
            {
                var mode = fa.atlasPopulationMode;
                int pagesBefore = fa.atlasTextureCount;
                string first = "无";
                var tex = fa.atlasTextures;
                if (tex != null && tex.Length > 0 && tex[0] != null)
                    first = $"{tex[0].width}x{tex[0].height}";

                log($"[SGZhFix] 字体 {fa.name}: 模式={mode} 图集页={pagesBefore} 首页={first} 多图集={fa.isMultiAtlasTexturesEnabled}");

                if (mode != AtlasPopulationMode.Dynamic) return false;

                bool ok = fa.TryAddCharacters(_chars, out string missing);
                int miss = missing == null ? 0 : missing.Length;
                log($"[SGZhFix]   预热结果: {(ok ? "全部加入" : $"有 {miss} 字未加入")}，图集页 {pagesBefore} → {fa.atlasTextureCount}");
                return true;
            }
            catch (Exception e)
            {
                log($"[SGZhFix]   预热 {fa?.name} 失败：{e.Message}");
                return false;
            }
        }
    }
}
