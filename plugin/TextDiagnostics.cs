using System;
using System.Collections.Generic;
using System.Text;
using BepInEx;
using Il2CppInterop.Runtime;
using TMPro;
using UnityEngine;

namespace SGZhFix
{
    /// <summary>
    /// 诊断：扫描界面上的 TMP 文本，找出「字体链渲染不了的中文字形」。
    ///
    /// 目的：定位 添丨稠花精 那类乱码——`丨` 在任何字符串表里都不存在，
    /// 说明它是字形缺失时的 notdef 字形，而不是数据本身有问题。
    /// 本组件回答三个问题：哪个 UI 对象、用的哪条字体链、缺哪些字。
    ///
    /// 只报 CJK 字形缺失（富文本标签、ASCII 标点不算），并按「字体+缺字集合」去重，
    /// 避免刷屏。跑够次数后自动停止。
    /// </summary>
    internal class TextDiagnostics : MonoBehaviour
    {
        public TextDiagnostics(IntPtr ptr) : base(ptr) { }

        private readonly HashSet<string> _reported = new HashSet<string>();
        private float _timer;
        private int _scans;
        private const float Interval = 5f;
        private const int MaxScans = 40;      // 5s × 40 = 约 200 秒，覆盖启动到游戏中

        private void Update()
        {
            try
            {
                _timer += Time.deltaTime;
                if (_timer < Interval) return;
                _timer = 0f;
                if (++_scans > MaxScans)
                {
                    Plugin.LogMsg($"[SGZhFix][诊断] 扫描结束（共 {MaxScans} 轮），累计报告 {_reported.Count} 类问题");
                    enabled = false;
                    return;
                }
                Scan();
            }
            catch (Exception e)
            {
                enabled = false;
                Plugin.LogErr($"[SGZhFix][诊断] 扫描出错，已停止：{e}");
            }
        }

        private void Scan()
        {
            var objs = Resources.FindObjectsOfTypeAll(Il2CppType.Of<TMP_Text>());
            foreach (var o in objs)
            {
                TMP_Text t;
                try { t = o.TryCast<TMP_Text>(); } catch { continue; }
                if (t == null) continue;

                bool active;
                string parsed;
                TMP_FontAsset font;
                try
                {
                    if (t.gameObject == null) continue;
                    active = t.isActiveAndEnabled;
                    if (!active) continue;
                    font = t.font;
                    if (font == null) continue;
                    parsed = t.GetParsedText();      // 已剥离富文本标签
                }
                catch { continue; }

                if (string.IsNullOrEmpty(parsed)) continue;

                var missing = MissingCjk(t, font, parsed);
                if (missing.Count == 0) continue;

                var key = font.name + "|" + new string(missing.ToArray());
                if (!_reported.Add(key)) continue;

                Plugin.LogErr(
                    $"[SGZhFix][诊断] 中文缺字形  对象='{PathOf(t.gameObject)}'  字体='{font.name}'" +
                    $"  缺字=[{new string(missing.ToArray())}]  文本={Trunc(parsed, 70)}");
                Plugin.LogErr($"[SGZhFix][诊断]   字体链: {ChainOf(t, font)}");
            }
        }

        /// <summary>返回 parsed 里字体链渲染不了的 CJK 字符（去重，保序）。</summary>
        private static List<char> MissingCjk(TMP_Text t, TMP_FontAsset font, string parsed)
        {
            var chain = BuildChain(t, font);
            var missing = new List<char>();
            var seen = new HashSet<char>();
            foreach (var ch in parsed)
            {
                if (ch < 0x2E80) continue;               // 只关心 CJK 区
                if (ch == '\n' || ch == '\r' || ch == '\t') continue;
                if (!seen.Add(ch)) continue;
                bool ok = false;
                foreach (var f in chain)
                {
                    try { if (f != null && f.HasCharacter(ch)) { ok = true; break; } }
                    catch { }
                }
                if (!ok) missing.Add(ch);
            }
            return missing;
        }

        /// <summary>模拟 TMP 的 fallback 查找顺序：自身 → 自身 fallback → 全局 fallback → 全局默认</summary>
        private static List<TMP_FontAsset> BuildChain(TMP_Text t, TMP_FontAsset font)
        {
            var chain = new List<TMP_FontAsset>();
            var seen = new HashSet<int>();
            void Add(TMP_FontAsset f)
            {
                if (f == null) return;
                int id;
                try { id = f.GetInstanceID(); } catch { return; }
                if (seen.Add(id)) chain.Add(f);
            }

            Add(font);
            try { if (font.fallbackFontAssetTable != null) foreach (var f in font.fallbackFontAssetTable) Add(f); } catch { }
            try
            {
                var s = TMP_Settings.fallbackFontAssets;
                if (s != null) foreach (var f in s) Add(f);
            }
            catch { }
            try { Add(TMP_Settings.defaultFontAsset); } catch { }
            return chain;
        }

        private static string ChainOf(TMP_Text t, TMP_FontAsset font)
        {
            var sb = new StringBuilder();
            foreach (var f in BuildChain(t, font))
            {
                if (sb.Length > 0) sb.Append(" → ");
                try { sb.Append(f.name); } catch { sb.Append("?"); }
            }
            return sb.ToString();
        }

        private static string PathOf(GameObject go)
        {
            var sb = new StringBuilder();
            try
            {
                var tr = go.transform;
                int depth = 0;
                while (tr != null && depth++ < 8)
                {
                    if (sb.Length > 0) sb.Insert(0, "/");
                    sb.Insert(0, tr.name);
                    tr = tr.parent;
                }
            }
            catch { }
            return sb.ToString();
        }

        private static string Trunc(string s, int n)
        {
            if (string.IsNullOrEmpty(s)) return "";
            s = s.Replace("\n", "\\n").Replace("\r", "");
            return s.Length <= n ? s : s.Substring(0, n) + "…";
        }
    }
}
