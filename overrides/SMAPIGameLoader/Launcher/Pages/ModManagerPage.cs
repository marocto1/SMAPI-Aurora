using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using Android.Text;
using AndroidX.AppCompat.App;
using AndroidX.RecyclerView.Widget;
using Google.Android.Material.FloatingActionButton;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace SMAPIGameLoader.Launcher.Pages;

internal sealed class ModManagerPage : LinearLayout
{
    private readonly Context _context;
    private readonly List<ModInfo> _allMods = new();
    private readonly List<ModInfo> _visibleMods = new();
    private readonly ModAdapter _adapter;
    private readonly TextView _counts;
    private readonly TextView _empty;
    private readonly RecyclerView _list;
    private string _filter = "";
    private int _stateFilter; // 0 all, 1 enabled, 2 disabled, 3 issues
    private readonly Button[] _filterButtons = new Button[4];

    public FloatingActionButton InstallFab { get; }

    public ModManagerPage(Context context) : base(context)
    {
        _context = context;
        Orientation = Orientation.Vertical;
        SetBackgroundColor(AuroraUi.Background);

        var header = new LinearLayout(context) { Orientation = Orientation.Vertical };
        header.SetPadding(AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 29),
            AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 16));
        AddView(header, AuroraUi.ItemParams(context));

        var smallTitle = AuroraUi.Text(context, "YOUR COLLECTION", 12, AuroraUi.AccentSoft, true);
        header.AddView(smallTitle, AuroraUi.ItemParams(context, 9));
        var title = AuroraUi.Text(context, "Mod Library", 26, AuroraUi.White, true);
        header.AddView(title, AuroraUi.ItemParams(context, 7));
        _counts = AuroraUi.Text(context, "Scanning mods…", 13, AuroraUi.Muted);
        header.AddView(_counts, AuroraUi.ItemParams(context, 16));

        var search = new EditText(context);
        search.SetSingleLine(true);
        search.Hint = "Search installed mods";
        search.SetHintTextColor(AuroraUi.Muted);
        search.SetTextColor(AuroraUi.White);
        search.SetTextSize(Android.Util.ComplexUnitType.Sp, 14);
        search.SetPadding(AuroraUi.Dp(context, 16), AuroraUi.Dp(context, 9),
            AuroraUi.Dp(context, 16), AuroraUi.Dp(context, 9));
        search.Background = AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 15, true);
        header.AddView(search, AuroraUi.ItemParams(context, 13));

        var filters = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        string[] filterNames = { "All", "Enabled", "Disabled", "Issues" };
        for (int i = 0; i < filterNames.Length; i++)
        {
            int selection = i;
            var chip = AuroraUi.Action(context, filterNames[i]);
            chip.SetPadding(AuroraUi.Dp(context, 5), 0, AuroraUi.Dp(context, 5), 0);
            _filterButtons[i] = chip;
            filters.AddView(chip, new LayoutParams(0, AuroraUi.Dp(context, 45), 1f)
            { RightMargin = i == filterNames.Length - 1 ? 0 : AuroraUi.Dp(context, 5) });
            chip.Click += (_, __) =>
            {
                _stateFilter = selection;
                UpdateFilterButtons();
                ApplyFilter();
            };
        }
        header.AddView(filters, AuroraUi.ItemParams(context, 10));
        var diagnose = AuroraUi.Action(context, "Run dependency diagnostics");
        diagnose.SetAllCaps(false);
        diagnose.ContentDescription = "Show local mod compatibility warnings";
        diagnose.Click += (_, __) => ShowDiagnostics();
        header.AddView(diagnose, AuroraUi.ItemParams(context, 9));
        UpdateFilterButtons();
        search.TextChanged += (_, __) =>
        {
            _filter = search.Text?.Trim() ?? "";
            ApplyFilter();
        };

        var body = new FrameLayout(context);
        AddView(body, new LayoutParams(LayoutParams.MatchParent, 0, 1f));

        _adapter = new ModAdapter(context, _visibleMods, OnToggledMod, OnClickedMod);
        _list = new RecyclerView(context);
        _list.SetLayoutManager(new LinearLayoutManager(context));
        _list.SetAdapter(_adapter);
        _list.SetPadding(AuroraUi.Dp(context, 14), AuroraUi.Dp(context, 6),
            AuroraUi.Dp(context, 14), AuroraUi.Dp(context, 94));
        _list.SetClipToPadding(false);
        _list.VerticalScrollBarEnabled = false;
        _list.SetItemAnimator(new DefaultItemAnimator());
        body.AddView(_list, new FrameLayout.LayoutParams(
            LayoutParams.MatchParent, LayoutParams.MatchParent));

        _empty = AuroraUi.Text(context, "No mods found.\nTap + to import a mod ZIP.", 15, AuroraUi.Muted);
        _empty.Gravity = GravityFlags.Center;
        body.AddView(_empty, new FrameLayout.LayoutParams(
            LayoutParams.MatchParent, LayoutParams.MatchParent));

        InstallFab = new FloatingActionButton(context);
        InstallFab.SetImageResource(Android.Resource.Drawable.IcInputAdd);
        InstallFab.BackgroundTintList = Android.Content.Res.ColorStateList.ValueOf(AuroraUi.Accent);
        InstallFab.Click += (_, __) => ModInstaller.OnClickInstallMod(RefreshMods);
        AuroraUi.AddPressAnimation(InstallFab);
        var installLayout = new FrameLayout.LayoutParams(
            LayoutParams.WrapContent, LayoutParams.WrapContent)
        {
            Gravity = GravityFlags.End | GravityFlags.Bottom,
            BottomMargin = AuroraUi.Dp(context, 22),
            RightMargin = AuroraUi.Dp(context, 24)
        };
        body.AddView(InstallFab, installLayout);
        RefreshMods();
    }

    public void RefreshMods()
    {
        _allMods.Clear();
        try
        {
            var files = new List<string>();
            ModTool.FindManifestFile(ModTool.ModsDir, files);
            for (int i = 0; i < files.Count; i++)
                _allMods.Add(new ModInfo(files[i], i));
        }
        catch (Exception error)
        {
            ErrorDialogTool.Show(error);
        }
        AuroraModHealth.Scan(_allMods);
        ApplyFilter();
    }

    private void ApplyFilter()
    {
        _visibleMods.Clear();
        foreach (var mod in _allMods.OrderBy(m => m.modName, StringComparer.OrdinalIgnoreCase))
        {
            var matchesText = _filter.Length == 0
                || mod.modName.Contains(_filter, StringComparison.OrdinalIgnoreCase);
            var matchesState = _stateFilter == 0
                || (_stateFilter == 3 && AuroraModHealth.GetIssues(mod).Count > 0)
                || (_stateFilter is 1 or 2 && mod.Enabled == (_stateFilter == 1));
            if (matchesText && matchesState)
                _visibleMods.Add(mod);
        }
        _adapter.NotifyDataSetChanged();
        _empty.Visibility = _visibleMods.Count == 0 ? ViewStates.Visible : ViewStates.Gone;
        _list.Visibility = _visibleMods.Count == 0 ? ViewStates.Gone : ViewStates.Visible;
        RefreshCounts();
    }

    private void UpdateFilterButtons()
    {
        for (int i = 0; i < _filterButtons.Length; i++)
        {
            var selected = i == _stateFilter;
            var button = _filterButtons[i];
            button.SetTextColor(selected ? AuroraUi.Background : AuroraUi.Muted);
            AuroraUi.Ripple(button, AuroraUi.Solid(_context,
                selected ? AuroraUi.AccentSoft : AuroraUi.SurfaceRaised, 13, !selected));
        }
    }

    private void RefreshCounts()
    {
        int enabled = _allMods.Count(mod => mod.Enabled);
        int disabled = _allMods.Count - enabled;
        int warningCount = _allMods.Count(mod => AuroraModHealth.GetIssues(mod).Count > 0);
        _counts.Text = $"{_allMods.Count} installed · {enabled} enabled · {disabled} disabled · {warningCount} need attention";
    }

    private void OnToggledMod(ModInfo mod)
    {
        // The switch callback may run during RecyclerView layout; defer list refresh.
        Post(() =>
        {
            AuroraModHealth.Scan(_allMods);
            ApplyFilter();
        });
    }

    private void ShowDiagnostics()
    {
        AuroraModHealth.Scan(_allMods);
        ApplyFilter();
        var problems = _allMods
            .Select(mod => new { mod, issues = AuroraModHealth.GetIssues(mod) })
            .Where(item => item.issues.Count > 0)
            .ToList();
        var body = problems.Count == 0
            ? "No manifest or required dependency issues found. Android compatibility is not guaranteed."
            : string.Join("\n\n", problems.Take(18).Select(item =>
                item.mod.modName + "\n• " + string.Join("\n• ", item.issues))) +
                (problems.Count > 18 ? "\n\nMore mods have warnings; use the Issues filter." : "");
        new AlertDialog.Builder(_context)
            .SetTitle($"Dependency diagnostics · {problems.Count} affected mods")
            .SetMessage(body)
            .SetPositiveButton("OK", (_, __) => { })
            .Show();
    }


    private void OnClickedMod(ModInfo mod, View anchor)
    {
        var menu = new PopupMenu(_context, anchor);
        menu.Menu!.Add(0, 1, 0, "Open folder");
        menu.Menu.Add(0, 2, 1, "Delete mod");
        menu.Menu.Add(0, 3, 2, "Check dependencies");
        menu.MenuItemClick += (_, e) =>
        {
            if (e.Item?.ItemId == 1)
            {
                try { FileTool.OpenAppFiles(mod.ModFolderPath); }
                catch (Exception ex) { Toast.MakeText(_context, ex.Message, ToastLength.Short)?.Show(); }
            }
            else if (e.Item?.ItemId == 3)
            {
                var issues = AuroraModHealth.GetIssues(mod);
                new AlertDialog.Builder(_context)
                    .SetTitle(mod.modName)
                    .SetMessage(issues.Count == 0
                        ? "No required dependency problems detected. Android compatibility is not guaranteed."
                        : "Compatibility warnings:\n• " + string.Join("\n• ", issues))
                    .SetPositiveButton("OK", (_, __) => { })
                    .Show();
            }
            else if (e.Item?.ItemId == 2)
            {
                new AlertDialog.Builder(_context)
                    .SetTitle("Delete " + mod.modName + "?")
                    .SetMessage("This will remove the mod files. Game saves are not deleted.")
                    .SetPositiveButton("Delete", (_, __) =>
                    {
                        if (ModInstaller.TryDeleteMod(mod.ModFolderPath)) RefreshMods();
                    })
                    .SetNegativeButton("Cancel", (_, __) => { })
                    .Show();
            }
        };
        menu.Show();
    }
}