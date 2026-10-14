// Tools > Arabic Localization: runs the Arabic localization tool (localize.py) from inside the Unity Editor.
// Copy to Assets/Editor/ next to ArabicLocQA.cs. Needs Python 3.10+ with `pip install anthropic fonttools`.
// The tool runs in the background: the Editor stays usable and its output streams into the window.
// API keys are never stored here. Set ANTHROPIC_API_KEY (and OPENAI_API_KEY if used) as user environment
// variables, then restart Unity Hub and Unity so the Editor inherits them.
// Settings are saved to ProjectSettings/ArabicLocalization.json (paths relative to the project root), so the
// whole team shares them through version control.
// Not compiled outside your project: expect small fixes on first run.
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

[Serializable]
public class ArabicLocSettings
{
#if UNITY_EDITOR_WIN
    public string python = "py";
#else
    public string python = "python3";
#endif
    public string toolDir = "Tools/arabic-l10n";
    public string source = "Localization/strings_en.csv";
    public string outDir = "Localization/arabic_out";
    public string model = "claude-opus-5-5";
    public string judgeModel = "claude-opus-5-5";
    public string genderVar = "";
    public string syntax = "auto"; // auto | icu | smart (Unity Smart Strings)
    public bool batchApi = false;
    public bool retranslateAll = false;
    public bool useSubscription = true; // translate through Claude Code on a Claude subscription: no API key, no credits
    public string font = "Assets/Fonts/ArabicFont.ttf";
    public bool shaped = true;
    public string exportTo = "Assets/Localization/Arabic/strings.csv";
}

public class ArabicLocalizationWindow : EditorWindow
{
    const string SettingsFile = "ProjectSettings/ArabicLocalization.json";
    static readonly string[] SyntaxIds = { "auto", "icu", "smart" };
    static readonly GUIContent[] SyntaxLabels =
        { new GUIContent("Auto-detect"), new GUIContent("ICU MessageFormat"), new GUIContent("Unity Smart Strings") };
    ArabicLocSettings s;
    Process proc;
    string running;
    Action<int> onExit;
    readonly ConcurrentQueue<string> incoming = new ConcurrentQueue<string>();
    readonly StringBuilder log = new StringBuilder();
    Vector2 scroll;
    bool showSettings = true;

    static string Root => Directory.GetParent(Application.dataPath).FullName;
    static string Abs(string p) => Path.GetFullPath(Path.IsPathRooted(p) ? p : Path.Combine(Root, p));
    string Review => Path.Combine(Abs(s.outDir), "review.csv");

    static ArabicLocalizationWindow Get() => GetWindow<ArabicLocalizationWindow>("Arabic Localization");
    [MenuItem("Tools/Arabic Localization/Open", priority = 0)] static void MOpen() => Get();
    [MenuItem("Tools/Arabic Localization/Fake-Arabic Test Strings", priority = 10)] static void MPseudo() => Get().Pseudo();
    [MenuItem("Tools/Arabic Localization/1. Check English Source", priority = 20)] static void MLint() => Get().Lint();
    [MenuItem("Tools/Arabic Localization/2. Translate", priority = 21)] static void MTranslate() => Get().Translate();
    [MenuItem("Tools/Arabic Localization/3. Open Review Sheet", priority = 22)] static void MReview() => Get().OpenReview();
    [MenuItem("Tools/Arabic Localization/4. Score Linguist Audit", priority = 23)] static void MScore() => Get().Score();
    [MenuItem("Tools/Arabic Localization/5. Export to Unity", priority = 24)] static void MExport() => Get().Export();
    [MenuItem("Tools/Arabic Localization/6. Font Check", priority = 25)] static void MFont() => Get().FontCheck();

    void OnEnable()
    {
        var path = Path.Combine(Root, SettingsFile);
        s = File.Exists(path) ? JsonUtility.FromJson<ArabicLocSettings>(File.ReadAllText(path)) : new ArabicLocSettings();
        EditorApplication.update += Pump;
    }

    void OnDisable()
    {
        EditorApplication.update -= Pump;
        // A domain reload must not kill a long translation: the tool keeps running and writes its files.
        if (proc != null && !proc.HasExited)
            Debug.Log($"Arabic Localization: '{running}' keeps running in the background; results will appear in {s.outDir}.");
    }

