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
    /// 中文字形预热（只预热真正含中文字形的字体）。
    ///
    /// 背景与实测经过：
    ///  1. 游戏的中文字体是 TMP **Dynamic** 字体，图集运行时才分配、按需加字形；
    ///     字形没就位时渲染为空白 —— 这是「卡名有时显示有时不显示」的来源。
    ///  2. 第一版实现无差别地对 18 个字体灌 1714 字，**引入了新问题**：
    ///     实测日志显示，卡名/卡描述用的拉丁展示字体
    ///     （`Tom Chalky - BobbyJonesSoft-*`、`Comicraft - CCDuskTillDawn*`）
    ///     **根本不含 CJK 字形**（"有 1623 字未加入"），却仍被灌进 ~90 个
    ///     ASCII/标点字形，图集从 1 页涨到 2 页 —— 纯属有害。
    ///     卡牌标题/描述用的正是这些字体，跨页后渲染错乱，出现了「添丨稠花精」式乱码。
    ///  3. 试过「关多图集 + 调大图集到 8192² + ClearFontAssetData」做单页方案，
    ///     实测**装不下**：8192²（6700 万像素）只吃下 550/1713 字，
    ///     且开销极大（分配 64MB 纹理）会明显拖慢启动，已放弃。
    ///
    /// 本版做法（最小改动、只保留被实测证明有价值的部分）：
    ///  先用一个常用汉字探测。**吃不下 CJK 的字体直接跳过**，不再无谓撑大图集；
    ///  能吃的字体按**原有设置**灌入全部字符（不动图集尺寸、不动多图集开关、
    ///  不调用 ClearFontAssetData —— 那会销毁图集纹理，有破坏正在渲染文本的风险）。
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
                var all = new List<TMP_FontAsset>();
                var seen = new HashSet<int>();
                foreach (var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<TMP_FontAsset>()))
                {
                    TMP_FontAsset fa;
                    try { fa = o.TryCast<TMP_FontAsset>(); } catch { continue; }
                    Collect(fa, seen, all);          // 含 fallback 链
                }

                int dyn = 0, skipped = 0, warmed = 0;
                foreach (var fa in all)
                {
                    try
                    {
                        if (fa.atlasPopulationMode != AtlasPopulationMode.Dynamic) continue;
                        dyn++;
                        if (WarmOne(fa, log)) warmed++; else skipped++;
                    }
                    catch (Exception e) { log($"[SGZhFix]   预热 {Name(fa)} 出错：{e.Message}"); }
                }
                log($"[SGZhFix] 字形预热完毕：扫描 {all.Count} 个字体，动态 {dyn} 个 —— "
                    + $"预热 {warmed}，跳过(不含中文字形) {skipped}");
            }
            catch (Exception e) { logErr($"[SGZhFix] 字形预热出错（不影响游戏）：{e}"); }
        }

        /// <returns>true=已预热；false=不含中文字形，已跳过</returns>
        private static bool WarmOne(TMP_FontAsset fa, Action<string> log)
        {
            // 探测：一个常用汉字都加不进去，说明这个字体不含 CJK 字形。
            // 用探测而不是"全灌一遍再看缺多少"，是为了不给拉丁字体留下
            // 几十个 ASCII 字形 —— 那正是把它们的图集撑到第 2 页的原因。
            bool canCjk;
            try { canCjk = fa.TryAddCharacters("的", out string probeMissing) && string.IsNullOrEmpty(probeMissing); }
            catch { canCjk = false; }

            if (!canCjk)
            {
                log($"[SGZhFix]   字体 {Name(fa)}: 不含中文字形 → 跳过预热（避免无谓撑大图集）");
                return false;
            }

            bool ok;
            string missing = null;
            try { ok = fa.TryAddCharacters(_chars, out missing); }
            catch (Exception e) { ok = false; missing = e.Message; }

            int miss = string.IsNullOrEmpty(missing) ? 0 : missing.Length;
            log($"[SGZhFix]   字体 {Name(fa)}: {(ok ? "全部加入" : $"有 {miss} 字未加入")}，图集页={SafePages(fa)}");
            return true;
        }

        private static void Collect(TMP_FontAsset fa, HashSet<int> seen, List<TMP_FontAsset> acc)
        {
            if (fa == null) return;
            int id;
            try { id = fa.GetInstanceID(); } catch { return; }
            if (!seen.Add(id)) return;
            acc.Add(fa);
            try
            {
                var fb = fa.fallbackFontAssetTable;
                if (fb != null) foreach (var f in fb) Collect(f, seen, acc);
            }
            catch { }
        }

        private static int SafePages(TMP_FontAsset fa)
        {
            try { return fa.atlasTextureCount; } catch { return -1; }
        }

        private static string Name(TMP_FontAsset fa)
        {
            try { return fa.name; } catch { return "?"; }
        }
    }
}
