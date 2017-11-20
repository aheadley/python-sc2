import sys
import signal
import time
import asyncio
import os.path
import shutil
import tempfile
import subprocess
import portpicker
import websockets

from .protocol import Protocol
from .controller import Controller

class kill_switch(object):
    _to_kill = []

    @classmethod
    def add(cls, value):
        cls._to_kill.append(value)

    @classmethod
    def kill_all(cls):
        for p in cls._to_kill:
            p._clean()

class RemoteProcess(object):
    def __init__(self, host='127.0.0.1', port=None):
        self._host = host
        if port is None:
            port = portpicker.pick_unused_port()
        self._port = port
        self._ws = None

    @property
    def ws_url(self):
        return f"ws://{self._host}:{self._port}/sc2api"

    async def _connect(self):
        for _ in range(30):
            await asyncio.sleep(1)
            try:
                ws = await websockets.connect(self.ws_url, timeout=120)
                return ws
            except ConnectionRefusedError:
                pass

        raise TimeoutError("Websocket")

    def _clean(self):
        if self._ws is not None:
            self._ws.close()
        self._ws = None

    async def __aenter__(self, *args):
        try:
            self._ws = await self._connect()
        except:
            self._clean()
            raise
        return Controller(self._ws)

    async def __aexit__(self, *args):
        self._clean()

class LocalProcess(RemoteProcess):
    def __init__(self, fullscreen=False):
        super().__init__()
        self._fullscreen = fullscreen
        self._tmp_dir = tempfile.mkdtemp(prefix='SC2_')
        self._process = None

    def _launch(self):
        from .paths import Paths
        return subprocess.Popen([
                Paths.EXECUTABLE,
                "-listen", self._host,
                "-port", str(self._port),
                "-displayMode", "1" if self._fullscreen else "0",
                "-dataDir", Paths.BASE,
                "-tempDir", self._tmp_dir
            ],
            cwd=Paths.CWD,
            #, env=run_config.env
        )

    def _clean(self):
        super()._clean()
        if self._process is not None:
            if self._process.poll() is None:
                for _ in range(3):
                    self._process.terminate()
                    time.sleep(2)
                    if self._process.poll() is not None:
                        break
                else:
                    self._process.kill()
                    self._process.wait()

        if os.path.exists(self._tmp_dir):
            shutil.rmtree(self._tmp_dir)

        self._process = None

    async def __aenter__(self, *args):
        kill_switch.add(self)

        def signal_handler(signal, frame):
            kill_switch.kill_all()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            self._process = self._launch()
        except:
            self._clean()
            raise

        return await super().__aenter__(self, *args)

    async def __aexit__(self, *args):
        kill_switch.kill_all()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        await super().__aexit__(*args)
SC2Process = LocalProcess
