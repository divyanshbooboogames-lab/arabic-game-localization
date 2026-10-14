// Arabic render check for Unity (Editor only). Copy to Assets/Editor/. Menu: Tools > Arabic Localization > 7. Render Check.
// Renders every string of out/strings.csv into a text prefab you choose (e.g. an RTLTextMeshPro label sized like
// your tightest UI slot) and reports: glyphs missing from the font, text overflowing the box, and Arabic that was
// not shaped (letters will show disconnected). Shaping is done by the prefab's own component, so this works with
// RTLTMPro or any other TMP-based setup. Uses only core TextMeshPro API.
// Not compiled outside your project: if your TMP version differs, expect small fixes on first run.
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using TMPro;
using UnityEditor;
using UnityEngine;

public class ArabicLocQA : EditorWindow
{
    string csvPath = "Assets/Localization/strings.csv";
    string columns = "ar,ar-SA,ar-EG";
    GameObject textPrefab;

    [MenuItem("Tools/Arabic Localization/7. Render Check", priority = 26)]
    static void Open() => GetWindow<ArabicLocQA>("Arabic Loc QA");

    void OnGUI()
    {
        csvPath = EditorGUILayout.TextField("strings.csv", csvPath);
        columns = EditorGUILayout.TextField("Columns", columns);
        textPrefab = (GameObject)EditorGUILayout.ObjectField("Text prefab", textPrefab, typeof(GameObject), false);
        using (new EditorGUI.DisabledScope(textPrefab == null))
            if (GUILayout.Button("Run")) Run();
    }

    void Run()
    {
        var rows = ReadCsv(File.ReadAllText(csvPath, Encoding.UTF8));
        var header = rows[0];
        var canvas = new GameObject("ArabicLocQA_Canvas", typeof(Canvas));
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(textPrefab, canvas.transform);
        var tmp = instance.GetComponentInChildren<TMP_Text>();
        var report = new StringBuilder("key,column,issue,detail\n");
        int issues = 0, skipped = 0;
        try
        {
            foreach (var col in columns.Split(','))
            {
                int c = System.Array.IndexOf(header, col.Trim());
                if (c < 0) { Debug.LogWarning($"Arabic Loc QA: column '{col}' not in CSV"); continue; }
                for (int i = 1; i < rows.Count; i++)
                {
                    if (c >= rows[i].Length || rows[i][c].Length == 0) continue;
                    string key = rows[i][0], text = rows[i][c];
                    if (Regex.IsMatch(text, @"\{\s*\w+\s*,\s*(plural|select)")) { skipped++; continue; } // needs the formatter: test in game
                    text = Regex.Replace(text, @"\{\w+\}|%(\d+\$)?[sd]", "8888"); // widest-case sample value

                    tmp.text = text;
                    tmp.ForceMeshUpdate();
                    string shown = tmp.GetParsedText();

                    if (!tmp.font.HasCharacters(shown, out List<char> missing))
                    {
                        var real = missing.FindAll(ch => ch > ' ');
                        if (real.Count > 0) Add(report, ref issues, key, col, "missing_glyphs",
                            string.Join(" ", real.ConvertAll(ch => $"U+{(int)ch:X4}")));
                    }
                    var box = tmp.rectTransform.rect;
                    if (tmp.isTextOverflowing || tmp.preferredHeight > box.height + 0.5f)
                        Add(report, ref issues, key, col, "overflow", $"needs {tmp.preferredWidth:0}x{tmp.preferredHeight:0}, box {box.width:0}x{box.height:0}");

                    int baseLetters = 0, shapedForms = 0;
                    foreach (char ch in shown)
                    {
                        if (ch >= 'ب' && ch <= 'ي' && ch != 'ـ') baseLetters++;
                        else if (ch >= 'ﭐ' && ch <= 'ﻼ') shapedForms++;
                    }
                    if (baseLetters > shapedForms)
                        Add(report, ref issues, key, col, "not_shaped", "Arabic reaches TMP unshaped: letters render disconnected (use RTLTMPro or UI Toolkit ATG)");
                }
            }
        }
        finally { DestroyImmediate(canvas); }

        string outPath = Path.Combine(Path.GetDirectoryName(csvPath), "arabic_render_report.csv");
        File.WriteAllText(outPath, report.ToString(), new UTF8Encoding(true));
        Debug.Log($"Arabic Loc QA: {issues} issues, {skipped} ICU strings skipped (check those in game). Report: {outPath}");
    }

    static void Add(StringBuilder r, ref int n, string key, string col, string issue, string detail)
    {
        n++;
        r.Append(key).Append(',').Append(col).Append(',').Append(issue).Append(",\"").Append(detail.Replace("\"", "\"\"")).Append("\"\n");
    }

    static List<string[]> ReadCsv(string s)
    {
        var rows = new List<string[]>();
        var row = new List<string>();
        var field = new StringBuilder();
        bool quoted = false;
        for (int i = 0; i < s.Length; i++)
        {
            char ch = s[i];
            if (quoted)
            {
                if (ch != '"') field.Append(ch);
                else if (i + 1 < s.Length && s[i + 1] == '"') { field.Append('"'); i++; }
                else quoted = false;
            }
            else if (ch == '"') quoted = true;
            else if (ch == ',') { row.Add(field.ToString()); field.Clear(); }
            else if (ch == '\n') { row.Add(field.ToString().TrimEnd('\r')); field.Clear(); rows.Add(row.ToArray()); row = new List<string>(); }
            else field.Append(ch);
        }
        if (field.Length > 0 || row.Count > 0) { row.Add(field.ToString()); rows.Add(row.ToArray()); }
        return rows;
    }
}
