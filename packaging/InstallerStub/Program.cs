using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;

class Program
{
    static int Main()
    {
        try
        {
            var target = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "DigitalTimeWheel");
            Directory.CreateDirectory(target);
            using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("DigitalTimeWheelPayload.zip");
            if (stream == null) throw new InvalidOperationException("Installer payload is missing.");
            var temp = Path.Combine(Path.GetTempPath(), "DigitalTimeWheelPayload-" + Guid.NewGuid() + ".zip");
            using (var file = File.Create(temp)) stream.CopyTo(file);
            ZipFile.ExtractToDirectory(temp, target, true);
            File.Delete(temp);
            var startup = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.StartMenu), "Programs", "Digital Time Wheel.lnk");
            Directory.CreateDirectory(Path.GetDirectoryName(startup));
            var command = "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('" + startup.Replace("'", "''") + "');$s.TargetPath='powershell.exe';$s.Arguments='-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(target, "packaging\\run-app.ps1").Replace("'", "''") + "\"';$s.WorkingDirectory='" + target.Replace("'", "''") + "';$s.Save()";
            Process.Start(new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -Command \"" + command.Replace("\"", "\\\"") + "\"") { UseShellExecute = false, CreateNoWindow = true })?.WaitForExit();
            var uninstall = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.StartMenu), "Programs", "Digital Time Wheel Uninstall.lnk");
            var ucommand = "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('" + uninstall.Replace("'", "''") + "');$s.TargetPath='powershell.exe';$s.Arguments='-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(target, "uninstall.ps1").Replace("'", "''") + "\"';$s.Save()";
            Process.Start(new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -Command \"" + ucommand.Replace("\"", "\\\"") + "\"") { UseShellExecute = false, CreateNoWindow = true })?.WaitForExit();
            Process.Start(new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(target, "packaging\\run-app.ps1") + "\"") { UseShellExecute = true });
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.Message); return 1; }
    }
}
