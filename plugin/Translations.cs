using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace SGZhFix
{
    /// <summary>
    /// 译文数据源。格式与仓库根的 translations.json 一致：
    /// { "Card": { "PROPERTY_ANY": "任意", ... }, "Enemy": {...}, ... }
    /// 键名与游戏 StringTable 的表集合名一一对应。
    /// </summary>
    internal static class Translations
    {
        // 表集合名（对应 LocalizationExtensions 里的 TableCollection_* 常量）
        public static readonly string[] Collections = { "Card", "Card Names", "Enemy", "UI", "World" };

        private static readonly Dictionary<string, Dictionary<string, string>> ByCollection =
            new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal);

        /// <summary>扁平索引：key -> 译文。用于读取路径的兜底补丁（那里拿不到表集合名）。</summary>
        private static readonly Dictionary<string, string> ByKey =
            new Dictionary<string, string>(StringComparer.Ordinal);

        public static int Count { get; private set; }
        public static bool Loaded { get; private set; }

        public static void Load(string path, Action<string> log, Action<string> logError)
        {
            try
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(path));
                foreach (var coll in doc.RootElement.EnumerateObject())
                {
                    if (coll.Value.ValueKind != JsonValueKind.Object) continue;
                    var map = new Dictionary<string, string>(StringComparer.Ordinal);
                    foreach (var item in coll.Value.EnumerateObject())
                    {
                        map[item.Name] = item.Value.GetString() ?? string.Empty;
                    }
                    ByCollection[coll.Name] = map;
                    foreach (var kv in map) ByKey[kv.Key] = kv.Value;   // 键在各表间实测无重名
                }
                Count = ByKey.Count;
                Loaded = Count > 0;
                log($"[SGZhFix] 载入译文 {Count} 条，覆盖 {ByCollection.Count} 张表");
            }
            catch (Exception e)
            {
                logError($"[SGZhFix] 载入译文失败：{e}");
            }
        }

        public static bool TryGet(string collection, string key, out string value)
        {
            value = null;
            return ByCollection.TryGetValue(collection, out var map)
                   && map.TryGetValue(key, out value);
        }

        /// <summary>按 key 查找（不分表）。仅用于兜底补丁。</summary>
        public static bool TryGetByKey(string key, out string value) => ByKey.TryGetValue(key, out value);

        public static IEnumerable<KeyValuePair<string, Dictionary<string, string>>> All => ByCollection;

        public static Dictionary<string, string> Table(string collection)
            => ByCollection.TryGetValue(collection, out var m) ? m : null;
    }
}
