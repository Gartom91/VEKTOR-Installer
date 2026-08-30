from __future__ import annotations

import base64
import json
import os
import secrets
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from pydantic import ConfigDict

from .updater import PROTOCOL, UpdateError, UpdateManager


class PathRequest(BaseModel):
    path: str


class WriteRequest(BaseModel):
    path: str
    content: str = Field(max_length=5_000_000)
    overwrite: bool = False


class ElevatedRequest(BaseModel):
    command: str = Field(min_length=1, max_length=20_000)
    cwd: str = "C:\\"
    timeout: int = Field(60, ge=1, le=600)
    reason: str = Field(min_length=5, max_length=1000)


class DesktopActionRequest(BaseModel):
    action: str
    x: int | None = None
    y: int | None = None
    text: str = Field("", max_length=5000)


def configured_roots() -> list[Path]:
    raw = os.environ.get("HOST_BROKER_ROOTS", "C:\\")
    return [Path(item).resolve() for item in raw.split(";") if item.strip()]


def resolve_host_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        raise HTTPException(400, "An absolute Windows path is required")
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise HTTPException(400, f"Cannot resolve path: {exc}") from exc
    roots = configured_roots()
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise HTTPException(403, "Path is outside HOST_BROKER_ROOTS")
    return resolved


def authorize(authorization: str = Header(default="")) -> None:
    expected = os.environ.get("HOST_BROKER_TOKEN", "")
    supplied = authorization.removeprefix("Bearer ")
    if not expected or not secrets.compare_digest(supplied, expected):
        raise HTTPException(401, "Invalid host broker credential")


def authorize_host_tools(authorization: str = Header(default="")) -> None:
    authorize(authorization)
    if os.environ.get("HOST_BROKER_TOOLS_ENABLED", "true").lower() != "true":
        raise HTTPException(403, "Windows tools are disabled; this module only manages updates and diagnostics")


@asynccontextmanager
async def lifespan(application):
    application.state.updater = None
    application.state.updater_error = "Uruchom VEKTORA ze skrótu, aby skonfigurować aktualizacje."
    root = os.environ.get("VEKTOR_INSTALL_ROOT")
    if root and os.environ.get("HOST_BROKER_TOKEN"):
        try:
            updater = UpdateManager(Path(root), os.environ.get("VEKTOR_APP_URL", "http://127.0.0.1:8765"), os.environ["HOST_BROKER_TOKEN"])
            updater.start()
            application.state.updater = updater
        except Exception as exc:
            application.state.updater_error = str(exc) if isinstance(exc, UpdateError) else "Nie można uruchomić modułu aktualizacji. Sprawdź pliki instalacji."
    try:
        yield
    finally:
        if application.state.updater:
            application.state.updater.stop()


app = FastAPI(
    title="Local Agent Windows Host Broker",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "platform": os.name,
        "configured_root_count": len(configured_roots()),
        "elevation": "per-request-uac",
        "update_protocol": PROTOCOL,
        "updates_enabled": bool(getattr(app.state, "updater", None)),
        "host_tools_enabled": os.environ.get("HOST_BROKER_TOOLS_ENABLED", "true").lower() == "true",
    }


@app.get("/v1/system/metrics", dependencies=[Depends(authorize)])
def system_metrics() -> dict[str, Any]:
    metrics: dict[str, Any] = {"gpus": [], "cpu_percent": None}
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                name, load, used, total = [part.strip() for part in line.split(",")]
                metrics["gpus"].append({"name": name, "utilization_percent": float(load), "memory_used_mb": float(used), "memory_total_mb": float(total)})
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter \"Name='_Total'\").PercentProcessorTime"], capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            metrics["cpu_percent"] = float(result.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return metrics


@app.post("/v1/filesystem/list", dependencies=[Depends(authorize_host_tools)])
def list_directory(body: PathRequest) -> dict[str, Any]:
    path = resolve_host_path(body.path)
    if not path.is_dir():
        raise HTTPException(400, "Path is not a directory")
    entries = []
    try:
        for item in path.iterdir():
            try:
                stat = item.stat()
                entries.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )
            except OSError as exc:
                entries.append({"name": item.name, "path": str(item), "error": str(exc)})
            if len(entries) >= 2000:
                break
    except PermissionError as exc:
        raise HTTPException(403, f"Windows denied directory access: {exc}") from exc
    return {"path": str(path), "entries": entries, "truncated": len(entries) >= 2000}


