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

#### shorter forms of `wait`

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

### boolean operators

We prefer to use `not`, `or`, `and` over `!`, `||`, `&&`.

