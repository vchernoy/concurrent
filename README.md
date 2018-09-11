# Mutex + Condition Variable = Monitor (C. A. R. Hoare)

## Scala++

### `monitor` -- the extension of `class`

```scala
monitor Monitor(value: Type) {
    def foo() {
        statements
    }
    ...
}
```

It is equivalent to:

```scala
class Monitor(value: Type) {
    synchronized def foo() {
        try {
            statements
        } finally {
            this.notifyAll;
        }
    }
    ...
}
```

### `wait`-statement

```scala
wait condition until deadline
```

* `condition` is a boolean expression, evaluated on each loop iteration.
* `deadline` is of type Time, computed on each iteration.

Wait for `condition` to become `true` until `deadline` occurs.

It is equivalent to

```scala
while (!condition && deadline > now()) {
    this.wait(deadline - now());
}
```

#### Shorter forms of `wait`

```scala
wait condition
```

The statement is unblocked when the `condition` becomes `true`.

```scala
wait until deadline
```

It just waits till system time reaches the given `deadline`.

#### `wait for`-statement

```scala
wait condition for timeout
```

This is equivalent to

```scala
val beg = now()
wait condition until beg + timeout
```

It also has the following short forms, like:

```scala
wait condition
wait for timeout
```

### Dijkstra’s while loop.

```scala
while (condition1) {
    statements1
} else if (condition2) {
    statements2
...
}
```

I find `elif` is nicer than `else if`, but it is very unusual for Java/Scala world.

The Dijkstra's while loop is equivalent to

```scala
while (true) {
    if (condition1) {
        statements1
    } else if (condition2) {
        statements2
    ...
    } else {
        break;
    }
}
```

### Boolean operators

We prefer to use `not`, `or`, `and` over `!`, `||`, `&&`.

## Basic Primitives of Syncronization

### Atomic Increment

```scala
monitor AtomicInc(var value: Int = 0) {
    def get = value
    def incAndGet: Int = {
        value++
        value
    }
    def set(v: Int) {
        value = v
    }
    def waitUntilExceeds(v: Int) {
        wait value > v
    }
}
```

### Compare and Swap (CaS)

```scala
monitor CompareAndSwap[V](var value: V = _) {
    def get = value
    def cas(prevValue: V, newValue: V): Boolean =
        if (value == prevValue) {
            value = newValue
            true
        } else false
}
```

## Barries

### Manual Barrier

```scala
monitor Barrier(maxArrivals: Int) {
    private var nArrivals: Int

    def arrive() {
        nArrivals++
        wait nArrivals >= maxArrivals
    }
}
```

### Automatically reset Barrier

```scala
monitor AutoBarrier(maxArrivals: Int) {
    private var nArrivals: Int

    def arrive() {
        nArrivals++
        thisMaxArrivals = nArrivals - nArrivals % maxArrivals + maxArrivals
        wait nArrivals >= thisMaxArrivals
    }
}
```

## Events

### Manual Event

```scala
monitor Event {
    private var signaled: Boolean

    def signal() {
        signaled = true
    }
    def wait() {
        wait signaled
    }
    def reset() {
        signaled = false
    }
}
```

### Auto Event with `signalOne`

```scala
monitor AutoEvent {
    private var signaled: Boolean

    def signal() {
        signaled = true
    }
    def wait() {
        wait signaled
        signaled = false
    }
}
```

### Condition Event

```scala
monitor ConditionEvent {
    private var nSignaled: Int
    private var nPending: Int

    def signal() {
        nSignaled++
    }
    def signalAll() {
        nSignaled = nPending
    }
    def wait() {
        val id = nPending
        nPending++
        wait nSignaled > id
    }
}
```

## Condition Variables, Mutexes, and Semaphores

### Condition Variable

Note that `ConditionVar` is just a class, since we use `ConditionEvent`

```scala
class ConditionVar(mutex: Mutex) {
    private val event = new ConditionEvent

    def await() {
        mutex.unlock
        try {
            event.wait
        } finally {
            mutex.lock
        }
    }
    def notify() {
        event.signal
    }
    def notifyAll() {
        event.signalAll
    }
}
```

### Mutex

```scala
monitor Mutex {
    private var locked: Boolean

    def isLocked = locked
    def lock() {
        wait not locked
        locked = true
    }
    def unlock() {
        locked = false
    }
    def tryLock(timeout: Duration = 0): Boolean = {
        wait not locked for timeout
        if (not locked) {
            locked = true
            true
        } else false
    }
    def conditionVar(): ConditionVar = new ConditionVar(this)
}
```

