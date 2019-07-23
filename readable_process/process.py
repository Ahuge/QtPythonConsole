import os
import signal
import sys
import subprocess
import time
from threading import Thread

from six import text_type
from six.moves.queue import Queue, Empty
from six.moves import cStringIO as StringIO


class ReadableProcess(object):
    def __init__(self, command):
        super(ReadableProcess, self).__init__()
        self._command = command
        self._out_pipe = StringIO()
        self._err_pipe = StringIO()
        self._stdout_t = None
        self._stderr_t = None
        self._process = None
        self._out_queue = None
        self._err_queue = None
        self._out_t = None
        self._err_t = None

    @property
    def returncode(self):
        if self._process:
            return self._process.returncode
        return 1

    def poll(self):
        if self._process:
            return self._process.poll()
        return 1

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def kill(self):
        if self._process:
            os.killpg(os.getpgid(self.pid()), signal.SIGTERM)
            self._process.terminate()

    def pid(self):
        if self._process:
            return self._process.pid

    def run(self):
        if self._process:
            raise ValueError("Already Ran")

        self._out_queue = Queue()
        self._err_queue = Queue()

        try:
            self._process = subprocess.Popen(
                self._command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
            self._stdout_t = Thread(
                target=self.enqueue_output, args=(self._process.stdout, self._out_queue)
            )
            self._stdout_t.daemon = True
            self._stderr_t = Thread(
                target=self.enqueue_output, args=(self._process.stderr, self._err_queue)
            )
            self._stderr_t.daemon = True

            self._stdout_t.start()
            self._stderr_t.start()
        except Exception:
            import traceback
            fmt = traceback.format_exc()
            for line in fmt.split("\n"):
                self._err_queue.put(line)

    def read_stdout_line(self):
        try:
            return self._out_queue.get_nowait()
        except Empty:
            return None

    def read_stdout_all(self):
        buf = []
        line = self.read_stdout_line()
        while line and line is not None:
            buf.append(text_type(line))
            line = self.read_stdout_line()
            time.sleep(0.1)
        return "\n".join(buf)

    def read_stderr_line(self):
        try:
            return self._err_queue.get_nowait()
        except Empty:
            return None

    def read_stderr_all(self):
        buf = []
        line = self.read_stderr_line()
        while line and line is not None:
            buf.append(text_type(line))
            line = self.read_stderr_line()
            time.sleep(0.1)
        return "\n".join(buf)

    def read_all(self):
        return self.read_stdout_all(), self.read_stderr_all()