@app.post("/v1/filesystem/read", dependencies=[Depends(authorize_host_tools)])
def read_file(body: PathRequest) -> dict[str, Any]:
    path = resolve_host_path(body.path)
    if not path.is_file():
        raise HTTPException(400, "Path is not a file")
    try:
        size = path.stat().st_size
        if size > 5_000_000:
            raise HTTPException(413, "Host file exceeds the 5 MB read limit")
        return {
            "path": str(path),
            "content": path.read_text(encoding="utf-8", errors="replace"),
            "size": size,
        }
    except PermissionError as exc:
        raise HTTPException(403, f"Windows denied file access: {exc}") from exc


@app.post("/v1/filesystem/write", dependencies=[Depends(authorize_host_tools)])
def write_file(body: WriteRequest) -> dict[str, Any]:
    path = resolve_host_path(body.path)
    if path.exists() and not body.overwrite:
        raise HTTPException(409, "File exists; set overwrite=true in the approved request")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        temporary.write_text(body.content, encoding="utf-8")
        temporary.replace(path)
        return {"path": str(path), "bytes": path.stat().st_size}
    except PermissionError as exc:
        raise HTTPException(403, f"Windows denied file write: {exc}") from exc


@app.post("/v1/filesystem/info", dependencies=[Depends(authorize_host_tools)])
def file_info(body: PathRequest) -> dict[str, Any]:
    path = resolve_host_path(body.path)
    try:
        stat = path.stat()
        return {
            "path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }
    except PermissionError as exc:
        raise HTTPException(403, f"Windows denied metadata access: {exc}") from exc


@app.post("/v1/desktop/screenshot", dependencies=[Depends(authorize_host_tools)])
def desktop_screenshot() -> dict[str, Any]:
    if os.name != "nt":
        raise HTTPException(501, "Desktop capture is available only on Windows")
    output = Path(tempfile.gettempdir()) / f"local-agent-screen-{uuid4().hex}.png"
    script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bitmap.Size)
