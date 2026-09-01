"""Windows-side, narrowly scoped Docker updater for an existing VEKTOR stack.

No Docker socket is mounted in the application. Updates never run a downloaded
installer/script, change the Ollama service, prune images or remove user volumes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

PROTOCOL = 2
REPOSITORY = "gartom91/local-ai-agent"
DIFFUSION_REPOSITORY = "gartom91/vektor-diffusion"
RELEASE_REPOSITORY = "Gartom91/VEKTOR-Installer"
RELEASE_API = f"https://api.github.com/repos/{RELEASE_REPOSITORY}/releases/latest"
RELEASES_URL = f"https://github.com/{RELEASE_REPOSITORY}/releases/latest"
VERSION_RE = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
IMAGE_RE = re.compile(rf"^{re.escape(REPOSITORY)}:({VERSION_RE})@sha256:[a-f0-9]{{64}}$")
DIFFUSION_IMAGE_RE = re.compile(rf"^{re.escape(DIFFUSION_REPOSITORY)}:({VERSION_RE})@sha256:[a-f0-9]{{64}}$")
MANAGED_OVERRIDE_HEADER = "# Managed by VEKTOR updater. Data and other services are unchanged.\nservices:\n"
DEFAULT_SETTINGS = {"auto_check": True, "auto_install": True, "interval_hours": 6, "idle_minutes": 5}
CRITICAL_PHASES = {"backing_up", "installing", "verifying", "rolling_back"}


class UpdateError(Exception):
    pass


class AppBusy(UpdateError):
    pass


def now():
    return datetime.now(UTC).isoformat()


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(VERSION_RE, value):
        raise UpdateError("Wydanie ma nieprawidłowy numer wersji.")
    return tuple(int(p) for p in value.split("."))


def validate_release(value, tag):
    if not isinstance(value, dict):
        raise UpdateError("Nieprawidłowy manifest wydania.")
    version = value.get("version")
    version_tuple(version)
    if tag != "v" + version:
        raise UpdateError("Numer wersji manifestu nie zgadza się z wydaniem.")
    image = value.get("agentImage", "")
    match = IMAGE_RE.fullmatch(image) if isinstance(image, str) else None
    if not match or match.group(1) != version:
        raise UpdateError("Obraz musi pochodzić z oficjalnego repozytorium i być przypięty po SHA256.")
    protocol = value.get("updateProtocol")
    if type(protocol) is not int or protocol < 1:
        raise UpdateError("Wydanie nie zawiera informacji o obsłudze automatycznych aktualizacji.")
    diffusion_image = value.get("diffusionImage")
    if protocol >= 2:
        diffusion_match = DIFFUSION_IMAGE_RE.fullmatch(diffusion_image) if isinstance(diffusion_image, str) else None
        if not diffusion_match or diffusion_match.group(1) != version:
            raise UpdateError("Generator obrazów musi pochodzić z oficjalnego repozytorium i być przypięty po SHA256.")
    else:
        diffusion_image = None
    return {"version": version, "image": image, "diffusion_image": diffusion_image, "protocol": protocol,
            "url": f"https://github.com/{RELEASE_REPOSITORY}/releases/tag/{tag}"}


def parse_managed_override(content):
    match = re.fullmatch(
        re.escape(MANAGED_OVERRIDE_HEADER)
        + r"  agent:\n    image: (?P<agent>[^\r\n]+)\n"
        + r"(?:  stable-diffusion:\n    image: (?P<diffusion>[^\r\n]+)\n)?",
        content.replace("\r\n", "\n"),
    )
    if not match:
        raise UpdateError("Plik przypięcia wersji zmieniono ręcznie. Nie nadpiszę niestandardowej konfiguracji.")
    agent, diffusion = match.group("agent"), match.group("diffusion")
    if not IMAGE_RE.fullmatch(agent) and not re.fullmatch(r"sha256:[a-f0-9]{64}", agent):
        raise UpdateError("Plik przypięcia wersji zawiera nieprawidłowy obraz VEKTORA.")
    if diffusion and not DIFFUSION_IMAGE_RE.fullmatch(diffusion) and not re.fullmatch(r"sha256:[a-f0-9]{64}", diffusion):
        raise UpdateError("Plik przypięcia wersji zawiera nieprawidłowy obraz generatora.")
    return {"agent": agent, "diffusion": diffusion}


def managed_override(agent, diffusion=None):
    if not IMAGE_RE.fullmatch(agent) and not re.fullmatch(r"sha256:[a-f0-9]{64}", agent):
        raise UpdateError("Nieprawidłowy obraz VEKTORA do przypięcia.")
    if diffusion and not DIFFUSION_IMAGE_RE.fullmatch(diffusion) and not re.fullmatch(r"sha256:[a-f0-9]{64}", diffusion):
        raise UpdateError("Nieprawidłowy obraz generatora do przypięcia.")
    value = MANAGED_OVERRIDE_HEADER + "  agent:\n    image: " + agent + "\n"
    if diffusion:
        value += "  stable-diffusion:\n    image: " + diffusion + "\n"
    return value


class ReleaseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        allowed = {"github.com", "api.github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
        if parsed.scheme != "https" or parsed.hostname not in allowed or parsed.username or parsed.password or parsed.port not in {None, 443}:
            raise UpdateError("Kanał aktualizacji przekierował do niedozwolonego adresu.")
        if parsed.hostname == "github.com" and not parsed.path.startswith("/" + RELEASE_REPOSITORY + "/releases/"):
            raise UpdateError("Przekierowanie nie prowadzi do oficjalnego wydania.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_release_url(url, limit):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), ReleaseRedirects())
    request = urllib.request.Request(url, headers={"User-Agent": "VEKTOR-Updater/1", "Accept": "application/vnd.github+json"})
    try:
        with opener.open(request, timeout=20) as response:
            raw = response.read(limit + 1)
        if len(raw) > limit:
            raise UpdateError("Manifest aktualizacji jest zbyt duży.")
        return raw
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 429}:
            raise UpdateError("Limit sprawdzania wydań GitHub. Spróbuję później.") from None
        raise UpdateError(f"Nie można pobrać informacji o wydaniu (HTTP {exc.code}).") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise UpdateError("Brak połączenia z kanałem aktualizacji. Bieżąca wersja nadal działa.") from None


def latest_release():
    try:
        release = json.loads(read_release_url(RELEASE_API, 512_000))
        if release.get("draft") is not False or release.get("prerelease") is not False:
            raise UpdateError("Automatycznie instalowane są tylko stabilne, opublikowane wydania.")
        tag = release.get("tag_name", "")
        if not re.fullmatch("v" + VERSION_RE, tag):
            raise UpdateError("Nieprawidłowy identyfikator stabilnego wydania.")
        assets = [a for a in release.get("assets", []) if a.get("name") == "release.json" and a.get("state") == "uploaded"]
        if len(assets) != 1:
            raise UpdateError("To wydanie nie udostępnia manifestu aktualizacji. Sprawdź nowszy instalator.")
        asset = assets[0]
        expected = f"https://github.com/{RELEASE_REPOSITORY}/releases/download/{tag}/release.json"
        if asset.get("browser_download_url") != expected or asset.get("size", 0) > 32_000:
            raise UpdateError("Nieprawidłowy adres manifestu aktualizacji.")
        raw = read_release_url(expected, 32_000)
        checksum = asset.get("digest")
        if not isinstance(checksum, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", checksum):
            raise UpdateError("GitHub nie udostępnił sumy kontrolnej manifestu.")
        if "sha256:" + hashlib.sha256(raw).hexdigest() != checksum:
            raise UpdateError("Suma kontrolna manifestu nie zgadza się. Aktualizacja zablokowana.")
        return validate_release(json.loads(raw), tag)
    except (ValueError, TypeError, AttributeError):
        raise UpdateError("Nie można odczytać manifestu aktualizacji.") from None


def safe_path(root: Path, name: str) -> Path:
    root = root.absolute()
    if root.resolve() != root or not root.is_dir() or root == Path(root.anchor):
        raise UpdateError("Folder instalacji nie jest bezpiecznym, zwykłym katalogiem.")
    path = root / name
    if not path.is_relative_to(root) or path.resolve() != path:
        raise UpdateError("Nieprawidłowa ścieżka aktualizacji.")
    for item in [root, *root.parents, path, *path.parents]:
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if item.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                raise UpdateError("Aktualizacja nie obsługuje dowiązań w folderze instalacji.")
    return path


def atomic_json(path: Path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def compose_lock_name(root: Path):
    canonical = os.path.normcase(str(root.absolute())).rstrip("\\")
    return "Local\\VEKTOR.UpdateCompose." + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


@contextmanager
def compose_operation(root: Path):
    """Same Windows mutex as both launchers/installer; never start mid-restore."""
    if os.name != "nt":
        yield True  # The Windows launcher protocol is not offered on Linux.
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateMutexW(None, False, compose_lock_name(root))
    if not handle:
        raise UpdateError("Nie można zabezpieczyć operacji uruchamiania VEKTORA.")
    owned = False
    try:
        result = kernel.WaitForSingleObject(handle, 0)
        if result not in {0, 0x80, 0x102}:
            raise UpdateError("Błąd wspólnej blokady uruchamiania i aktualizacji.")
        owned = result in {0, 0x80}
        yield owned
    finally:
        if owned:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


class DockerStack:
    def __init__(self, root: Path, executable: str | None = None):
        self.root = root.absolute()
        safe_path(self.root, ".env")
        self.override = safe_path(self.root, "compose.update.yaml")
        config_path = safe_path(self.root, "installation.json")
        self.files = []
        self.gpu_enabled = False
        self.prefix = ["compose", "--project-directory", str(self.root)]
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
            self.prefix += ["--project-name", "vektor-desktop", "--env-file", str(self.root / ".env")]
            self.files = [self.root / "compose.yaml"]
            if config.get("GPU"):
                self.gpu_enabled = True
                self.files.append(self.root / "compose.gpu.yaml")
                self.prefix += ["--profile", "images"]
        else:
            self.files = [self.root / "docker-compose.yml"]
        for file in self.files:
            if not safe_path(self.root, file.name).is_file():
                raise UpdateError("Nie znaleziono konfiguracji Compose tej instalacji.")
        self.executable = executable or shutil.which("docker")
        if not self.executable and os.name == "nt":
            for base, suffix in ((os.environ.get("LOCALAPPDATA", ""), "Programs/DockerDesktop/resources/bin/docker.exe"),
                                 (os.environ.get("ProgramFiles", ""), "Docker/Docker/resources/bin/docker.exe")):
                if base and (Path(base) / suffix).is_file():
                    self.executable = str(Path(base) / suffix)
                    break
        if not self.executable:
            raise UpdateError("Nie znaleziono Docker CLI. Uruchom instalator VEKTORA.")

    def run(self, arguments, timeout=60):
        try:
            result = subprocess.run([self.executable, *arguments], cwd=self.root, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except subprocess.TimeoutExpired:
            raise UpdateError("Docker przekroczył czas operacji aktualizacji.") from None
        except OSError:
            raise UpdateError("Nie można uruchomić Docker CLI.") from None
        if result.returncode:
            # Docker diagnostics can include expanded environment values. Never
            # put raw stdout/stderr, compose config or credentials in the UI.
            raise UpdateError(f"Operacja Docker nie powiodła się (kod {result.returncode}). Sprawdź, czy Docker działa i ma wolne miejsce.")
        return result.stdout.strip()

    def compose(self, *arguments, timeout=120):
        files = list(self.files)
        if self.override.exists():
            safe_path(self.root, self.override.name)
            parse_managed_override(self.override.read_text(encoding="ascii"))
            files.append(self.override)
        return self.run([*self.prefix, *[part for file in files for part in ("-f", str(file))], *arguments], timeout)

    def container(self):
        identifier = self.compose("ps", "-a", "-q", "agent", timeout=20).strip()
        if not re.fullmatch(r"[a-f0-9]{12,64}", identifier):
            raise UpdateError("Nie znaleziono jednego kontenera VEKTORA w tej instalacji.")
        data = json.loads(self.run(["inspect", identifier], 20))[0]
        labels = data.get("Config", {}).get("Labels", {}) or {}
        if labels.get("com.docker.compose.service") != "agent":
            raise UpdateError("Kontener nie należy do usługi VEKTORA.")
        working = Path(labels.get("com.docker.compose.project.working_dir", "")).absolute()
        if os.path.normcase(str(working)) != os.path.normcase(str(self.root)):
            raise UpdateError("Kontener pochodzi z innego folderu instalacji.")
        configured = labels.get("com.docker.compose.project.config_files", "").split(",")
        known = {os.path.normcase(str(p)) for p in [*self.files, self.override]}
        if not configured or any(os.path.normcase(str(Path(p).absolute())) not in known for p in configured):
            raise UpdateError("Niestandardowe pliki Compose wymagają aktualizacji ręcznej.")
        image = data.get("Image", "")
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", image):
            raise UpdateError("Nie można zachować poprzedniego obrazu.")
        mounts = [m for m in data.get("Mounts", []) if m.get("Destination") == "/app/data"]
        if len(mounts) != 1 or mounts[0].get("Type") != "volume" or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", mounts[0].get("Name", "")):
            raise UpdateError("Automatyczna aktualizacja wymaga nazwanego woluminu danych VEKTORA.")
        diffusion_image = None
        if self.override.exists():
            diffusion_image = parse_managed_override(self.override.read_text(encoding="ascii"))["diffusion"]
        if not diffusion_image:
            env_path = safe_path(self.root, ".env")
            if env_path.is_file():
                values = [line.partition("=")[2].strip() for line in env_path.read_text(encoding="utf-8-sig").splitlines() if line.startswith("DIFFUSION_IMAGE=")]
                if len(values) == 1 and (DIFFUSION_IMAGE_RE.fullmatch(values[0]) or re.fullmatch(r"sha256:[a-f0-9]{64}", values[0])):
                    diffusion_image = values[0]
        if self.gpu_enabled:
            diffusion_id = self.compose("ps", "-a", "-q", "stable-diffusion", timeout=20).strip()
            if not re.fullmatch(r"[a-f0-9]{12,64}", diffusion_id):
                raise UpdateError("Nie znaleziono lokalnego generatora obrazów tej instalacji.")
            diffusion_data = json.loads(self.run(["inspect", diffusion_id], 20))[0]
            diffusion_labels = diffusion_data.get("Config", {}).get("Labels", {}) or {}
            if diffusion_labels.get("com.docker.compose.service") != "stable-diffusion":
                raise UpdateError("Kontener generatora obrazów nie należy do tej instalacji VEKTORA.")
            diffusion_image = diffusion_data.get("Image", "")
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", diffusion_image):
                raise UpdateError("Nie można zachować poprzedniego obrazu generatora.")
        return {"id": identifier, "image": image, "diffusion_image": diffusion_image, "volume": mounts[0]["Name"]}

    def download(self, release):
        self.run(["pull", release["image"]], 900)
        labels = json.loads(self.run(["image", "inspect", release["image"], "--format", "{{json .Config.Labels}}"], 30)) or {}
        if labels.get("org.opencontainers.image.version") != release["version"] or labels.get("org.vektor.update.protocol") != str(PROTOCOL):
            raise UpdateError("Pobrany obraz ma inną wersję lub nieobsługiwany protokół aktualizacji.")
        if self.gpu_enabled and release.get("diffusion_image"):
            self.run(["pull", release["diffusion_image"]], 1800)
            diffusion_labels = json.loads(self.run(["image", "inspect", release["diffusion_image"], "--format", "{{json .Config.Labels}}"], 30)) or {}
            if diffusion_labels.get("org.opencontainers.image.version") != release["version"] or diffusion_labels.get("org.vektor.diffusion.protocol") != "1":
                raise UpdateError("Pobrany generator obrazów ma inną wersję lub nieobsługiwany protokół.")

    def daemon_ready(self):
        try:
            return self.run(["info", "--format", "{{.OSType}}"], 15) == "linux"
        except UpdateError:
            return False

    def pin(self, image, diffusion_image=None):
        safe_path(self.root, self.override.name)
        temporary = safe_path(self.root, "compose.update." + uuid4().hex + ".tmp")
        with temporary.open("x", encoding="ascii") as stream:
            stream.write(managed_override(image, diffusion_image))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.override)

    def start(self):
        services = ["agent", "stable-diffusion"] if self.gpu_enabled else ["agent"]
        self.compose("up", "-d", "--no-deps", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "120", *services, timeout=150)

    def checkpoint(self, command, identifier):
        current = self.container()
        try:
            return json.loads(self.run(["exec", current["id"], "python", "-m", "app.update_snapshot", command, identifier], 300))
        except (UpdateError, ValueError):
            if command == "verify":
                raise UpdateError("Nie przeszła kontrola danych nowej wersji: integralność baz, zachowanie rozmów lub plików. Szczegóły kopii pozostają w jej manifeście.") from None
            raise UpdateError("Nie udało się utworzyć spójnej kopii danych. Sprawdź wolne miejsce, dostęp do plików i działanie kontenera.") from None

    def rollback(self, transaction):
        current = self.container()
        if current["volume"] != transaction["volume"]:
            raise UpdateError("Wolumin danych się zmienił. Automatyczne przywracanie zostało zatrzymane.")
        # A stale checkpoint must never overwrite work accepted after a lease
        # expired. Check before even stopping the current container.
        self.run(["run", "--rm", "--network", "none", "--mount", f'type=volume,source={current["volume"]},target=/app/data,readonly',
                  "--entrypoint", "python", transaction["previous_image"], "-m", "app.update_snapshot", "check-lock", transaction["id"]], 30)
        self.compose("stop", "-t", "30", "agent", timeout=45)
        helper = "vektor-update-restore-" + transaction["id"]
        try:
            self.run(["run", "--rm", "--name", helper, "--label", "org.vektor.update.transaction=" + transaction["id"],
                      "--network", "none", "--mount", f'type=volume,source={current["volume"]},target=/app/data',
                      "--entrypoint", "python", transaction["previous_image"], "-m", "app.update_snapshot", "restore", transaction["id"]], 300)
        except UpdateError:
            # Killing a timed-out Docker CLI does not stop its container. Never
            # leave a data-restoration writer running after reporting a timeout.
            try:
                details = json.loads(self.run(["inspect", helper], 15))[0]
                owned = details.get("Config", {}).get("Labels", {}).get("org.vektor.update.transaction") == transaction["id"]
                same_volume = any(m.get("Destination") == "/app/data" and m.get("Name") == current["volume"] for m in details.get("Mounts", []))
                if owned and same_volume and details.get("Image") == transaction["previous_image"]:
                    self.run(["stop", "-t", "10", helper], 25)
            except (UpdateError, ValueError, KeyError, IndexError, TypeError):
                pass  # Keep journal and app stopped; next recovery checks lease.
            raise
        self.pin(transaction["previous_image"], transaction.get("previous_diffusion_image"))
        self.start()


class AppClient:
    def __init__(self, url, token):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise UpdateError("Updater wymaga lokalnego adresu aplikacji.")
        self.url, self.token = url.rstrip("/"), token

    def request(self, path, payload=None):
        request = urllib.request.Request(self.url + "/api/updates/" + path,
                                         data=json.dumps(payload).encode() if payload is not None else None,
                                         headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *_args, **_kwargs):
                raise UpdateError("Lokalny moduł aktualizacji nie może przekierowywać żądań.")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=10) as response:
                return json.loads(response.read(1_000_000))
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                raise AppBusy("Aktualizacja czeka na zakończenie pracy i zgód we wszystkich projektach.") from None
            raise UpdateError("Aplikacja nie udostępnia gotowego modułu aktualizacji. Uruchom aktualny instalator lub VEKTORA ze skrótu.") from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise UpdateError("VEKTOR jeszcze nie odpowiada. Aktualizacja poczeka na uruchomienie aplikacji.") from None

    def runtime(self):
        return self.request("runtime")

    def prepare(self, identifier, version, idle_seconds=0):
        return self.request("prepare", {"id": identifier, "target_version": version, "idle_seconds": idle_seconds})

    def release(self, identifier):
        return self.request("release", {"id": identifier})

    def ready(self, version, timeout=120):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status = self.runtime()
                if status.get("version") == version and status.get("protocol") == PROTOCOL:
                    return status
            except UpdateError:
                pass
            time.sleep(2)
        raise UpdateError("Nowa wersja nie przeszła testu uruchomienia.")


class UpdateManager:
    def __init__(self, root: Path, app_url: str, token: str, *, stack=None, app=None, feed=latest_release):
        self.root = root.absolute()
        self.directory = safe_path(self.root, "data/updater")
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.settings_path = safe_path(self.root, "data/updater/settings.json")
        self.status_path = safe_path(self.root, "data/updater/status.json")
        self.transaction_path = safe_path(self.root, "data/updater/transaction.json")
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.stopped = threading.Event()
        self.thread = None
        self.instance_file = None
        self.stack = stack or DockerStack(self.root)
        self.app = app or AppClient(app_url, token)
        self.feed = feed
        self.settings = dict(DEFAULT_SETTINGS)
        if self.settings_path.exists():
            self.settings.update(self.validate_settings(json.loads(self.settings_path.read_text(encoding="utf-8"))))
        else:
            atomic_json(self.settings_path, self.settings)
        if not self.settings["auto_check"]:
            self.settings["auto_install"] = False
        self.state = {"phase": "idle", "message": "Sprawdzę dostępność nowych wydań.", "last_checked": None,
                      "latest_version": None, "history": [], "release": None}
        if self.status_path.exists():
            self.state.update(json.loads(self.status_path.read_text(encoding="utf-8")))
        self.manual_check = False
        self.install_requested = False
        self.failed_image = self.state.get("failed_image")
        self.next_check = 0.0
        self.downloaded = None
        if not self.transaction_path.exists() and self.state["phase"] in {"checking", "downloading", "waiting"}:
            self.phase("available" if self.state.get("release") else "idle", "Moduł uruchomiony ponownie. Sprawdzę stan przed kolejną aktualizacją.")

    @staticmethod
    def validate_settings(values):
        if not isinstance(values, dict) or set(values) - set(DEFAULT_SETTINGS):
            raise UpdateError("Nieprawidłowe ustawienia aktualizacji.")
        for key, value in values.items():
            if key in {"auto_check", "auto_install"}:
                valid = type(value) is bool
            else:
                valid = type(value) is int and 1 <= value <= (168 if key == "interval_hours" else 120)
            if not valid:
                raise UpdateError("Nieprawidłowa wartość ustawienia aktualizacji.")
        return values

    def status(self):
        with self.lock:
            return {"available": True, "protocol": PROTOCOL, "settings": dict(self.settings), **self.state,
                    "release": None, "can_install": bool(self.state.get("release") and self.state["release"]["protocol"] <= PROTOCOL and self.state["phase"] not in CRITICAL_PHASES | {"checking", "downloading", "recovery_required"}), "releases_url": RELEASES_URL}

    def phase(self, phase, message, **fields):
        with self.lock:
            if self.state.get("phase") != phase:
                fields["phase_started_at"] = now()
            self.state.update(phase=phase, message=message, **fields)
            atomic_json(self.status_path, self.state)

    def configure(self, values):
        with self.lock:
            self.settings.update(self.validate_settings(values))
            if not self.settings["auto_check"]:
                self.settings["auto_install"] = False
            atomic_json(self.settings_path, self.settings)
            if not self.settings["auto_install"] and self.state["phase"] == "waiting" and not self.install_requested:
                self.phase("available", "Wydanie jest dostępne. Automatyczna instalacja została wyłączona.")
            self.wake.set()
            return self.status()

    def request_check(self):
        with self.lock:
            if self.transaction_path.exists() or self.state["phase"] in CRITICAL_PHASES | {"downloading", "checking", "recovery_required"}:
                raise UpdateError("Poczekaj na zakończenie bieżącej operacji aktualizacji.")
            self.manual_check = True
            self.phase("checking", "Sprawdzam stabilne wydania VEKTORA…")
            self.wake.set()
            return self.status()

    def request_install(self):
        with self.lock:
            if not self.state.get("release") or self.state["phase"] not in {"available", "waiting", "error", "rolled_back"}:
                raise UpdateError("Najpierw sprawdź dostępność nowego wydania.")
            if self.state["release"]["protocol"] > PROTOCOL:
                raise UpdateError("To wydanie wymaga nowszego instalatora Windows.")
            self.install_requested = True
            self.failed_image = None
            self.phase("waiting", "Aktualizacja zostanie zainstalowana po zakończeniu zadań i oczekujących zgód.", failed_image=None)
            self.wake.set()
            return self.status()

    def cancel(self):
        with self.lock:
            if self.state["phase"] != "waiting":
                raise UpdateError("Można odwołać tylko aktualizację oczekującą na bezczynność.")
            self.install_requested = False
            self.failed_image = self.state["release"]["image"]
            self.phase("available", "Pominięto automatyczną instalację tego wydania. Możesz uruchomić ją ręcznie.", failed_image=self.failed_image)
            return self.status()

    def check(self):
        self.phase("checking", "Sprawdzam stabilne wydania VEKTORA…")
        current = self.app.runtime()
        release = self.feed()
        newer = version_tuple(release["version"]) > version_tuple(current["version"])
        if newer and release["protocol"] > PROTOCOL:
            self.phase("manual_required", "Nowe wydanie wymaga aktualizacji modułu Windows przez instalator.",
                       latest_version=release["version"], release=release, last_checked=now())
        elif newer:
            self.phase("available", "Dostępna jest nowa wersja VEKTORA.", latest_version=release["version"], release=release, last_checked=now())
        else:
            self.phase("up_to_date", "Masz aktualną wersję VEKTORA.", latest_version=release["version"], release=None, last_checked=now())
        self.next_check = time.monotonic() + self.settings["interval_hours"] * 3600

    @staticmethod
    def busy(runtime):
        return any(runtime.get(key, 0) for key in ("active_jobs", "active_runs", "pending_approvals", "active_requests", "project_deletions", "maintenance"))

    def install(self, release, *, manual=False):
        current = self.app.runtime()
        if version_tuple(release["version"]) <= version_tuple(current["version"]):
            self.install_requested = False
            self.phase("up_to_date", "Bieżąca wersja jest już aktualna.", release=None)
            return
        idle_seconds = 0 if manual else self.settings["idle_minutes"] * 60
        if self.busy(current) or current.get("idle_seconds", 0) < idle_seconds:
            self.phase("waiting", "Czekam na bezczynność oraz zakończenie zadań i zgód we wszystkich projektach.")
            return
        release_images = (release["image"], release.get("diffusion_image") if getattr(self.stack, "gpu_enabled", False) else None)
        if self.downloaded != release_images:
            self.phase("downloading", "Pobieram i weryfikuję obrazy. Możesz nadal korzystać z aplikacji.")
            self.stack.download(release)
            self.downloaded = release_images
        if not manual and not self.settings["auto_install"]:
            self.phase("available", "Obraz jest gotowy. Automatyczna instalacja została wyłączona.")
            return
        previous = self.stack.container()
        identifier = uuid4().hex
        transaction = {"id": identifier, "previous_image": previous["image"], "previous_diffusion_image": previous.get("diffusion_image"), "previous_version": current["version"],
                       "volume": previous["volume"], "release": release, "checkpoint_ready": False, "switched": False, "committed": False, "restored": False}
        atomic_json(self.transaction_path, transaction)
        try:
            self.app.prepare(identifier, release["version"], idle_seconds)
        except AppBusy:
            self.transaction_path.unlink(missing_ok=True)
            self.phase("waiting", "Pojawiło się nowe zadanie. Aktualizacja poczeka; niczego nie przerwano.")
            return
        try:
            self.phase("backing_up", "Zapisuję bezpieczną kopię danych wszystkich projektów.")
            backup = self.stack.checkpoint("create", identifier)
            transaction["checkpoint_ready"] = True
            transaction["backup"] = backup
            atomic_json(self.transaction_path, transaction)
            self.phase("installing", "Instaluję nową wersję. Okno połączy się ponownie automatycznie.")
            transaction["switched"] = True
            atomic_json(self.transaction_path, transaction)
            self.stack.pin(release["image"], release.get("diffusion_image"))
            self.stack.start()
            self.phase("verifying", "Sprawdzam uruchomienie nowej wersji i integralność zachowanych danych.")
            self.app.ready(release["version"])
            self.stack.checkpoint("verify", identifier)
            # Commit BEFORE reopening admission. An uncertain release response
            # must never roll back new work that the app may already have accepted.
            transaction["committed"] = True
            atomic_json(self.transaction_path, transaction)
            self._finish(transaction)
        except Exception as exc:
            if transaction["committed"]:
                raise UpdateError("Nowa wersja przeszła kontrolę, ale finalizacja wymaga ponownego uruchomienia modułu Windows. Dane nie będą cofane.") from None
            self._rollback(transaction, str(exc) if isinstance(exc, UpdateError) else "Nie powiodła się kontrola aktualizacji.")

    def _finish(self, transaction):
        release = transaction["release"]
        self.app.release(transaction["id"])
        self.install_requested = False
        self.failed_image = None
        history = [x for x in self.state.get("history", []) if x.get("backup") != transaction["id"]]
        history = [*history, {"version": release["version"], "at": now(), "result": "updated", "backup": transaction["id"]}][-10:]
        self.phase("completed", "VEKTOR został zaktualizowany. Odśwież okno, aby wczytać nowy interfejs.",
                   release=None, failed_image=None, history=history, backup=transaction.get("backup"), installed_version=release["version"])
        self.transaction_path.unlink(missing_ok=True)

    def _rollback(self, transaction, error):
        release = transaction["release"]
        self.failed_image = release["image"]
        self.install_requested = False
        if transaction["switched"] and not transaction.get("restored"):
            if not transaction["checkpoint_ready"]:
                raise UpdateError("Brak kompletnej kopii. Wymagane ręczne przywrócenie instalacji.")
            self.phase("rolling_back", "Kontrola nowej wersji nie powiodła się. Przywracam poprzedni obraz i kopię danych.")
            self.stack.rollback(transaction)
            self.app.ready(transaction["previous_version"])
        # Like a successful commit, a completed restoration must be durable
        # before admission reopens. A lost unlock response must not restore again.
        transaction["restored"] = True
        transaction.setdefault("rollback_error", error)
        atomic_json(self.transaction_path, transaction)
        self.app.release(transaction["id"])
        error = transaction["rollback_error"]
        history = [x for x in self.state.get("history", []) if x.get("backup") != transaction["id"]]
        history = [*history, {"version": release["version"], "at": now(), "result": "rolled_back" if transaction["switched"] else "cancelled", "backup": transaction["id"]}][-10:]
        self.phase("rolled_back" if transaction["switched"] else "error",
                   "Przywrócono poprzednią wersję i dane. " + error if transaction["switched"] else "Bieżąca wersja pozostała bez zmian. " + error,
                   failed_image=self.failed_image, history=history)
        self.transaction_path.unlink(missing_ok=True)

    def recover(self):
        if not self.transaction_path.exists():
            return
        transaction = json.loads(self.transaction_path.read_text(encoding="utf-8"))
        if not re.fullmatch(r"[a-f0-9]{32}", transaction.get("id", "")) or not re.fullmatch(r"sha256:[a-f0-9]{64}", transaction.get("previous_image", "")):
            raise UpdateError("Nieprawidłowy zapis przerwanej aktualizacji. Wymagana diagnostyka ręczna.")
        if any(type(transaction.get(key)) is not bool for key in ("switched", "checkpoint_ready", "committed")):
            raise UpdateError("Nieprawidłowy stan przerwanej aktualizacji.")
        if type(transaction.get("restored", False)) is not bool or (transaction.get("restored") and transaction["committed"]):
            raise UpdateError("Nieprawidłowy stan finalizacji aktualizacji.")
        version_tuple(transaction["previous_version"])
        release = transaction["release"]
        validate_release({"version": release["version"], "agentImage": release["image"], "diffusionImage": release.get("diffusion_image"), "updateProtocol": release["protocol"]}, "v" + release["version"])
        if transaction.get("committed"):
            self._resume_finalized_app(release["version"])
            self._finish(transaction)
            return
        if transaction.get("restored"):
            self._resume_finalized_app(transaction["previous_version"])
        self._rollback(transaction, "Wznowiono odzyskiwanie po przerwaniu pracy modułu Windows.")

    def _resume_finalized_app(self, version):
        try:
            current = self.app.runtime()
        except UpdateError:
            # After a PC restart Docker may be ready before the app. Start the
            # already-pinned image, with no data restoration or image change.
            self.stack.start()
            current = self.app.ready(version)
        if current.get("version") != version:
            raise UpdateError("Po przerwanej aktualizacji uruchomiono inną wersję. Dane pozostają bez zmian; wymagana diagnostyka.")

    def tick(self):
        with compose_operation(self.root) as owned:
            if owned:
                self._tick()

    def _tick(self):
        if self.transaction_path.exists():
            if hasattr(self.stack, "daemon_ready") and not self.stack.daemon_ready():
                return  # Startup may still be bringing Docker online. Keep journal.
            self.recover()
        should_check = self.manual_check or (self.settings["auto_check"] and time.monotonic() >= self.next_check)
        if should_check:
            self.manual_check = False
            try:
                self.check()
            except Exception as exc:
                self.next_check = time.monotonic() + 900
                self.install_requested = False
                self.phase("error", str(exc) if isinstance(exc, UpdateError) else "Nie udało się sprawdzić aktualizacji. Bieżąca wersja pozostaje bez zmian.", last_checked=now(), release=None)
                return
        release = self.state.get("release")
        if release and release["protocol"] <= PROTOCOL and (self.install_requested or (self.settings["auto_install"] and self.failed_image != release["image"])):
            self.install(release, manual=self.install_requested)

    def start(self):
        # Process-scoped file lock protects against a second host module updating
        # the same stack. An OS crash releases the lock; the journal survives.
        self.instance_file = safe_path(self.root, "data/updater/instance.lock").open("a+b")
        if self.instance_file.tell() == 0:
            self.instance_file.write(b"0")
            self.instance_file.flush()
        self.instance_file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.instance_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.instance_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.instance_file.close()
            self.instance_file = None
            raise UpdateError("Inny moduł Windows zarządza aktualizacjami tej instalacji.") from None
        self.thread = threading.Thread(target=self._loop, name="vektor-updater", daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stopped.is_set():
            try:
                self.tick()
            except Exception as exc:
                critical = self.transaction_path.exists()
                self.install_requested = False
                if self.state.get("release"):
                    self.failed_image = self.state["release"]["image"]
                self.phase("recovery_required" if critical else "error", str(exc) if isinstance(exc, UpdateError) else "Aktualizacja nie została ukończona. Sprawdź moduł Windows.", failed_image=self.failed_image)
                # Never repeatedly restore data or retry a broken release in a
                # tight loop. Recovery is attempted once on the next host start.
                if critical:
                    return
                self.next_check = time.monotonic() + 900
            self.wake.wait(30)
            self.wake.clear()

    def stop(self):
        self.stopped.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=5)
        if self.instance_file and (not self.thread or not self.thread.is_alive()):
            self.instance_file.close()
            self.instance_file = None
