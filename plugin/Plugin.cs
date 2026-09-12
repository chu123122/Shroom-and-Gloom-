using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using UnityEngine;
using UnityEngine.Localization.Settings;

namespace SGZhFix
{
    /// <summary>
    /// 《Shroom and Gloom》中文显示修复。
    ///
    /// 问题：中文 StringTable 里有 65 条 entry 的值为空字符串，而
    /// LocalizationExtensions.FlagIfEmpty 对空值返回空串且不回退英文
    /// （5 个取值函数全部收口于此），导致 LocalizationHelpers.ProcessCommonWordLinkKey
    /// 拼出 &lt;link=...&gt;&lt;/link&gt; 零长度链接——整词连同点击区一起不可见。
    ///
    /// 做法：运行时把这 65 条译文写回内存中的 StringTable。
    /// 之所以改数据而不是只改取值函数：悬停 tooltip 走的是 KeywordTooltipRegistry，
    /// 它直接读表、绕过了那 5 个函数，只补函数修不到它。
    /// </summary>
    [BepInPlugin(Guid, "Shroom and Gloom 中文显示修复", Version)]
    public class Plugin : BasePlugin
    {
        public const string Guid = "sg.zhfix";
        public const string Version = "1.0.0";

        internal static ManualLogSource LogSource;

        public override void Load()
        {
            LogSource = Log;
            try
            {
                // BepInEx 6 的 BasePlugin 没有 Info 属性（那是 BepInEx 5），
                // 插件一律放在 plugins/ 下，直接用 Paths.PluginPath
                Translations.Load(Path.Combine(Paths.PluginPath, "translations.json"), LogMsg, LogErr);

                if (Translations.Loaded)
                {
                    Patches.Apply(LogMsg, LogErr);
                    GlyphWarmer.LoadCharset(LogMsg, LogErr);
                    AddComponent<LocalizationPump>();
                    AddComponent<TextDiagnostics>();   // 诊断（默认关闭，见 TextDiagnostics.Enabled）
                    LogMsg($"[SGZhFix] 就绪，等待本地化表加载…");
                }
            }
            catch (Exception e)
            {
                LogErr($"[SGZhFix] 初始化失败（游戏仍可正常游玩）：{e}");
            }
        }

        // 注意：不要叫 Info/Error，会与基类成员名冲突（方法组传参时编译失败）
        internal static void LogMsg(string msg) => LogSource?.LogInfo(msg);
        internal static void LogErr(string msg) => LogSource?.LogError(msg);
    }

    /// <summary>
    /// 轮询等待本地化表就绪，然后把译文写进表，最后触发一次 UI 刷新。
    /// 用 Update 轮询而不是挂 S_Localization 的初始化回调：那是异步 UniTask，
    /// 跨 IL2CPP 边界挂接容易出问题，轮询简单且够用（表加载只需几秒）。
    /// </summary>
    internal class LocalizationPump : MonoBehaviour
    {
        // Il2CppObjectBase 通过反射查找 (IntPtr) 构造函数来实例化注入类型，必须显式提供
        public LocalizationPump(IntPtr ptr) : base(ptr) { }

        private bool _injectedForLocale;
        private bool _everInjected;
        private string _lastLocale;
        private float _waited;
        private float _zhSince;          // 切到中文后经过的秒数
        private const float Timeout = 120f;
        private const float AlreadyFilledGrace = 5f;