$bitmap.Save('{str(output).replace("'", "''")}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose(); $bitmap.Dispose()
"""
    process = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0 or not output.exists():
        raise HTTPException(500, f"Screenshot failed: {process.stderr[:500]}")
    try:
        data = output.read_bytes()
        return {"mime_type": "image/png", "base64": base64.b64encode(data).decode("ascii")}
    finally:
        output.unlink(missing_ok=True)


@app.post("/v1/desktop/action", dependencies=[Depends(authorize_host_tools)])
def desktop_action(body: DesktopActionRequest) -> dict[str, Any]:
    if os.name != "nt":
        raise HTTPException(501, "Desktop control is available only on Windows")
    if body.action not in {"move", "click", "double_click", "type", "keypress"}:
        raise HTTPException(422, "Unsupported desktop action")
    payload = base64.b64encode(body.text.encode("utf-16-le")).decode("ascii")
    x, y = body.x or 0, body.y or 0
    script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System; using System.Runtime.InteropServices;
public class NativeMouse {{
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int X,int Y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,UIntPtr e);
}}
'@
$action='{body.action}'; $x={x}; $y={y}
if($action -in @('move','click','double_click')){{[NativeMouse]::SetCursorPos($x,$y)|Out-Null}}
if($action -in @('click','double_click')){{[NativeMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[NativeMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)}}
if($action -eq 'double_click'){{Start-Sleep -Milliseconds 80;[NativeMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[NativeMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)}}
if($action -in @('type','keypress')){{$t=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('{payload}'));[System.Windows.Forms.SendKeys]::SendWait($t)}}
"""
    process = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise HTTPException(500, f"Desktop action failed: {process.stderr[:500]}")
    return {"performed": body.action, "x": body.x, "y": body.y}


@app.post("/v1/elevated/execute", dependencies=[Depends(authorize_host_tools)])
def elevated_execute(body: ElevatedRequest) -> dict[str, Any]:
    if os.name != "nt":
        raise HTTPException(501, "Elevation is available only from the Windows host broker")
    cwd = resolve_host_path(body.cwd)
    if not cwd.is_dir():
        raise HTTPException(400, "Elevated cwd is not a directory")
    result_path = Path(tempfile.gettempdir()) / f"local-agent-elevated-{uuid4().hex}.json"
    command_b64 = base64.b64encode(body.command.encode("utf-8")).decode("ascii")
    wrapper = f"""
$ErrorActionPreference = 'Stop'
$result = @{{ stdout = ''; stderr = ''; exit_code = 1; duration = 0 }}
$started = [System.Diagnostics.Stopwatch]::StartNew()
try {{
  Set-Location -LiteralPath '{str(cwd).replace("'", "''")}'
  $command = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{command_b64}'))
  $output = & ([ScriptBlock]::Create($command)) 2>&1 | Out-String
  $result.stdout = $output
  $result.exit_code = if ($null -eq $LASTEXITCODE) {{ 0 }} else {{ $LASTEXITCODE }}
}} catch {{
  $result.stderr = $_ | Out-String
  $result.exit_code = 1
}}
$started.Stop()
$result.duration = $started.Elapsed.TotalSeconds
$result | ConvertTo-Json -Compress | Set-Content -LiteralPath '{str(result_path).replace("'", "''")}' -Encoding UTF8
"""
    encoded_wrapper = base64.b64encode(wrapper.encode("utf-16-le")).decode("ascii")
    launcher = (
        "$p=Start-Process -FilePath 'powershell.exe' "
        f"-ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand','{encoded_wrapper}') "
        "-Verb RunAs -Wait -PassThru; exit $p.ExitCode"
    )
    started = time.perf_counter()
    try:
        process = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", launcher],
            capture_output=True,
            text=True,
            timeout=body.timeout + 30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "Elevated process timed out after UAC") from exc
    if process.returncode != 0 or not result_path.exists():
        raise HTTPException(
            409,
            "Elevation was cancelled or the elevated process failed before returning a result",
        )
    try:
        result = json.loads(result_path.read_text(encoding="utf-8-sig"))
        result["broker_duration"] = time.perf_counter() - started
        result["elevated"] = True
        result["reason"] = body.reason
        return result
    finally:
        result_path.unlink(missing_ok=True)


class UpdaterSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    auto_check: bool | None = None
    auto_install: bool | None = None
    interval_hours: int | None = Field(None, ge=1, le=168)
    idle_minutes: int | None = Field(None, ge=1, le=120)


class InstallUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    confirmed: bool


def update_service():
    manager = getattr(app.state, "updater", None)
    if not manager:
        raise HTTPException(503, getattr(app.state, "updater_error", "Moduł aktualizacji nie jest skonfigurowany."))
    return manager


def update_action(action):
    try:
        return action()
    except UpdateError as exc:
        raise HTTPException(409, str(exc)) from None


@app.get("/v1/updates", dependencies=[Depends(authorize)])
def update_status():
    return update_service().status()


@app.patch("/v1/updates/settings", dependencies=[Depends(authorize)])
def update_settings(body: UpdaterSettings):
    return update_action(lambda: update_service().configure(body.model_dump(exclude_none=True)))


@app.post("/v1/updates/check", dependencies=[Depends(authorize)])
def check_update():
    return update_action(lambda: update_service().request_check())


@app.post("/v1/updates/install", dependencies=[Depends(authorize)])
def install_update(body: InstallUpdate):
    if not body.confirmed:
        raise HTTPException(400, "Potwierdź instalację aktualizacji.")
    return update_action(lambda: update_service().request_install())


@app.post("/v1/updates/cancel", dependencies=[Depends(authorize)])
def cancel_update():
    return update_action(lambda: update_service().cancel())
