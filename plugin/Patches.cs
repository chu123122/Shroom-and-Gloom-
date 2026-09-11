using System;
using HarmonyLib;
using UnityEngine.Localization.Settings;

namespace SGZhFix
{
    /// <summary>
    /// 兜底补丁：万一 <c>StringTableEntry.Value</c> 的写入在 Il2CppInterop 下
    /// 没能写穿到底层表，这几处 postfix 仍能在读取时拦住空值。
    ///
    /// 主路径（往 StringTable 里写数据）不需要任何补丁，
    /// 所以即使这些补丁在当前 BepInEx/IL2CPP 组合下不生效，修复依然成立。
    ///
    /// 为什么不补 FlagIfEmpty：它是 private 小方法，被 IL2CPP 内联的风险高，
    /// 一旦内联补丁完全不触发。下面这 5 个是 public 大方法，稳妥得多。
    /// </summary>
    internal static class Patches
    {
        public static void Apply(Action<string> info, Action<string> error)
        {
            try
            {
                var harmony = new Harmony(Plugin.Guid);
                harmony.PatchAll(typeof(Patches));
                info("[SGZhFix] 兜底补丁已注册");
            }
            catch (Exception e)
            {
                // 补丁失败不影响主路径
                error($"[SGZhFix] 兜底补丁注册失败（不影响注入）：{e}");
            }
        }

        // ---- 5 个取值函数：命中空值就用译文填 ----

        [HarmonyPostfix, HarmonyPatch(typeof(LocalizationExtensions), nameof(LocalizationExtensions.GetCardEntry))]
        private static void CardEntry(string entryKey, ref string __result)
            => Fill("Card", entryKey, ref __result);

        [HarmonyPostfix, HarmonyPatch(typeof(LocalizationExtensions), nameof(LocalizationExtensions.GetEnemyEntry))]
        private static void EnemyEntry(string entryKey, ref string __result)
            => Fill("Enemy", entryKey, ref __result);

        [HarmonyPostfix, HarmonyPatch(typeof(LocalizationExtensions), nameof(LocalizationExtensions.GetUIEntry))]
        private static void UIEntry(string entryKey, ref string __result)
            => Fill("UI", entryKey, ref __result);

        [HarmonyPostfix, HarmonyPatch(typeof(LocalizationExtensions), nameof(LocalizationExtensions.GetWorldEntry))]
        private static void WorldEntry(string entryKey, ref string __result)
            => Fill("World", entryKey, ref __result);

        [HarmonyPostfix, HarmonyPatch(typeof(LocalizationExtensions), nameof(LocalizationExtensions.GetCardNamesEntry))]
        private static void CardNamesEntry(string entryKey, ref string __result)
            => Fill("Card Names", entryKey, ref __result);

        private static void Fill(string collection, string key, ref string result)
        {
            if (!string.IsNullOrEmpty(result)) return;              // 非空一律放行
            if (Translations.TryGet(collection, key, out var v)) result = v;
        }

        // ---- 悬停 tooltip：它直接读表，绕过了上面 5 个函数 ----

        [HarmonyPostfix, HarmonyPatch(typeof(KeywordTooltipRegistry), nameof(KeywordTooltipRegistry.TryGetTooltipFromLinkID))]
        private static void Tooltip(string linkKey, ref string tooltip, ref bool __result)
        {
            if (!__result || !string.IsNullOrEmpty(tooltip)) return;
            if (string.IsNullOrEmpty(linkKey)) return;

            // 与 KeywordTooltipRegistry.SplitLinkKey 一致：按第一个 '_' 切成 表集合 / 条目键
            var idx = linkKey.IndexOf('_');
            if (idx <= 0 || idx >= linkKey.Length - 1) return;
            var collection = linkKey.Substring(0, idx);
            var key = linkKey.Substring(idx + 1).ToUpperInvariant();

            if (Translations.TryGet(collection, key, out var v)) tooltip = v;
        }
    }
}
