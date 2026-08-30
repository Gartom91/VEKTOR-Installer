using System.Diagnostics;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;

namespace VektorSetup;

static class Program
{
    [STAThread]
    static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--extract") { Extract(Path.GetFullPath(args[1])); return 0; }
        ApplicationConfiguration.Initialize();
        Application.Run(new SetupWindow());
        return 0;
    }

    internal static void Extract(string path)
    {
        Directory.CreateDirectory(path);
        using var source = Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip")!;
        using var zip = new ZipArchive(source);
        zip.ExtractToDirectory(path, overwriteFiles: true);
    }
}

sealed class SetupWindow : Form
{
    readonly TextBox destination = new() { Dock = DockStyle.Fill, Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "VEKTOR") };
    readonly TextBox log = new() { Dock = DockStyle.Fill, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, BackColor = Color.FromArgb(10, 17, 26), ForeColor = Color.Gainsboro };
    readonly CheckBox terms = new() { AutoSize = true, Text = "Zgadzam się na instalację WSL2/Docker i akceptuję warunki Docker Desktop." };
    readonly CheckBox host = new() { AutoSize = true, Text = "Włącz moduł Windows (pliki, pulpit, UAC — działania nadal wymagają zgód)." };
    readonly CheckBox autostart = new() { AutoSize = true, Text = "Uruchamiaj VEKTORA po zalogowaniu do Windows.", Checked = true };
    readonly Button install = new() { Text = "Zainstaluj / napraw", AutoSize = true };
    readonly Button browse = new() { Text = "Wybierz folder…", AutoSize = true };
    readonly Button open = new() { Text = "Uruchom VEKTORA", AutoSize = true, Enabled = false };
    readonly Button cloud = new() { Text = "Zaloguj do Ollama cloud", AutoSize = true, Enabled = false };
    bool busy;

    public SetupWindow()
    {
        Text = "VEKTOR — instalator Windows 1.3.2"; Width = 900; Height = 700; MinimumSize = new Size(760, 620);
        StartPosition = FormStartPosition.CenterScreen; Font = new Font("Segoe UI", 10); BackColor = Color.FromArgb(17, 26, 39); ForeColor = Color.Gainsboro;
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(24), ColumnCount = 1, RowCount = 10 };
        for (int i = 0; i < 9; i++) layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.Controls.Add(new Label { Text = "VEKTOR", Font = new Font("Segoe UI", 25, FontStyle.Bold), ForeColor = Color.Turquoise, AutoSize = true });
        layout.Controls.Add(new Label { Text = "Windows 10/11 x64 • WSL2 • minimum 8 GB RAM • internet\nInstalacja może wymagać UAC i restartu. Twoje istniejące dane nie będą usuwane.", AutoSize = true, Margin = new Padding(0, 8, 0, 12) });
        layout.Controls.Add(destination);
        browse.Click += (_, _) => { using var dialog = new FolderBrowserDialog(); if (dialog.ShowDialog() == DialogResult.OK) destination.Text = dialog.SelectedPath; };
        layout.Controls.Add(browse);
        layout.Controls.Add(terms);
        var license = new LinkLabel { Text = "Warunki Docker Desktop (niektóre zastosowania wymagają płatnej licencji)", AutoSize = true, LinkColor = Color.Turquoise };
        license.LinkClicked += (_, _) => Process.Start(new ProcessStartInfo("https://www.docker.com/legal/docker-subscription-service-agreement/") { UseShellExecute = true });
        layout.Controls.Add(license); layout.Controls.Add(host); layout.Controls.Add(autostart);
        var actions = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill };
        actions.Controls.AddRange([install, open, cloud]); layout.Controls.Add(actions); layout.Controls.Add(log); Controls.Add(layout);
        foreach (var button in new[] { install, open, cloud, browse }) { button.ForeColor = Color.Black; button.BackColor = Color.FromArgb(92, 210, 190); }
        install.Click += async (_, _) => await InstallAsync();
        open.Click += (_, _) => Launch("Start-VEKTOR.ps1", false);
        cloud.Click += (_, _) => Launch("Cloud-Login.ps1", true);
        FormClosing += (_, e) => { if (busy) { e.Cancel = true; MessageBox.Show("Trwa instalacja. Poczekaj na jej zakończenie."); } };
    }
    void Append(string? text) { if (text is not null && !IsDisposed) BeginInvoke(() => log.AppendText(text + Environment.NewLine)); }
    void Launch(string script, bool console)
    {
        var psi = new ProcessStartInfo("powershell.exe") { UseShellExecute = true, WindowStyle = console ? ProcessWindowStyle.Normal : ProcessWindowStyle.Hidden };
        foreach (var arg in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", Path.Combine(destination.Text, script) }) psi.ArgumentList.Add(arg);
        Process.Start(psi);
    }
    async Task InstallAsync()
    {
        if (!terms.Checked) { MessageBox.Show("Przeczytaj i zaakceptuj warunki instalacji zależności."); return; }
        if (RuntimeInformation.OSArchitecture != Architecture.X64) { MessageBox.Show("To wydanie obsługuje Windows x64. ARM64 i x86 nie są obsługiwane."); return; }
        busy = true; install.Enabled = browse.Enabled = false; destination.Enabled = false; log.Clear(); open.Enabled = cloud.Enabled = false;
        string temp = Path.Combine(Path.GetTempPath(), "VEKTOR-Setup-" + Guid.NewGuid().ToString("N"));
        try
        {
            Program.Extract(temp);
            var psi = new ProcessStartInfo("powershell.exe") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (var arg in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", Path.Combine(temp, "Install-VEKTOR.ps1"), "-InstallDir", Path.GetFullPath(destination.Text), "-AcceptDockerLicense" }) psi.ArgumentList.Add(arg);
            if (host.Checked) psi.ArgumentList.Add("-EnableHost");
            if (autostart.Checked) psi.ArgumentList.Add("-Autostart");
            using var process = new Process { StartInfo = psi };
            process.OutputDataReceived += (_, e) => Append(e.Data); process.ErrorDataReceived += (_, e) => Append(e.Data);
            process.Start(); process.BeginOutputReadLine(); process.BeginErrorReadLine(); await process.WaitForExitAsync(); process.WaitForExit();
            if (process.ExitCode == 0) { Append("Gotowe. Skrót VEKTOR jest na pulpicie. Cloud wymaga Twojego logowania."); open.Enabled = cloud.Enabled = true; }
            else if (process.ExitCode == 3010) Append("Zapisano pliki instalatora. Uruchom ponownie Windows i ponów instalację. Nie usuwaj danych.");
            else Append($"Instalacja nie została ukończona (kod {process.ExitCode}). Szczegóły powyżej; możesz ponowić bez kasowania danych.");
        }
        catch (Exception ex) { Append(ex.Message); }
        finally { busy = false; install.Enabled = browse.Enabled = true; destination.Enabled = true; /* Keep extracted diagnostics/payload on failure for recovery. */ }
    }
}
