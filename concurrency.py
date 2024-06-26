from collections import defaultdict, deque
from concurrent.futures import Executor
from datetime import datetime, timedelta
from heapq import heappop, heappush
from threading import Condition, Lock, Thread


class AtomicInc:
    def __init__(self, value: int = 0):
        self.value = value
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def inc_and_get(self, v: int) -> int:
        with self.cv:
            self.value += v
            self.cv.notify_all()
            return self.value

    def set(self, v: int):
        with self.cv:
            self.value = v
            self.cv.notify_all()

    def wait_until_exceeds(self, v: int):
        with self.cv:
            self.cv.wait_for(lambda: self.value > v)


class CAS:
    def __init__(self, value: any):
        self.value = value
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def get(self) -> any:
        with self.cv:
            return self.value

    def set(self, v: any):
        with self.cv:
            self.value = v
            self.cv.notify_all()

    def cas(self, prev_value: any, new_value: any) -> bool:
        with self.cv:
            if self.value == prev_value:
                self.value = new_value
                self.cv.notify_all()
                return True
            return False


class Barrier:
    def __init__(self, max_arrivals: int):
        self.max_arrivals = max_arrivals
        self.arrivals = 0
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def arrive(self):
        with self.cv:
            self.arrivals += 1
            self.cv.wait_for(lambda: self.arrivals >= self.max_arrivals)
            self.cv.notify_all()

    def wait(self):
        with self.cv:
            self.cv.wait_for(lambda: self.arrivals >= self.max_arrivals)


class AutoBarrier:
    def __init__(self, max_arrivals: int):
        self.max_arrivals = max_arrivals
        self.arrivals = 0
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def arrive(self):
        with self.cv:
            self.arrivals += 1
            max_arrivals = (
                self.arrivals - self.arrivals % self.max_arrivals + self.max_arrivals
            )
            if self.arrivals == max_arrivals:
                self.cv.notify_all()
            else:
                self.cv.wait_for(lambda: self.arrivals >= max_arrivals)

    def wait(self):
        with self.cv:
            max_arrivals = (
                self.arrivals - self.arrivals % self.max_arrivals + self.max_arrivals
            )
            self.cv.wait_for(lambda: self.arrivals >= max_arrivals)


class Event:
    def __init__(self):
        self.signaled = False
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def signal(self):
        with self.cv:
            self.signaled = True
            self.cv.notify_all()

    def wait(self):
        with self.cv:
            self.cv.wait_for(lambda: self.signaled)

    def reset(self):
        with self.cv:
            self.signaled = False


class AutoEvent:
    def __init__(self):
        self.signaled = False
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def signal(self):
        with self.cv:
            self.signaled = True
            self.cv.notify_all()

    def wait(self):
        with self.cv:
            self.cv.wait_for(lambda: self.signaled)
            self.signaled = False


class ConditionEvent:
    def __init__(self):
        self.signaled = 0
        self.pendging = 0
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def signal(self):
        with self.cv:
            self.signaled += 1
            self.cv.notify_all()

    def signal_all(self):
        with self.cv:
            self.signaled = self.pending
            self.cv.notify_all()

    def wait(self):
        with self.cv:
            pid = self.pending
            self.pendging += 1
            self.cv.wait_for(lambda: self.signaled > pid)


class Semaphore:
    def __init__(self, value: int):
        self.value = value
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def release(self):
        with self.cv:
            self.value += 1
            self.cv.notify_all()

    def acquire(self):
        with self.cv:
            self.cv.wait_for(lambda: self.value > 0)
            self.value -= 1

    def try_acquire(self, timeout) -> bool:
        with self.cv:
            self.cv.wait_for(lambda: self.value > 0, timeout)
            if self.value > 0:
                self.value -= 1
                return True

            return False


class RWLock:
    def __init__(self):
        self.readers = 0
        self.writers = 0
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def lock_read(self):
        with self.cv:
            self.cv.wait_for(lambda: self.writers <= 0)
            self.readers += 1
            self.cv.notify_all()

    def unlock_read(self):
        with self.cv:
            self.readers -= 1
            self.cv.notify_all()

    def lock_write(self):
        with self.cv:
            self.cv.wait_for(lambda: self.writers + self.readers == 0)
            self.writers += 1
            self.cv.notify_all()

    def unlock_write(self):
        with self.cv:
            self.writers -= 1
            self.cv.notify_all()