    void OnGUI()
    {
        showSettings = EditorGUILayout.Foldout(showSettings, "Settings (shared via " + SettingsFile + ")", true);
        if (showSettings)
        {
            EditorGUI.BeginChangeCheck();
            s.python = EditorGUILayout.TextField(new GUIContent("Python command", "py, python, python3 or a full path"), s.python);
            s.toolDir = EditorGUILayout.TextField(new GUIContent("Tool folder", "Folder containing localize.py"), s.toolDir);
            s.source = EditorGUILayout.TextField(new GUIContent("English CSV", "key, en, type, context, speaker, listener, scene... A Unity Localization CSV export (Key, English(en)) also works"), s.source);
            s.outDir = EditorGUILayout.TextField(new GUIContent("Work folder", "review.csv and other outputs go here"), s.outDir);
            s.model = EditorGUILayout.TextField(new GUIContent("Translator model", "Bake-off winner, e.g. claude-opus-5-5 or openai:<model>"), s.model);
            s.judgeModel = EditorGUILayout.TextField(new GUIContent("Reviewer model", "Preferably a different provider than the translator"), s.judgeModel);
            s.genderVar = EditorGUILayout.TextField(new GUIContent("Player gender variable", "e.g. player_gender, if the game passes it; else empty"), s.genderVar);
            int syn = Mathf.Max(0, Array.IndexOf(SyntaxIds, s.syntax));
            s.syntax = SyntaxIds[EditorGUILayout.Popup(new GUIContent("Plural syntax", "Auto detects it from the English strings"), syn, SyntaxLabels)];
            s.batchApi = EditorGUILayout.Toggle(new GUIContent("Half-price batch mode", "Claude Batches API: 50% cheaper, results usually within an hour"), s.batchApi);
            s.retranslateAll = EditorGUILayout.Toggle(new GUIContent("Retranslate everything", "Off: unchanged approved strings are reused for free. On: after a style-guide change"), s.retranslateAll);
            s.useSubscription = EditorGUILayout.Toggle(new GUIContent("Use Claude subscription (no API key)", "Claude Code does the translating on your subscription; the models above and batch mode are then ignored"), s.useSubscription);
            s.font = EditorGUILayout.TextField(new GUIContent("Arabic font file", ".ttf/.otf used by your Arabic TMP font asset"), s.font);
            s.shaped = EditorGUILayout.Toggle(new GUIContent("Pre-shaped text (RTLTMPro)", "Font must contain Arabic presentation forms"), s.shaped);
            s.exportTo = EditorGUILayout.TextField(new GUIContent("Export to", "Where the final strings.csv is copied inside Assets"), s.exportTo);
            if (EditorGUI.EndChangeCheck())
                File.WriteAllText(Path.Combine(Root, SettingsFile), JsonUtility.ToJson(s, true));
            if (!s.useSubscription && string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY")))
                EditorGUILayout.HelpBox("ANTHROPIC_API_KEY is not visible to Unity. Set it as a user environment variable, then restart Unity Hub and Unity. (Not needed if you signed in with `ant auth login`.)", MessageType.Warning);
        }

        using (new EditorGUI.DisabledScope(proc != null))
        {
            if (GUILayout.Button("Fake-Arabic test strings (test layout before translating)")) Pseudo();
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("1. Check source")) Lint();
            if (GUILayout.Button("2. Translate")) Translate();
            if (GUILayout.Button("3. Review sheet")) OpenReview();
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("4. Score")) Score();
            if (GUILayout.Button("5. Export to Unity")) Export();
            if (GUILayout.Button("6. Font check")) FontCheck();
            if (GUILayout.Button("7. Render check")) EditorApplication.ExecuteMenuItem("Tools/Arabic Localization/7. Render Check");
            EditorGUILayout.EndHorizontal();
        }
        if (proc != null)
        {
            EditorGUILayout.HelpBox($"Running: {running}. You can keep working; output appears below.", MessageType.Info);
            if (GUILayout.Button("Cancel")) Cancel();
        }
        scroll = EditorGUILayout.BeginScrollView(scroll);
        EditorGUILayout.TextArea(log.ToString(), GUILayout.ExpandHeight(true));
        EditorGUILayout.EndScrollView();
    }

    string Translator => s.useSubscription ? "claude-code" : s.model;
    string Reviewer => s.useSubscription ? "claude-code" : s.judgeModel;

    void Lint() => Run("Check English source",
        new List<string> { "lint", Abs(s.source), "--out", Abs(s.outDir), "--suggest", "--model", Translator, "--syntax", s.syntax },
        code => Open(Path.Combine(Abs(s.outDir), "source_lint.csv")));

    void Translate()
    {
        if (!EditorUtility.DisplayDialog("Translate to Arabic", s.useSubscription
                ? $"Prepare {s.source} as translation jobs for Claude Code?\nNo API key or credits: Claude Code does the work on your Claude subscription."
                : $"Send {s.source} to {s.model} (translator) and {s.judgeModel} (reviewer)?\nThis uses your paid API account.",
                "Translate", "Cancel")) return;
        var args = new List<string> { "translate", Abs(s.source), "--out", Abs(s.outDir), "--model", Translator, "--judge-model", Reviewer };
        if (s.batchApi && !s.useSubscription) args.Add("--batch-api");
        if (s.retranslateAll) args.Add("--no-reuse");
        AddFormatArgs(args);
        Run("Translate", args, code => { if (code == 0) OpenReview(); });
    }

    void Pseudo()
    {
        if (!EditorUtility.DisplayDialog("Fake-Arabic test strings",
                $"Replace the Arabic strings at {s.exportTo} with fake Arabic for layout testing?\nRun 5. Export to Unity later to put real translations back.",
                "Replace", "Cancel")) return;
        Run("Fake-Arabic test strings", new List<string> { "pseudo", Abs(s.source), "--out", Abs(s.outDir) }, code =>
        {
            if (code != 0) return;
            CopyIntoProject(Path.Combine(Abs(s.outDir), "pseudo_strings.csv"));
            Log("Import it with the CSV extension, switch the game to Arabic, and look for: letters not joined, text not right-to-left, missing [ ] (truncation), broken plurals.");
        });
    }

    void CopyIntoProject(string file)
    {
        var target = Abs(s.exportTo);
        Directory.CreateDirectory(Path.GetDirectoryName(target));
        File.Copy(file, target, true);
        AssetDatabase.Refresh();
        Log($"Copied to {s.exportTo}. Import it with your String Table Collection's CSV extension (Import).");
    }

    void OpenReview()
    {
        if (File.Exists(Review)) Open(Review);
        else Log("No review sheet yet: run 2. Translate first.");
    }

    void Score() => Run("Score linguist audit", new List<string> { "score", Review });

    void Export()
    {
        var args = new List<string> { "export", Review, "--out", Abs(s.outDir) };
        AddFormatArgs(args);
        Run("Export", args, code =>
        {
            if (code != 0) { Log("Export blocked: fix the rows listed above in the review sheet, then export again."); return; }
            CopyIntoProject(Path.Combine(Abs(s.outDir), "strings.csv"));
        });
    }

    void FontCheck()
    {
        var args = new List<string> { "fontcheck", Path.Combine(Abs(s.outDir), "strings.csv"), "--font", Abs(s.font) };
        if (s.shaped) args.Add("--shaped");
        Run("Font check", args);
    }

    void AddFormatArgs(List<string> args) // plural/select syntax and the optional player-gender variable
    {
        args.Add("--syntax");
        args.Add(s.syntax);
        if (string.IsNullOrEmpty(s.genderVar)) return;
        args.Add("--gender-var");
        args.Add(s.genderVar);
    }

    void Run(string label, List<string> args, Action<int> exit = null)
    {
        if (proc != null) return;
        var script = Path.Combine(Abs(s.toolDir), "localize.py");
        if (!File.Exists(script)) { Log($"localize.py not found in {Abs(s.toolDir)}: set 'Tool folder' in Settings."); return; }
        var psi = new ProcessStartInfo(s.python)
        {
            Arguments = Quote(script) + " " + string.Join(" ", args.ConvertAll(Quote)),
            WorkingDirectory = Abs(s.toolDir),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };
        psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"; // Arabic output would crash a Windows console codepage
        psi.EnvironmentVariables["PYTHONUTF8"] = "1";
        Log($"\n> {label}");
        try
        {
            proc = new Process { StartInfo = psi };
            proc.OutputDataReceived += (sender, e) => { if (e.Data != null) incoming.Enqueue(e.Data); };
            proc.ErrorDataReceived += (sender, e) => { if (e.Data != null) incoming.Enqueue(e.Data); };
            proc.Start();
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();
            running = label;
            onExit = exit;
        }
        catch (Exception e)
        {
            proc = null;
            Log($"Could not start '{s.python}': {e.Message}. Install Python 3.10+ and set 'Python command' in Settings.");
        }
    }

    void Pump()
    {
        bool changed = false;
        while (incoming.TryDequeue(out var line)) { log.AppendLine(line); changed = true; }
        if (proc != null && proc.HasExited)
        {
            proc.WaitForExit(); // let the async readers flush
            while (incoming.TryDequeue(out var line)) log.AppendLine(line);
            int code = proc.ExitCode;
            proc.Dispose();
            proc = null;
            log.AppendLine($"[{running} finished, exit code {code}]");
            if (code == 3)
                log.AppendLine("Waiting for Claude Code: paste the 'Follow ...' line above into Claude Code. It answers the jobs and finishes the run; then continue here (e.g. 3. Open Review Sheet).");
            var handler = onExit;
            onExit = null;
            handler?.Invoke(code);
            changed = true;
        }
        if (changed) { scroll.y = float.MaxValue; Repaint(); }
    }

    void Cancel()
    {
        onExit = null; // a cancelled run must not trigger its follow-up step
        try { if (proc != null && !proc.HasExited) proc.Kill(); } catch (Exception e) { Log(e.Message); }
        Log($"[{running} cancelled; finished requests are cached, so running it again resumes]");
    }

    void Log(string msg) { log.AppendLine(msg); Repaint(); }

    static void Open(string path) { if (File.Exists(path)) EditorUtility.OpenWithDefaultApp(path); }

    static string Quote(string a) => "\"" + a.Replace("\"", "\\\"") + "\"";
}