        private void Update()
        {
            try
            {
                _waited += Time.deltaTime;
                // 超时只用于「迟迟等不到中文」这一种情况。
                // 注入成功后不再计时，否则会在 120s 时报一条假的超时错误，
                // 并且把组件停掉、失去响应后续语言切换的能力。
                if (!_everInjected && _waited > Timeout)
                {
                    Plugin.LogErr($"[SGZhFix] 等待中文语言超时（{Timeout}s），放弃。");
                    enabled = false;
                    return;
                }

                var locale = LocalizationSettings.SelectedLocale;
                if (locale == null) return;
                var code = locale.Identifier.Code;
                if (string.IsNullOrEmpty(code)) return;

                // 语言变了就重新评估（中→英→中 也要能再注入）
                if (code != _lastLocale)
                {
                    _lastLocale = code;
                    _injectedForLocale = false;
                    _zhSince = 0f;
                    Plugin.LogMsg($"[SGZhFix] 当前语言: {code}");
                }

                // 关键：GetTable 返回的是「当前 locale」的表。
                // 英文下表里每个 key 都有值，此时注入会被全部跳过——
                // 必须等语言真的切到中文再动手。
                if (!code.ToLowerInvariant().StartsWith("zh")) return;

                _zhSince += Time.deltaTime;
                if (TablesReady() && !_injectedForLocale)
                {
                    int written = Inject();      // 幂等：只填空值
                    if (written > 0)
                    {
                        _injectedForLocale = true;
                        _everInjected = true;
                        Plugin.LogMsg($"[SGZhFix] 注入完成：写入 {written} 条（{code}，等待 {_waited:F1}s）");
                        // 表就绪、语言已是中文，此时预热最合适：把中文全部落进单页图集，
                        // 既避免字形缺失导致的空白，也避免跨页导致的渲染错乱
                        GlyphWarmer.Warm(Plugin.LogMsg, Plugin.LogErr);
                        Refresh();
                    }
                    else if (_zhSince > AlreadyFilledGrace)
                    {
                        // 连续几秒一条都没写，说明这张表本来就不缺这些条目
                        _injectedForLocale = true;
                        Plugin.LogMsg($"[SGZhFix] {code} 表中这些条目均已有值，无需注入");
                    }
                }
            }
            catch (Exception e)
            {
                enabled = false;
                Plugin.LogErr($"[SGZhFix] 注入过程出错，已停止（游戏仍可正常游玩）：{e}");
            }
        }

        /// <summary>5 张表都能取到才算就绪。</summary>
        internal static bool TablesReady()
        {
            foreach (var coll in Translations.Collections)
            {
                if (LocalizationSettings.StringDatabase.GetTable(coll) == null) return false;
            }
            return true;
        }

        private static int Inject()
        {
            int written = 0, skipped = 0, missing = 0;
            foreach (var coll in Translations.Collections)
            {
                var wanted = Translations.Table(coll);
                if (wanted == null) continue;

                var table = LocalizationSettings.StringDatabase.GetTable(coll);
                if (table == null) continue;

                foreach (var kv in wanted)
                {
                    var entry = table.GetEntry(kv.Key);
                    if (entry == null) { missing++; continue; }
                    // 只填空值：已有译文一律不动（含官方后续修好的内容）
                    if (!string.IsNullOrEmpty(entry.Value)) { skipped++; continue; }
                    entry.Value = kv.Value;
                    written++;
                }
            }
            if (skipped > 0) Plugin.LogMsg($"[SGZhFix] 跳过 {skipped} 条（表内已有值）");
            if (missing > 0) Plugin.LogMsg($"[SGZhFix] {missing} 条在当前表中不存在，已跳过");
            return written;
        }

        /// <summary>
        /// 复用游戏现成的语言切换事件刷新界面。它有 10 个订阅者
        /// （DeckDisplay / EncounterUI / V_Player / SpeechBubble / M_EnemyController /
        ///  M_HazardController / RoundUpUIManager / SelfStandingEncounterUI /
        ///  CreditsScroller / LocalizationTextGroup），不新增刷新机制。
        /// </summary>
        private static void Refresh()
        {
            try
            {
                var cb = LocalizationHelpers.OnLanguageChange;
                if (cb != null) cb.Invoke();
                else Plugin.LogMsg("[SGZhFix] OnLanguageChange 无订阅者，跳过刷新");
            }
            catch (Exception e)
            {
                Plugin.LogErr($"[SGZhFix] 刷新事件触发失败：{e}");
            }
        }
    }
}