class RWLock2:
    def __init__(self):
        self.readers = 0
        self.writers = 0
        self.pending_writers = 0
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def lock_read(self):
        with self.cv:
            self.cv.wait_for(lambda: self.writers + self.pending_writers <= 0)
            self.readers += 1
            self.cv.notify_all()

    def unlock_read(self):
        with self.cv:
            self.readers -= 1
            self.cv.notify_all()

    def lock_write(self):
        with self.cv:
            self.pending_writers += 1
            self.cv.wait_for(lambda: self.writers + self.pending_writers <= 0)
            self.pending_writers -= 1
            self.writers += 1
            self.cv.notify_all()

    def unlock_write(self):
        with self.cv:
            self.writers -= 1
            self.cv.notify_all()


class UnboundedBlockingQueue:
    def __init__(self):
        self.queue = deque()
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def enqueue(self, item: any):
        with self.cv:
            self.queue.append(item)
            self.cv.notify_all()

    def dequeue(self) -> any:
        with self.cv:
            self.cv.wait_for(lambda: bool(self.queue))
            return self.queue.popleft()


class BlockingQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.queue = deque()
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def enqueue(self, item: any):
        with self.cv:
            self.cv.wait_for(lambda: len(self.queue) < self.capacity)
            self.queue.append(item)
            self.cv.notify_all()

    def dequeue(self) -> any:
        with self.cv:
            self.cv.wait_for(lambda: bool(self.queue))
            return self.queue.popleft()


class DelayQueue:
    def __init__(self):
        self.entries: list[tuple[datetime, any]] = []
        self.lock = Lock()
        self.cv = Condition(self.lock)

    def enqueue(self, value: any, timeout: timedelta):
        with self.cv:
            heappush(self.entries, (datetime.now() + timeout, value))
            self.cv.notify_all()

    def dequeue(self) -> any:
        with self.cv:
            while not self.entries or self.entries[0][0] > datetime.now():
                if not self.entries:
                    self.cv.wait()
                else:
                    self.cv.wait((self.entries[0][0] - datetime.now()).total_seconds())

            return heappop(self.entries)[1]


class DelayExecutor:
    def __init__(self, exec: Executor):
        self.exec = exec
        self.runnables = DelayQueue()
        self.worker = Thread(target=self.run)
        self.worker.start()

    def run(self):
        while True:
            runnable = self.runnables.dequeue()
            self.exec.submit(runnable)

    def execute(self, runnable, timeout=timedelta(seconds=0)):
        if timeout == timedelta(seconds=0):
            self.exec.submit(runnable)
        else:
            self.runnables.enqueue(runnable, timeout)


class ExpireMap:
    def __init__(self):
        self.table = defaultdict(lambda: {"value": None, "when": None})
        self.keys = DelayQueue()
        self.worker = Thread(target=self._run_worker)
        self.worker.start()
        self.lock = Lock()

    def _run_worker(self):
        while True:
            key = self.keys.dequeue()
            with self.lock:
                if key in self.table:
                    when = self.table[key]["when"]
                    if when is None or when <= datetime.now():
                        del self.table[key]

    def contains(self, key):
        with self.lock:
            return key in self.table

    def get(self, key):
        with self.lock:
            return self.table[key]["value"]

    def put(self, key, value):
        with self.lock:
            self.table[key]["value"] = value

    def remove(self, key, timeout=0):
        with self.lock:
            if timeout > 0:
                when = datetime.now() + timedelta(seconds=timeout)
                self.table[key]["when"] = when
            else:
                del self.table[key]

        if timeout > 0:
            self.keys.enqueue(key, timeout)


class ExpireMap:
    def __init__(self):
        self.table = defaultdict(lambda: {"value": None, "when": None})
        self.keys = DelayQueue()
        self.worker = Thread(target=self._run_worker)
        self.worker.start()
        self.lock = Lock()

    def _run_worker(self):
        while True:
            key = self.keys.dequeue()
            with self.lock:
                if key in self.table:
                    when = self.table[key]["when"]
                    if when is None or when <= datetime.now():
                        del self.table[key]

    def contains(self, key):
        with self.lock:
            return key in self.table

    def get(self, key):
        with self.lock:
            return self.table[key]["value"]

    def put(self, key, value):
        with self.lock:
            self.table[key]["value"] = value

    def remove(self, key, timeout=0):
        with self.lock:
            if timeout > 0:
                when = datetime.now() + timedelta(seconds=timeout)
                self.table[key]["when"] = when
            else:
                del self.table[key]

        if timeout > 0:
            self.keys.enqueue(key, timeout)
