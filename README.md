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
            notifyAll();
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
    wait(deadline - now());
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
} elif (condition2) {
    statements2
...
}
```

It is equivalent to 

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

## Manual barrier

```scala
monitor Barrier(maxArrivals: Int) {
    private var nArrivals: Int

    def arrive() {
        nArrivals++
        wait nArrivals >= maxArrivals
    }
}
```

## Automatically reset barrier

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

## Events Zoo

### Manual event

```scala
monitor Event {
    private var pulsedAll: Boolean

    def pulseAll() {
        pulsedAll = true
    }
    def wait() {
        wait pulsedAll
    }
}
```

### Manual event with `pulseOne`

```scala
monitor Event {
    private var pulsedOne: Boolean
    private var pulsedAll: Boolean

    def pulseOne() {
        pulsedOne = true
    }
    def pulseAll() {
        pulsedAll = true
    }
    def wait() {
        wait pulsedOne or pulsedAll
        if (pulsedOne) {
            pulsedOne = false
        }
    }
}
```

### Automatically reset event

```scala
monitor AutoEvent {
    private var pulse: Int

    def pulseAll() {
        pulse++
    }
    def wait() {
        val nextPulse = pulse + 1
        wait pulse >= nextPulse
    }
}
```

### Manual event supporting `reset`

```scala
monitor Event {
    private var pulse: Int
    private var pulsed: Boolean

    def pulseAll() {
        pulse++
        pulsed = true
    }
    def wait() {
        if (not pulsed) {
            val nextPulse = pulse + 1
            wait pulse >= nextPulse
        }
    }
    def reset() {
        pulsed = false
    }
}
```

### Automatically reset event with `pulseOne`

```scala
monitor AutoEvent {
    private var nPulsed: Int
    private var nPending: Int

    def pulseOne() {
        nPulsed++
    }
    def pulseAll() {
        nPulsed = nPending
    }
    def wait() {
        nPending++
        val id = nPending
        wait nPulsed >= id
    }
}
```

### Manual event supporting `reset` and `pulseOne`

```scala
monitor Event {
    private var nPulsed: Int
    private var nPending: Int

    def pulseOne() {
        nPulsed++
    }
    def pulseAll() {
        nPulsed = +INFINITY
    }
    def wait() {
        nPending++
        val id = nPending
        wait nPulsed >= id
    }
    def reset() {
        nPulsed = nPending
    }
}
```

## Condition Variable, Mutex, and Semaphore

### Condition variable

Note that `Condition` is just a class, since we use `AutoEvent`

```scala
class Condition(mutex: Mutex) {
	private val event = new AutoEvent

	def await() {
		mutex.unlock()
		try {
    		event.wait()
	    } finally {
		    mutex.lock()
	    }
	}
	def signal() {
		event.pulseOne()
	}
	def signalAll() {
		event.pulseAll()
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
	def condition(): Condition = new Condition(this)
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
	def tryAcquire(timeout: Duration): Boolean = {
		wait nUnits > 0 for timeout
		if (nUnits > 0) {
			nUnits--
			true
        } else false
	}
}
```

## Read/Write Mutex Zoo

### Read/write mutex

```scala
monitor ReadWriteMutex {
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

### Up-prioritizing write-access requests

```scala
monitor ReadWriteMutex {
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

## Blocking Queue Zoo

### Unbounded blocking queue

```scala
monitor UnboundedBlockingQueue[V] {
	private val queue = new Queue[V]

	def enqueue(value: V) {
		queue.enqueue(value)
	}
	def dequeue(): V = {
		wait not queue.empty()
		queue.dequeue()
	}
}
```

### Bounded blocking queue

```scala
monitor BlockingQueue[V](capacity: Int) {
	private val queue = new Queue[V]

	def enqueue(value: V) {
		wait queue.size() < capacity
		queue.enqueue(value)
	}
	def dequeue(): V = {
		wait not queue.empty()
		queue.dequeue()
	}
}
```

## Delay Queue Zoo

### Using Dijkstra’s while loop.

```scala
monitor DelayQueue[V] {
	case class Entry(value: V, when: Time)

	private val queue = new PriorityQueue[Entry](e => e.when)

	def enqueue(value: V, timeout: Duration) {
		queue.enqueue(Entry(value, now() + timeout))
	}
	def dequeue(): V = {
		while (queue.empty()) {
			wait()
		} elif (queue.top().when > now()) {
			wait(queue.top().when - now())
		}
		queue.dequeue().value
    }
}
```

### Delay queue with `wait until`-statement

```scala
monitor DelayQueue[V] {
	case class Entry(value: V, when: Time)

	private val queue = new PriorityQueue[Entry](e => e.when)

	def enqueue(value: V, timeout: Duration) {
		queue.enqueue(Entry(value, now() + timeout))
	}
	def dequeue(): V = {
           wait not queue.empty() and queue.top().when <= now()
                   until if (queue.empty()) INFINITY else queue.top().when

		queue.dequeue().value
	}
}
```

## Advanced Syncronization

### Delay executor

class DelayExecutor(exec: Executor) {
	private val queue = new DelayQueue[Runnable]
	private val worker = new Thread {
	    override def run() {
		    while (true) {
			    exec.execute(queue.dequeue())
		    }
	    }
    }
	worker.start()

	def execute(r: Runnable, timeout: Duration = 0) {
		if (timeout == 0) {
			exec.execute(r)
		} else {
		    queue.enqueue(r, timeout)
	    }
	}
}
```

### Dealine map

```
monitor DeadlineMap[K, V] {
	class MEntry(var value: V, var it: DelayQueue[Entry].iterator=_)

	private val queue = new DelayQueue[K]
	private val table = new HashMap[K, MEntry]
	private val worker = new Thread {
	    override def run() {
		    while (true) {
			    remove(queue.dequeue().key)
		    }
	    }
	}
	worker.start()

	def containsKey(key K): Boolean = table.containsKey(key)
	def get(key: K, defaultVal: V): V =
        if (table.containsKey(key)) table.get(key).value else null
	def put(key: K, value: V) {
		if (table.containsKey(key)) {
		    table.get(key).value = value
	    } else {
		    table.put(key, new MEntry(value))
	    }
	}
	def remove(key: K, timeout: Duration = 0) {
		if (table.containsKey(key)) {
			val e = table.get(key)
		    if (e.it != null) {
			    e.it.remove()
			}
            if (timeout > 0) {
                e.it = queue.enqueue(key, timeout)
            } else {
	            table.remove(key)
            }
		}
	}
}
```

