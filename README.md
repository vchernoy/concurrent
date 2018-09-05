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