### Semaphore

```scala
monitor Semaphore(nUnits: Int = 0) {
    def release() {
        nUnits++
    }
    def acquire() {
        wait nUnits > 0
        nUnits--
    }
    def tryAcquire(timeout: Duration = 0): Boolean = {
        wait nUnits > 0 for timeout
        if (nUnits > 0) {
            nUnits--
            true
        } else false
    }
}
```

## Read/Write Locks

### Read/Write Lock

```scala
monitor ReadWriteLock {
    private var nReaders: Int
    private var nWriters: Int

    def lockRead() {
        wait nWriters == 0
        nReaders++
    }
    def unlockRead() {
        nReaders--
    }
    def lockWrite() {
        wait nWriters + nReaders == 0
        nWriters++
    }
    def unlockWrite() {
        nWriters--
    }
}
```

### Read/Write Lock with up-prioritizing write-access requests

```scala
monitor ReadWriteLock {
    private var nReaders: Int
    private var nWriters: Int
    private var nWriteReqs: Int

    def lockRead() {
        wait nWriters + nWriteReqs == 0
        nReaders++
    }
    def unlockRead() {
        nReaders--
    }
    def lockWrite() {
        nWriteReqs++
        wait nWriters + nReaders == 0
        nWriteReqs--
        nWriters++
    }
    def unlockWrite() {
        nWriters--
    }
}
```

## Blocking Queues

### Unbounded Blocking Queue

```scala
monitor UnboundedBlockingQueue[V] {
    private val values = new Queue[V]

    def enqueue(value: V) {
        values.enqueue(value)
    }
    def dequeue(): V = {
        wait not values.isEmpty
        values.dequeue
    }
}
```

### Bounded Blocking Queue

```scala
monitor BlockingQueue[V](capacity: Int) {
    private val values = new Queue[V]

    def enqueue(value: V) {
        wait values.size < capacity
        values.enqueue(value)
    }
    def dequeue(): V = {
        wait not values.isEmpty
        values.dequeue
    }
}
```

## Delay Queues

### Delay Queue with Dijkstra’s `while`-loop

```scala
monitor DelayQueue[V] {
    case class Entry(value: V, when: Time)

    private val entries = new PriorityQueue[Entry](e => e.when)

    def enqueue(value: V, timeout: Duration = 0) {
        entries.enqueue(Entry(value, now() + timeout))
    }
    def dequeue(): V = {
        while (entries.isEmpty) {
            this.wait
        } else if (entries.head.when > now()) {
            this.wait(entries.head.when - now())
        }
        entries.dequeue.value
    }
}
```

### Delay Queue with `wait until`-statement

```scala
monitor DelayQueue[V] {
    case class Entry(value: V, when: Time)

    private val entries = new PriorityQueue[Entry]()(Ordering.by{e => -e.when})

    def enqueue(value: V, timeout: Duration = 0) {
        entries.enqueue(Entry(value, now() + timeout))
    }
    def dequeue(): V = {
        wait not entries.isEmpty and entries.head.when <= now()
                until if (entries.isEmpty) INFINITY else entries.head.when

        entries.dequeue.value
    }
}
```

## Advanced Syncronization

### Delay Executor

```scala
class DelayExecutor(exec: Executor) {
    private val runnables = new DelayQueue[Runnable]
    private val worker = new Thread {
        override def run() {
            while (true) {
                exec.execute(runnables.dequeue)
            }
        }
    }
    worker.start

    def execute(r: Runnable, timeout: Duration = 0) {
        if (timeout == 0) {
            exec.execute(r)
        } else {
            runnables.enqueue(r, timeout)
        }
    }
}
```

### Expire Map

```scala
monitor ExpireMap[K, V] {
    class MEntry(var value: V = _, var it: DelayQueue[Entry].iterator=_)

    private val keys = new DelayQueue[K]
    private val table = new HashMap[K, MEntry]
    private val worker = new Thread {
        override def run() {
            while (true) {
                remove(keys.dequeue)
            }
        }
    }
    worker.start

    def contains(key K): Boolean = table.contains(key)
    def get(key: K): V = table.getOrElse(key, new MEntry).value
    def put(key: K, value: V) {
        table.getOrElseUpdate(key, new MEntry).value = value
    }
    def remove(key: K, timeout: Duration = 0) {
        table.get(key) match {
            case Some(e) => {
                if (e.it != null) {
                    e.it.remove
                }
                if (timeout > 0) {
                    e.it = keys.enqueue(key, timeout)
                } else {
                    table.remove(key)
                }
            }
            case _ =>
        }
    }
}
```

