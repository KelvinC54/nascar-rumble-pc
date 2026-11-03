# Focus the game window, press a key sequence, then save a screenshot.
# usage: powershell -File drive.ps1 -Keys "X,X,Return" -Shot out.png [-Delay 900]
# Keys are .NET virtual-key names (X, Return, Up, Down, Left, Right, ...); "wait" pauses one delay.
param([string]$Keys = "", [string]$Shot = "", [int]$Delay = 900)

Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Drv {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  public struct RECT { public int L, T, R, B; }
  public static void Press(byte vk, int holdMs) {
    byte sc = (byte)MapVirtualKey(vk, 0);
    keybd_event(vk, sc, 0, UIntPtr.Zero);
    System.Threading.Thread.Sleep(holdMs);
    keybd_event(vk, sc, 2, UIntPtr.Zero);
  }
}
'@
[Drv]::SetProcessDPIAware() | Out-Null
$h = (Get-Process NascarRumble_Recompiled -ErrorAction Stop).MainWindowHandle
[Drv]::ShowWindow($h, 9) | Out-Null
[Drv]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 400

foreach ($k in ($Keys -split ',' | Where-Object { $_ })) {
    if ($k -eq 'wait') { Start-Sleep -Milliseconds $Delay; continue }
    $vk = [byte][System.Windows.Forms.Keys]::$k
    [Drv]::Press($vk, 120)
    Start-Sleep -Milliseconds $Delay
}

if ($Shot) {
    $r = New-Object Drv+RECT
    [Drv]::GetWindowRect($h, [ref]$r) | Out-Null
    $bmp = New-Object Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
    [Drawing.Graphics]::FromImage($bmp).CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
    (New-Object Drawing.Bitmap $bmp, ([int]($bmp.Width / 2)), ([int]($bmp.Height / 2))).Save($Shot)
}
