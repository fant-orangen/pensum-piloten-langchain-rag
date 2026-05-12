# Anonymized Retrieval Review

Method identities are hidden in this document. Use the separate key file after review.
Each method is normalized to the same final chunk count before answer generation.

## q1

**Question:** If I put a lock around my shared counter so that only one thread at a time can touch it, and my program still sometimes produces the wrong total, does that mean the lock is broken?

### Method A

- Retrieval latency: 0.870s
- Generation latency: 7.082s

**Answer:**

Not necessarily. If a shared counter is **always** accessed while holding the same correct lock**, then the total should be correct.

If the result is still wrong, it usually means one of these is happening:

1. **Some code path updates or reads the counter without the lock**
   ```cpp
   counter++;        // unsafe if not locked
   ```

2. **Different threads are using different locks**
   ```cpp
   lockA protects counter in one place
   lockB protects counter somewhere else
   ```
   That does not protect the counter.

3. **The lock is released too early**
   ```cpp
   lock();
   temp = counter;
   unlock();

   temp++;
   counter = temp;   // unsafe
   ```

4. **The lock implementation is wrong**
   This is possible, especially with custom spinlocks or missing memory barriers, but it is usually less likely than misuse.

So the lock is probably not “broken.” More likely, the counter is not protected consistently.

The rule is:

> Every access to the shared counter that can race must be inside the same lock’s critical section.

For example:

```cpp
lock();
counter++;
unlock();
```

If every increment really follows that pattern with the same lock, then the final count should be correct.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `029d1d5f7654354c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `163`
- Score: `n/a `

```text
is usually BUSY?
Unfortunately, the overhead of acquiring and releasing a lock can increase dramatically with
the number of threads contending for the lock. For a contended lock, this can further increase
the number of threads waiting for the lock. Consider again the example we used earlier, of a
spinlock protecting a shared counter:
    void Counter::Increment() { 
        while (test_and_set(&lock)) // while BUSY 
            ; // spin 
        value++; 
        lock = FREE; 
        memory_barrier(); 
    }
Even if many threads try to increment the same counter, only one thread at a time can execute
the critical section; the other threads must wait their turn. As we observed earlier, because
the counter value must be communicated from one lock holder to the next, the critical section
```

#### Chunk 2

- Chunk ID: `a2618dd2233bfed8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `114`
- Score: `n/a `

```text
Discussion. This is just an example of dangers that lurk when you try to elide locks; the
lesson applies more broadly. This example is extremely simple — fewer than 10 lines
of code with very simple logic — y et a number of published solutions have been wrong.
As Meyers and Alexandrescu note, some tempting solutions using temporary variables
and the volatile keyword do n ot work. Bacon et al.’s “The ’Double-Checked Locking is
Broken’ Declaration” discusses a range of non-solutions in Java.
http://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
This type of optimization is risky and often does not provide significant performance
gains in practice. Most programmers should not consider them. Even expert
```

#### Chunk 3

- Chunk ID: `6134cb7c27556687`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `165`
- Score: `n/a `

```text
value++; 
     lock = FREE; 
     memory_barrier(); 
 }
However, it turns out this does not help. W hen the lock is released, the new value of the lock,
FREE, must be communicated to the other waiting processors. On modern systems, each
processor separately fetches the data into its cache. Eventually one of them gets the new value
and acquires the lock. If the critical section is not very long, the other processors will still be
busy fetching the new value and trying to acquire the lock, preventing the lock release from
completing.
One approach is to adjust the frequency of polling to the length of time that the thread has
been waiting. A more scalable solution is to assign each waiting thread a separate memory
```

#### Chunk 4

- Chunk ID: `14af8b26ec192826`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `163`
- Score: `n/a `

```text
the counter value must be communicated from one lock holder to the next, the critical section
will take significantly longer on a multiprocessor than on a single processor.
```

#### Chunk 5

- Chunk ID: `13a0b379ab586aee`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `112`
- Score: `n/a `

```text
1. Double-Checked Locking.
We strongly advise holding a shared obj ect’s lock across any method that accesses the
object’s member variables. Programmers are often tempted to avoid some of these lock
acquire and release operations. Unfortunately, such efforts often result in code that is
complex, wrong, or both.
To illustrate the challenges, consider the doubl e-checked locking design pattern. The
canonical example is an object that is allocated and initialized lazily the first time it is
needed by any thread. (This example and analysis is taken from Meyers and
Alexandrescu, “C++ and the Perils of Double-Checked Locking.”
http://www.aristeia.com/Papers/DDJ_Jul_ Aug_2004_r evised.pdf ) Being good
```

### Method B

- Retrieval latency: 5.422s
- Generation latency: 9.378s

**Answer:**

Usually, **no — it does not mean the lock is broken**.

A lock only protects the shared counter if **every access to that counter uses the same lock correctly**.

For example, this is safe:

```c
lock.acquire();
counter++;
lock.release();
```

But the program can still get the wrong total if any of these happen:

1. **Some code touches `counter` without the lock**

```c
counter++;   // unsafe if other threads also access counter
```

2. **Different threads use different locks**

```c
// Thread A
lock1.acquire();
counter++;
lock1.release();

// Thread B
lock2.acquire();
counter++;
lock2.release();
```

That does not provide mutual exclusion.

3. **The lock protects only part of the operation**

```c
lock.acquire();
temp = counter;
lock.release();

temp++;

lock.acquire();
counter = temp;
lock.release();
```

This is still unsafe because the read-modify-write operation is split.

4. **You read the final total before all threads are finished**

You need to wait for all worker threads to complete, e.g. with `join`.

5. **The counter overflows**

If many increments happen, the integer type might wrap around.

So the key idea is:

> A lock is not magic protection for a variable. It only works if all threads follow the rule: hold the same lock whenever accessing the shared state.

If the total is wrong, look for an access to the counter that is outside the lock or protected by the wrong lock.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `029d1d5f7654354c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `163`
- Score: `3.58003 rerank_score`

```text
is usually BUSY?
Unfortunately, the overhead of acquiring and releasing a lock can increase dramatically with
the number of threads contending for the lock. For a contended lock, this can further increase
the number of threads waiting for the lock. Consider again the example we used earlier, of a
spinlock protecting a shared counter:
    void Counter::Increment() { 
        while (test_and_set(&lock)) // while BUSY 
            ; // spin 
        value++; 
        lock = FREE; 
        memory_barrier(); 
    }
Even if many threads try to increment the same counter, only one thread at a time can execute
the critical section; the other threads must wait their turn. As we observed earlier, because
the counter value must be communicated from one lock holder to the next, the critical section
```

#### Chunk 2

- Chunk ID: `259c96c1742883cf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `85`
- Score: `3.19566 rerank_score`

```text
associates each lock with some subset of shared state and requires a thread to hold the lock
when accessing that state. Then, only one thread can access the shared state at a time.
Mutual exclusion greatly simplifies reasoning about programs because a thread can perform
an arbitrary set of operations while holding a lock, and those operations appe ar to be atomic
to other threads. In particular, because a lock enforces mutual exclusion and threads must hold
the lock to access shared state, no other thread can observe an intermediate state. Other
threads can only observe the state left after the lock release.
EXAMPLE: Locking to group multiple operations. Consider, for example, a bank account
object that includes a list of transactions and a total balance. To add a new transaction, we
```

#### Chunk 3

- Chunk ID: `58d16c658efa74d5`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `154`
- Score: `2.06269 rerank_score`

```text
significantly limit server parallelism. How can we tell if the lock on a shared obj ect is going
to be a problem?
A convenient approach is to derive a bound on the performance of a parallel program by
assuming that the rest of the program is perfectly parallelizable — in other words, that the
only limiting factor is that only one thread at a time can hold the shared lock.
```

#### Chunk 4

- Chunk ID: `a0a1ed5a20d382c7`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `81`
- Score: `1.57932 rerank_score`

```text
different threads’ access to shared state.
Suppos e, for example, we had a primitive called a lock that only one thread at a time can
own. Then, we can solve the Too M uch Milk problem by defining the class for a Kitchen
object with the following method:
    Kitchen::buyIfNeeded() { 
        lock.acquire(); 
        if (milk == 0) {     // if no milk 
            milk++;          // buy milk 
        } 
        lock.release(); 
    }
After outlining a strategy for managing synchronization in the next section, we define locks
and condition variables (another type of synchronization object) in Sections 5.3 and 5.4.
5.2 Structuring Shared Objects
```

#### Chunk 5

- Chunk ID: `7529440c615e8c50`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `155`
- Score: `1.31159 rerank_score`

```text
normal program behavior, but rather as a way of isolating the effect of hardware on the
performance of code using shared obj ects.
Suppos e we set up an array of a thousand shared obj ects, where each object is a simple
integer counter protected by a spinlock. (We use a spinlock rather than a lock to avoid
measuring context switch time.) The program iterates through the array. For each item, it
acquires the lock, increments the counter, and releases the lock. We repeat the loop a
thousand times to improve measurement precision.
Consider the following scenarios:
One thread, one array. When one thread iterates through the array, incrementing each
counter in turn, the test gives the time it takes to acquire and release an array of
uncontended locks.
```

### Method C

- Retrieval latency: 6.140s
- Generation latency: 12.446s

**Answer:**

Usually, **no** — it does not mean the lock itself is broken.

If a shared counter is protected correctly, then every access that can affect the counter must use the **same lock**:

```c
lock();
counter++;
unlock();
```

If the final total is still sometimes wrong, common causes are:

1. **Some code touches the counter without the lock**

   ```c
   counter++;   // bug if done outside the lock
   ```

2. **Different threads use different locks**

   ```c
   lockA protects counter in one place
   lockB protects counter somewhere else
   ```

   That does not provide mutual exclusion.

3. **You read the final value before all threads have finished**

   You usually need something like:

   ```c
   join(thread1);
   join(thread2);
   printf("%d\n", counter);
   ```

4. **The lock implementation is incorrect**

   This is possible if you wrote your own lock, especially a spinlock, but less likely if you are using a standard mutex/library lock.

5. **Integer overflow**

   If the counter exceeds the maximum value of its type, the total can become wrong even with locking.

So the better diagnosis is:

> The lock is probably not broken; the counter is probably not consistently protected by the same lock, or the final value is being checked too early.

A lock only protects the code that actually uses it.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `029d1d5f7654354c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `163`
- Score: `0.805927 vector_distance`

```text
is usually BUSY?
Unfortunately, the overhead of acquiring and releasing a lock can increase dramatically with
the number of threads contending for the lock. For a contended lock, this can further increase
the number of threads waiting for the lock. Consider again the example we used earlier, of a
spinlock protecting a shared counter:
    void Counter::Increment() { 
        while (test_and_set(&lock)) // while BUSY 
            ; // spin 
        value++; 
        lock = FREE; 
        memory_barrier(); 
    }
Even if many threads try to increment the same counter, only one thread at a time can execute
the critical section; the other threads must wait their turn. As we observed earlier, because
the counter value must be communicated from one lock holder to the next, the critical section
```

#### Chunk 2

- Chunk ID: `7529440c615e8c50`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `155`
- Score: `0.815179 vector_distance`

```text
normal program behavior, but rather as a way of isolating the effect of hardware on the
performance of code using shared obj ects.
Suppos e we set up an array of a thousand shared obj ects, where each object is a simple
integer counter protected by a spinlock. (We use a spinlock rather than a lock to avoid
measuring context switch time.) The program iterates through the array. For each item, it
acquires the lock, increments the counter, and releases the lock. We repeat the loop a
thousand times to improve measurement precision.
Consider the following scenarios:
One thread, one array. When one thread iterates through the array, incrementing each
counter in turn, the test gives the time it takes to acquire and release an array of
uncontended locks.
```

#### Chunk 3

- Chunk ID: `a2618dd2233bfed8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `114`
- Score: `0.861536 vector_distance`

```text
Discussion. This is just an example of dangers that lurk when you try to elide locks; the
lesson applies more broadly. This example is extremely simple — fewer than 10 lines
of code with very simple logic — y et a number of published solutions have been wrong.
As Meyers and Alexandrescu note, some tempting solutions using temporary variables
and the volatile keyword do n ot work. Bacon et al.’s “The ’Double-Checked Locking is
Broken’ Declaration” discusses a range of non-solutions in Java.
http://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
This type of optimization is risky and often does not provide significant performance
gains in practice. Most programmers should not consider them. Even expert
```

#### Chunk 4

- Chunk ID: `31adea97e6dd91ae`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `0.861582 vector_distance`

```text
a new thread may swoop i n and acquire the lock on its fast path, setting count = 0. In this
case, the waiting thread is still woken up, and when it eventually runs, the main loop a bove
will set count = -1.
This example demonstrates that acquiring and releasing a lock can be inexpensive.
Programmers sometimes go to great lengths to avoid acquiring a lock in a particular situation.
However, the reasoning in such cases can be subtle, and om itting needed locks is dangerous.
In cases where there is little contention, avoiding locks is unlikely to significantly improve
performance, so it is usually better just to keep things simple and rely on locks to ensure
mutual exclusion when accessing shared state.
5.7.6 Implementing Condition Variables
```

#### Chunk 5

- Chunk ID: `6134cb7c27556687`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `165`
- Score: `0.871341 vector_distance`

```text
value++; 
     lock = FREE; 
     memory_barrier(); 
 }
However, it turns out this does not help. W hen the lock is released, the new value of the lock,
FREE, must be communicated to the other waiting processors. On modern systems, each
processor separately fetches the data into its cache. Eventually one of them gets the new value
and acquires the lock. If the critical section is not very long, the other processors will still be
busy fetching the new value and trying to acquire the lock, preventing the lock release from
completing.
One approach is to adjust the frequency of polling to the length of time that the thread has
been waiting. A more scalable solution is to assign each waiting thread a separate memory
```

## q2

**Question:** If I wrap every read and write to shared variables in a lock, does that mean my program cannot have any race conditions?

### Method A

- Retrieval latency: 0.228s
- Generation latency: 8.917s

**Answer:**

Not necessarily.

If **every access to a shared variable** — both reads and writes — is protected by the **same lock**, then you prevent a **data race** on that variable.

Example:

```c
lock.acquire();
x = x + 1;
lock.release();
```

and every other thread also uses that same lock before touching `x`.

But your program can still have **race conditions** in a broader sense.

For example:

```c
lock.acquire();
if (balance >= 100) {
    lock.release();

    // another thread may change balance here

    lock.acquire();
    balance -= 100;
}
lock.release();
```

Each individual access to `balance` is locked, but the overall logic is still unsafe because the check and update are not protected as one atomic operation.

A better version would be:

```c
lock.acquire();
if (balance >= 100) {
    balance -= 100;
}
lock.release();
```

So the key idea is:

> Locks must protect the whole critical section, not just individual reads and writes.

Also, all threads must agree on the same locking rule. If one thread accesses the variable without the lock, the protection is broken.

So:

- Same lock around all accesses → prevents data races on that shared state.
- But race conditions can still happen if the program’s higher-level ordering assumptions are wrong.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6cfd5e2ab6193607`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `116`
- Score: `0.706281 vector_distance`

```text
Another common use is inside the operating system kernel, where core data structures are
often read by many threads and only infrequently updated.
To generalize our mutual exclusion lock into a readers/writers lock, we implement a new
kind of shared obj ect, RWLock, to guard access to the shared data and to enforce these rules.
The RWLock is implemented using our standard synchronization building blocks: mutual
exclusion locks and condition variables.
A thread that wants to (atomically) read the shared data proceeds as follows:
    rwLock->startRead(); 
    // Read shared data 
    rwLock->doneRead();
Similarly, a thread that wants to (atomically) write the shared data does the following:
    rwLock->startWrite(); 
    // Read and write shared data 
    rwLock->doneWrite();
```

#### Chunk 2

- Chunk ID: `2b2687862e1d4f81`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `105`
- Score: `0.748218 vector_distance`

```text
Other than these fairly mechanical changes, writing the rest of your code proceeds as in the
single-threaded case.
1. Add a lock. Each shared object needs a lock as a member variable to enforce mutually
exclusive access to the object’s shared state.
This chapter focuses on the simple case where each shared obj ect includes exactly one
lock. In Chapter 6, we will talk about more advanced variations, such as an ownership
design pattern where higher-level program structure enforces mutual exclusion by
ensuring that at most one thread at a time owns and can access an object.
2. Add code to acquire and release the lock. All code accessing the object’s shared state
— any state shared across more than one thread — m ust hold the object’s lock.
```

#### Chunk 3

- Chunk ID: `a6e172643125a989`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `169`
- Score: `0.753641 vector_distance`

```text
A reader calls RCU::readLock and RCU::readUnlock before and after accessing the shared
data structure. A writer calls: RCU::writeLock to exclude other writers; RCU::publish to
issue the write that atomically updates the data structure so that reads can see the updates;
RCU::writeUnlock to let other writers proceed; and RCU::synchronize to wait for the grace
period to expire so that the old version of the object can be freed.
As Figure 6.9 illustrates, writes are serialized — on ly one write can proceed at a time.
However, a write can be concurrent with any number of reads. A write can also be
concurrent with another write’s grace period: there may be any number of versions of the
object until multiple overlapping grace periods expire.
```

#### Chunk 4

- Chunk ID: `79d5e77018b43bc0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `167`
- Score: `0.766231 vector_distance`

```text
simultaneously reading a shared obj ect, the standard readers/writers lock can limit
performance.
While the readers/writers synchronization object could be implemented with an MCS lock
and thereby reduce some of the effects of lock contention, it does not change the inherent
serial access of the readers/writers control structure.
The RCU Approach
How can concurrent reads access a data structure — on e that can also be written — w ithout
having to update the state of a synchronization variable on each read?
```

#### Chunk 5

- Chunk ID: `fbdb950a4ef87a32`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `145`
- Score: `0.779666 vector_distance`

```text
systematic approach, we make it possible for others to read, understand, maintain, and change
the multi-threaded code we write.
In this chapter, we have discussed:
Race conditions. The fundamental challenge to writing multi-threaded code that uses
shared data is that the behavior of the program may depend on the precise ordering of
operations executed by each thread. This non-deterministic behavior is difficult to
reason about, reproduce, and debug.
Locks and condition variables. Two useful sychronization abstractions are locks,
providing mutual exclusion, and condition variables, for waiting for shared state to
change.
A methodology for writing shared objects. Using locks and condition variables, we
outlined a sequence of steps to writing correct synchronization code for coordinating
```

### Method B

- Retrieval latency: 0.531s
- Generation latency: 7.876s

**Answer:**

Not necessarily.

If **every access to the shared variables is protected by the same lock**, then you usually eliminate **data races** on those variables: two threads cannot read/write them concurrently in an unsafe way.

But your program can still have **race conditions**, because a race condition is broader: the program’s behavior may still depend on the timing/interleaving of threads.

Example:

```c
lock();
if (x > 0) {
    unlock();

    // some other thread may change x here

    lock();
    x--;
}
unlock();
```

Each read/write of `x` is inside a lock, but the overall logic is still racy because the condition `x > 0` may no longer be true by the time `x--` happens.

The fix is to protect the whole critical operation:

```c
lock();
if (x > 0) {
    x--;
}
unlock();
```

So the rule is:

> Locks must protect not just individual reads/writes, but the whole sequence of operations that must be treated as one atomic action.

Also, all threads must consistently use the **same lock** for the same shared state. If different locks are used, the protection does not work.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `fbdb950a4ef87a32`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `145`
- Score: `3.5098 rerank_score`

```text
systematic approach, we make it possible for others to read, understand, maintain, and change
the multi-threaded code we write.
In this chapter, we have discussed:
Race conditions. The fundamental challenge to writing multi-threaded code that uses
shared data is that the behavior of the program may depend on the precise ordering of
operations executed by each thread. This non-deterministic behavior is difficult to
reason about, reproduce, and debug.
Locks and condition variables. Two useful sychronization abstractions are locks,
providing mutual exclusion, and condition variables, for waiting for shared state to
change.
A methodology for writing shared objects. Using locks and condition variables, we
outlined a sequence of steps to writing correct synchronization code for coordinating
```

#### Chunk 2

- Chunk ID: `2fa7bd45f10af57b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `73`
- Score: `1.06078 rerank_score`

```text
Semaphores Considered Harmful. What other synchronization primitives are possible,
and how do they relate to locks and condition variables? (Section 5.8)
5.1 Challenges
We began this chapter with the core challenge of multi-threaded programming: a multi-
threaded program’s execution depends on the interleavings of different threads’ access to
shared memory, which can make it difficult to reason about or debug these programs. In
particular, coope rating threads’ execution may be affected by race conditions.
5.1.1 Race Conditions
A race condition occurs when the behavior of a program depends on the interleaving of
operations of different threads. In effect, the threads run a race between their operations, and
the results of the program execution depends on who wins the race.
```

#### Chunk 3

- Chunk ID: `5eab508b865e9e16`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `141`
- Score: `0.942975 rerank_score`

```text
without blocking.
Semaphores considered harmful. Our view is that programming with locks and condition
variables is superior to programming with semaphores. We advise you to always write your
code using those synchronization variables for two reasons.
First, using separate lock and condition variable classes makes code more self-documenting
and easier to read. As the quote from Dijkstra notes, two different abstractions are needed,
and code is clearer when the role of each synchronization variable is made clear through
explicit typing. For example, it is much easier to verify that every lock acquire is paired with
a lock release, if they are not mixed with other calls to P and V for general waiting.
```

#### Chunk 4

- Chunk ID: `6cfd5e2ab6193607`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `116`
- Score: `-0.883804 rerank_score`

```text
Another common use is inside the operating system kernel, where core data structures are
often read by many threads and only infrequently updated.
To generalize our mutual exclusion lock into a readers/writers lock, we implement a new
kind of shared obj ect, RWLock, to guard access to the shared data and to enforce these rules.
The RWLock is implemented using our standard synchronization building blocks: mutual
exclusion locks and condition variables.
A thread that wants to (atomically) read the shared data proceeds as follows:
    rwLock->startRead(); 
    // Read shared data 
    rwLock->doneRead();
Similarly, a thread that wants to (atomically) write the shared data does the following:
    rwLock->startWrite(); 
    // Read and write shared data 
    rwLock->doneWrite();
```

#### Chunk 5

- Chunk ID: `1905d60c619e4134`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `110`
- Score: `-0.920709 rerank_score`

```text
some systems, but it is not portable. In Java, it is completely prohibited.
4. Always hold the lock when operating on a condition variable.
The reason you signal on a condition variable — a fter manipulating shared state — is
that another thread is waiting in a loop f or some test on shared state to become true.
Condition variables are useless without shared state, and shared state should only be
accessed while holding a lock.
```

### Method C

- Retrieval latency: 1.035s
- Generation latency: 7.316s

**Answer:**

Not necessarily.

If **every access to the same shared variable is protected by the same lock**, then you can usually prevent a **data race** on that variable.

But a program can still have **race conditions**.

A **data race** is a specific low-level problem:

> two threads access the same memory concurrently, at least one writes, and there is no proper synchronization.

A **race condition** is broader:

> the program’s correctness depends on the timing/order of threads.

Example:

```cpp
lock(m);
if (balance >= 100) {
    unlock(m);

    // later...

    lock(m);
    balance -= 100;
}
unlock(m);
```

Each read/write of `balance` is inside a lock, but the logic is still wrong because another thread could change `balance` between the check and the subtraction.

The fix is to lock the whole critical section:

```cpp
lock(m);
if (balance >= 100) {
    balance -= 100;
}
unlock(m);
```

So:

- **Locking every read/write correctly can eliminate data races**
- But it does **not automatically eliminate all race conditions**
- You must lock around the whole operation that needs to be atomic
- You also need to use the **same lock consistently** for the same shared state

In short: locks help, but correctness depends on what you protect, not just whether individual reads and writes are locked.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `a6e172643125a989`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `169`
- Score: `n/a `

```text
A reader calls RCU::readLock and RCU::readUnlock before and after accessing the shared
data structure. A writer calls: RCU::writeLock to exclude other writers; RCU::publish to
issue the write that atomically updates the data structure so that reads can see the updates;
RCU::writeUnlock to let other writers proceed; and RCU::synchronize to wait for the grace
period to expire so that the old version of the object can be freed.
As Figure 6.9 illustrates, writes are serialized — on ly one write can proceed at a time.
However, a write can be concurrent with any number of reads. A write can also be
concurrent with another write’s grace period: there may be any number of versions of the
object until multiple overlapping grace periods expire.
```

#### Chunk 2

- Chunk ID: `fbdb950a4ef87a32`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `145`
- Score: `n/a `

```text
systematic approach, we make it possible for others to read, understand, maintain, and change
the multi-threaded code we write.
In this chapter, we have discussed:
Race conditions. The fundamental challenge to writing multi-threaded code that uses
shared data is that the behavior of the program may depend on the precise ordering of
operations executed by each thread. This non-deterministic behavior is difficult to
reason about, reproduce, and debug.
Locks and condition variables. Two useful sychronization abstractions are locks,
providing mutual exclusion, and condition variables, for waiting for shared state to
change.
A methodology for writing shared objects. Using locks and condition variables, we
outlined a sequence of steps to writing correct synchronization code for coordinating
```

#### Chunk 3

- Chunk ID: `6cfd5e2ab6193607`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `116`
- Score: `n/a `

```text
Another common use is inside the operating system kernel, where core data structures are
often read by many threads and only infrequently updated.
To generalize our mutual exclusion lock into a readers/writers lock, we implement a new
kind of shared obj ect, RWLock, to guard access to the shared data and to enforce these rules.
The RWLock is implemented using our standard synchronization building blocks: mutual
exclusion locks and condition variables.
A thread that wants to (atomically) read the shared data proceeds as follows:
    rwLock->startRead(); 
    // Read shared data 
    rwLock->doneRead();
Similarly, a thread that wants to (atomically) write the shared data does the following:
    rwLock->startWrite(); 
    // Read and write shared data 
    rwLock->doneWrite();
```

#### Chunk 4

- Chunk ID: `2836ebf67044bdf6`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `115`
- Score: `n/a `

```text
section walks through several examples.
5.6.1 Readers/Writers Lock
First, we implement a readers/writers lock. Like a normal mutual exclusion lock, a
readers/writers lock (RWLock) protects shared data. However, it makes the following
optimization. To maximize performance, an RWLock allows multiple “reader” threads to
simultaneously access the shared data. Any number of threads can safely read shared data at
the same time, as long as no thread is modifying the data. However, only one “writer” thread
may hold the RWLock at any one time. (While a “reader” thread is restricted to only read
access, a “writer” thread may read and write the data structure.) When a writer thread holds
the RWLock, it may safely modify the data, as the lock guarantees that no other thread
```

#### Chunk 5

- Chunk ID: `6af3d9f1b6bf0dd8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `167`
- Score: `n/a `

```text
is an active writer, no other writer or reader can be active.
The problem occurs when there are many concurrent reads with short critical sections.
Before reading, each reader must acquire a readers/writers lock in read mode and release it
afterwards. On both entrance and exit, the reader must update some state in the
readers/writers synchronization object. Even when there are only readers, the readers/writers
synchronization object can become a bottleneck. This limits the rate at which readers can
enter the critical section, because they can only acquire the lock one at a time. For critical
sections of less than a few thousand cycles, and for programs with dozens of threads
simultaneously reading a shared obj ect, the standard readers/writers lock can limit
performance.
```

## q3

**Question:** I’ve read that programs use virtual addresses and that these get translated to physical addresses. But if every memory access has to go through a translation step, isn’t that really slow? Why would any system accept that overhead?

### Method A

- Retrieval latency: 0.939s
- Generation latency: 12.019s

**Answer:**

Yes — **if address translation were done by walking page tables in memory on every access, it would be far too slow**.

Modern systems avoid that with hardware caching, mainly the **TLB**.

### The key idea: cache recent translations

A virtual address must be translated to a physical address, but programs tend to reuse nearby memory repeatedly. So CPUs keep a small, very fast cache of address translations called the:

> **TLB — Translation Lookaside Buffer**

It stores entries like:

```text
virtual page number → physical frame number + permissions
```

So on most memory accesses:

1. CPU generates a virtual address.
2. CPU checks the TLB.
3. If the translation is there, it gets the physical address quickly.
4. Memory access continues.

This is a **TLB hit**, and it is very fast.

Only when the translation is not in the TLB — a **TLB miss** — does the system need to do the slower page table lookup.

### Why this is acceptable

Because most accesses hit in the TLB. Programs usually show locality:

- they execute nearby instructions,
- access nearby stack locations,
- repeatedly use the same arrays/objects.

So the expensive lookup is not paid on every access.

Also, hardware is designed so translation often overlaps with cache lookup, meaning the processor does not necessarily stall for a full extra step each time.

### Why use virtual memory at all?

The overhead is accepted because virtual addressing gives major benefits:

- **Protection**: one process cannot freely access another process’s memory.
- **Isolation**: each program gets the illusion of its own private address space.
- **Flexible memory management**: the OS can move pages around in physical memory.
- **Demand paging**: load memory only when it is actually used.
- **Sharing**: multiple processes can share the same physical memory safely.
- **Sparse address spaces**: stacks, heaps, and memory-mapped files can grow without needing one big contiguous physical block.

So the tradeoff is:

```text
small translation overhead
in exchange for protection, flexibility, sharing, and efficient memory use
```

Without TLBs and caching, virtual memory would be impractical. With them, it is efficient enough that almost all modern general-purpose systems use it.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `9078584b68d2f01a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `n/a `

```text
make more effective use of on-chip caches.
Sparse addresses. Many programs have multiple dynamic memory regions that can
change in size over the course of the execution of the program: the heap for data objects,
a stack for each thread, and memory mapped files. Modern processors have 64-bit
address spaces, allowing each dynamic object ample room to grow as needed, but
making the translation function more complex.
Runtime lookup efficiency. Hardware address translation occurs on every instruction
fetch and every data load and store. It would be impractical if a lookup took, on
average, much longer to execute than the instruction itself. At first, many of the schemes
we discuss will seem wildly impractical! We will discuss ways to make even the most
convoluted translation systems efficient.
```

#### Chunk 2

- Chunk ID: `e1e88d38b9413270`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `n/a `

```text
In practice, modern systems use much more complex algorithms to translate between virtual
and physical addresses. The layer of indirection provided by virtual addresses gives
operating systems enormous flexibility to efficiently manage physical memory. For example,
```

#### Chunk 3

- Chunk ID: `08d3514f57b7c6c8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `n/a `

```text
changing its logical behavior. In other words, despite the optimization, every virtual address
is translated to exactly the same physical memory location, and every permission exception
causes a trap, exactly as would have occurred without the performance optimization.
For this, we will use a cache, a copy of some data that can be accessed more quickly than the
original. This section concerns how we might use caches to improve translation performance.
Caches are widely used in computer architecture, ope rating systems, distributed systems, and
many other systems; in the next chapter, we discuss more generally when caches work and
when they do n ot. For now, however, our focus is just on the use of caches for reducing the
```

#### Chunk 4

- Chunk ID: `cf5ba25c7110f8d0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `49`
- Score: `n/a `

```text
Instead, most systems with virtually addressed caches use them in tandem with the TLB.
Each virtual address is looked up in both the cache and the TLB at the same time; the
TLB specifies the permissions to use, while the cache provides the data if the access is
permitted. This way, only the TLB’s permissions need to be kept up to date. The TLB
and virtual cache are co-designed to take the same amount of time to perform a lookup,
so the processor does not stall waiting for the TLB.
A further issue is aliasing. Many operating systems allow processes sharing memory to use
different virtual addresses to refer to the same memory location. This is called a memory
address alias. Each process will have its own TLB entry for that memory, and the virtual
```

#### Chunk 5

- Chunk ID: `5d403298d2b03203`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `106`
- Score: `n/a `

```text
with different tradeoffs between interposition and execution speed.) This makes address
translation a pow erful tool for operating systems to introduce new, advanced services to
applications. We have already shown how to use address translation for:
Protection. Operating systems use address translation hardware, along with segment
and page table permissions, to restrict access by applications to privileged memory
locations such as those in the kernel.
Fill-on-demand/zero-on-demand. By setting some page table permissions to invalid,
the kernel can start executing a process before all of its code and data has been loaded
into memory; the hardware will trap to the kernel if the process references data before it
```

### Method B

- Retrieval latency: 0.221s
- Generation latency: 9.812s

**Answer:**

Yes — **if every access required a full page-table lookup in memory, it would be extremely slow**. Operating systems and CPUs accept virtual addressing because the translation is heavily optimized, and the benefits are huge.

The key idea is:

> Virtual addresses give each process its own view of memory, while the hardware/OS translate them to real physical addresses.

This gives the OS flexibility for things like:

- **process isolation**: one program cannot directly access another program’s memory
- **protection**: pages can be marked read-only, executable, kernel-only, etc.
- **relocation**: a program does not need to know where it is physically loaded in RAM
- **sparse address spaces**: stacks, heaps, and memory-mapped files can grow without needing one huge contiguous physical block
- **efficient memory management**: physical memory can be allocated, moved, shared, or swapped more flexibly

But you are right about the danger: address translation happens on **instruction fetches** and on **loads/stores**, so it must be fast.

Modern systems solve this mostly with a hardware cache called a **TLB** — Translation Lookaside Buffer.

A TLB stores recent translations like:

```text
virtual page → physical page
```

So in the common case:

```text
CPU generates virtual address
→ TLB quickly finds translation
→ physical memory/cache is accessed
```

Only when the TLB does not contain the needed translation — a **TLB miss** — does the system need to walk the page table, which is slower.

So the tradeoff is:

```text
Virtual memory adds translation overhead,
but hardware caching makes the common case fast,
and the OS gains protection, isolation, and flexible memory management.
```

Without optimizations like the TLB, virtual memory would indeed be much less practical.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `e1e88d38b9413270`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `0.553181 vector_distance`

```text
In practice, modern systems use much more complex algorithms to translate between virtual
and physical addresses. The layer of indirection provided by virtual addresses gives
operating systems enormous flexibility to efficiently manage physical memory. For example,
```

#### Chunk 2

- Chunk ID: `9078584b68d2f01a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `0.659415 vector_distance`

```text
make more effective use of on-chip caches.
Sparse addresses. Many programs have multiple dynamic memory regions that can
change in size over the course of the execution of the program: the heap for data objects,
a stack for each thread, and memory mapped files. Modern processors have 64-bit
address spaces, allowing each dynamic object ample room to grow as needed, but
making the translation function more complex.
Runtime lookup efficiency. Hardware address translation occurs on every instruction
fetch and every data load and store. It would be impractical if a lookup took, on
average, much longer to execute than the instruction itself. At first, many of the schemes
we discuss will seem wildly impractical! We will discuss ways to make even the most
convoluted translation systems efficient.
```

#### Chunk 3

- Chunk ID: `56e4912227434ec6`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `0.689382 vector_distance`

```text
We will end up with a fairly complex address translation mechanism, and so our discussion
will start with the simplest possible mechanisms and add functionality only as needed. It will
be helpful during the discussion for you to keep in mind the two views of memory: the
process sees its own memory, using its own addresses. We will call these virtual addr esses,
because they do n ot necessarily correspond to any physical reality. By contrast, to the
memory system, there are only physical addr esses — real locations in memory. From the
memory system perspective, it is given physical addresses and it does lookups and stores
values. The translation mechanism converts between the two views: from a virtual address to
a physical memory address.
Address translation in linkers and loaders
```

#### Chunk 4

- Chunk ID: `bc51805a0906f7fa`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `0.712743 vector_distance`

```text
hardware, to eliminate the need for multi-level page tables.
8.3 Towards Efficient Address Translation
At this point, you should be getting a bit antsy. After all, most of the hardware mechanisms we
have described involve at least two and pos sibly as many as four memory extra references,
on each instruction, before we even reach the intended physical memory location! It should
seem completely impractical for a processor to do s everal memory lookups on every
instruction fetch, and even more that for every instruction that loads or stores data.
In this section, we will discuss how to improve address translation performance without
changing its logical behavior. In other words, despite the optimization, every virtual address
```

#### Chunk 5

- Chunk ID: `08d3514f57b7c6c8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `0.737676 vector_distance`

```text
changing its logical behavior. In other words, despite the optimization, every virtual address
is translated to exactly the same physical memory location, and every permission exception
causes a trap, exactly as would have occurred without the performance optimization.
For this, we will use a cache, a copy of some data that can be accessed more quickly than the
original. This section concerns how we might use caches to improve translation performance.
Caches are widely used in computer architecture, ope rating systems, distributed systems, and
many other systems; in the next chapter, we discuss more generally when caches work and
when they do n ot. For now, however, our focus is just on the use of caches for reducing the
```

### Method C

- Retrieval latency: 0.702s
- Generation latency: 9.311s

**Answer:**

Yes, address translation *does* add overhead in principle — every instruction fetch, load, and store uses an address that must be checked and translated from a virtual address to a physical address.

Systems accept this because:

1. **The translation is done by hardware**
   - The CPU’s memory-management unit, or **MMU**, performs the translation automatically.
   - The OS sets up the translation tables, but normal memory accesses do not call into the OS.

2. **Most translations are cached**
   - CPUs use a small fast cache called a **TLB**: Translation Lookaside Buffer.
   - If the virtual-to-physical mapping is already in the TLB, translation is very fast — often effectively part of the normal memory-access pipeline.
   - Only on a TLB miss does the CPU need to do a slower page-table lookup.

3. **The benefits are huge**
   Virtual memory gives the OS major advantages:
   - **Process isolation**: one process cannot freely access another process’s memory.
   - **Protection**: memory can be marked read-only, executable, kernel-only, etc.
   - **Relocation**: each process can think its memory starts at address `0`, even if it is placed somewhere else physically.
   - **Less fragmentation**: physical memory does not need to be one big contiguous block per process.
   - **Sharing**: multiple processes can share the same physical memory, e.g. shared libraries.
   - **Demand paging**: parts of a program can be loaded only when needed.

So the tradeoff is:

> A small hardware-managed cost per memory access in exchange for protection, flexibility, sharing, and efficient memory management.

Without virtual addressing, memory management would be simpler but much less safe and much less flexible.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b0bfb380f282f615`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `20`
- Score: `3.90372 rerank_score`

```text
8.1 Address Translation Concept
Figure 8.1: Address translation in the abstract. The translator converts (virtual) memory addresses generated by the
program into physical memory addresses.
Considered as a black box, address translation is a simple function, illustrated in Figure 8.1.
The translator takes each instruction and data memory reference generated by a process,
checks whether the address is legal, and converts it to a physical memory address that can be
used to fetch or store instructions or data. The data itself — w hatever is stored in memory —
is returned as is; it is not transformed in any way. The translation is usually implemented in
hardware, and the operating system kernel configures the hardware to accomplish its aims.
```

#### Chunk 2

- Chunk ID: `e1e88d38b9413270`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `3.83256 rerank_score`

```text
In practice, modern systems use much more complex algorithms to translate between virtual
and physical addresses. The layer of indirection provided by virtual addresses gives
operating systems enormous flexibility to efficiently manage physical memory. For example,
```

#### Chunk 3

- Chunk ID: `56e4912227434ec6`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `3.71694 rerank_score`

```text
We will end up with a fairly complex address translation mechanism, and so our discussion
will start with the simplest possible mechanisms and add functionality only as needed. It will
be helpful during the discussion for you to keep in mind the two views of memory: the
process sees its own memory, using its own addresses. We will call these virtual addr esses,
because they do n ot necessarily correspond to any physical reality. By contrast, to the
memory system, there are only physical addr esses — real locations in memory. From the
memory system perspective, it is given physical addresses and it does lookups and stores
values. The translation mechanism converts between the two views: from a virtual address to
a physical memory address.
Address translation in linkers and loaders
```

#### Chunk 4

- Chunk ID: `53bbd3d6ec8d5627`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `3.64902 rerank_score`

```text
fragmented. Potentially, memory fragmentation may reach a point where there is not
enough contiguous space to start a new process, despite sufficient free memory in
aggregate.
For these reasons, most modern processors introduce a level of indirection, called virtual
addresses. With virtual addresses, every process’s memory starts at the same place, e.g.,
zero. Each process thinks that it has the entire machine to itself, although obvi ously that is not
the case in reality. The hardware translates these virtual addresses to physical memory
locations. A simple algorithm would be to add the base register to every virtual address so
that the process can use virtual addresses starting from zero.
In practice, modern systems use much more complex algorithms to translate between virtual
```

#### Chunk 5

- Chunk ID: `43a9507dc0552d38`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `37`
- Score: `3.28003 rerank_score`

```text
Figure 8.9: Address translation with a software hash table. The hardware page tables are omitted from the picture. The
virtual page number is hashed; this yields a position in the hash table that indicates the physical page frame. The virtual page
number must be checked against the contents of the hash entry to handle collisions and to check page access permissions.
As shown in Figure 8.9, if there is a match on both the virtual page number and the process
ID, then the translation is valid. Some systems do a  two stage lookup: they first map the
virtual address to a memory object ID, and then do the hash table lookup on the relative
virtual address within the memory object. If memory is mostly shared, this can save space in
the hash table without unduly slowing the translation.
```

## q4

**Question:** What problem does paging solve relative to giving each process a contiguous region of physical memory?

### Method A

- Retrieval latency: 0.982s
- Generation latency: 7.404s

**Answer:**

Paging solves the problem that **physical memory does not need to be allocated as one contiguous block per process**.

If each process needs a contiguous region of physical memory, the OS can run into problems like:

- **External fragmentation**: free memory exists, but it is split into many small gaps.
- **Hard allocation**: a process may need a large continuous block, even though enough total free memory exists.
- **Difficult resizing**: if a process grows, there may not be free space immediately after it.

With **paging**, a process still sees its memory as a linear virtual address space, but its pages can be placed in any free physical page frames.

So instead of needing:

```text
Process A: [ one big contiguous physical block ]
```

the OS can store it like:

```text
Process A page 0 -> frame 12
Process A page 1 -> frame 3
Process A page 2 -> frame 41
Process A page 3 -> frame 8
```

The page table keeps track of this mapping.

In short: **paging makes physical memory allocation simpler by allowing a process’s memory to be scattered across fixed-size frames, avoiding the need for large contiguous free regions.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `7ec889852a25ae7c`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `28`
- Score: `n/a `

```text
segmentation. Instead of a segment table whose entries contain pointers to variable-sized
segments, there is a page table for each process whose entries contain pointers to page
frames. Because page frames are fixed-sized and a pow er of two, the page table entries only
need to provide the upper bits of the page frame address, so they are more compact. There is
no need for a “bound” on the offset; the entire page in physical memory is allocated as a unit.
Figure 8.6 illustrates address translation with paged memory.
What will seem odd, a nd perhaps cool, about paging is that while a program thinks of its
memory as linear, in fact its memory can be, and usually is, scattered throughout physical
memory in a kind of abstract mosaic. The processor will execute one instruction after another
```

#### Chunk 2

- Chunk ID: `e28d7934c3207e46`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `n/a `

```text
however, the decks of all the processes currently running will be shuffled together, apparently
at random. The page tables are the magician’s assistant: able to instantly find the queen of
hearts from among the shuffled decks.
Paging addresses the principal limitation of segmentation: free-space allocation is very
straightforward. The operating system can represent physical memory as a bit map, with each
bit representing a physical page frame that is either free or in use. Finding a free frame is just
a matter of finding an empty bit.
Sharing memory between processes is also convenient: we need to set the page table entry for
each process sharing a page to poi nt to the same physical page frame. For a large shared
```

#### Chunk 3

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `n/a `

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

#### Chunk 4

- Chunk ID: `aecf0c0ac2d7a3b2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `n/a `

```text
each process sharing a page to poi nt to the same physical page frame. For a large shared
region that spans multiple page frames, such as a shared library, this may require setting up a
number of page table entries. Since we need to know when to release memory when a
process finishes, shared memory requires some extra book keeping to keep track of whether
the shared page is still in use. The data structure for this is called a core map; it records
information about each physical page frame such as which page table entries point to it.
Many of the optimizations we discussed under segmentation can also be done with paging.
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
```

#### Chunk 5

- Chunk ID: `7782e63ed2f7e473`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `n/a `

```text
multiple applications from different users, for example, running in different virtual machines.
It is in the interest of any single application to acquire as many physical resources as
possible, even if that hurts performance for other users.
A widely adopted solution is self-paging. With self-paging, each process or user is assigned
its fair share of page frames, using the max-min scheduling algorithm we described in
Chapter 7. If all of the active processes can fit in memory at the same time, the system does
not need to page. As the system starts to page, it evicts the page from whichever process has
the most allocated to it. Thus, the pig would only be able to allocate its fair share of page
frames, and beyond that any page faults it triggers would evict its own pages.
```

### Method B

- Retrieval latency: 0.470s
- Generation latency: 5.744s

**Answer:**

Paging solves the problem that a process does **not need one large contiguous block of physical memory**.

With contiguous physical allocation, the OS must find one big free region for the whole process. This causes problems such as:

- **External fragmentation**: free memory may exist, but split into many small pieces.
- **Difficult growth**: heaps, stacks, thread stacks, or memory-mapped regions may need to expand.
- **Harder sharing**: sharing part of memory between processes is awkward if each process must occupy one contiguous physical region.

With **paging**, a process’s virtual address space can look contiguous, but its pages can be placed in **any free physical page frames**. The OS only needs to find free frames, not one large continuous chunk. This makes physical memory allocation much simpler.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4905d257d16c74d0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `2.70886 rerank_score`

```text
specific location or not.
A dow nside of paging is that while the management of physical memory becomes simpler, the
management of the virtual address space becomes more challenging. Compilers typically
expect the execution stack to be contiguous (in virtual addresses) and of arbitrary size; each
new procedure call assumes the memory for the stack is available. Likewise, the runtime
library for dynamic memory allocation typically expects a contiguous heap. In a single-
threaded process, we can place the stack and heap at oppos ite ends of the virtual address
space, and have them grow towards each other, as shown in Figure 8.5. However, with
multiple threads per process, we need multiple thread stacks, each with room to grow.
```

#### Chunk 2

- Chunk ID: `10b09599c7445f9d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `23`
- Score: `0.429516 rerank_score`

```text
overwriting its own code, for example. It is also difficult to share regions of memory between
two processes. Since the memory for a process needs to be contiguous, supporting dynamic
memory regions, such as for heaps, thread stacks, or memory mapped files, becomes difficult
to impossible.
8.2.1 Segmented Memory
Figure 8.3: Address translation with a segment table. The virtual address has two components: a segment number and a
segment offset. The segment number indexes into the segment table to locate the start of the segment in physical memory.
```

#### Chunk 3

- Chunk ID: `d5e5f9a619087849`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `32`
- Score: `0.188724 rerank_score`

```text
segment, e.g., to prevent writes to the code segment, or to an individual page, e.g., to implement copy-on-write.
Paged Segmentation
Let us start a system with only two levels of a tree. With page d segmentation, memory is
segmented, bu t instead of each segment table entry pointing directly to a contiguous region of
physical memory, each segment table entry points to a page table, which in turn points to the
memory backing that segment. The segment table entry “bound” describes the page table
length, that is, the length of the segment in pages. Because paging is used at the lowest level,
all segment lengths are some multiple of the page size. Figure 8.7 illustrates translation with
paged segmentation.
```

#### Chunk 4

- Chunk ID: `e28d7934c3207e46`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.106876 rerank_score`

```text
however, the decks of all the processes currently running will be shuffled together, apparently
at random. The page tables are the magician’s assistant: able to instantly find the queen of
hearts from among the shuffled decks.
Paging addresses the principal limitation of segmentation: free-space allocation is very
straightforward. The operating system can represent physical memory as a bit map, with each
bit representing a physical page frame that is either free or in use. Finding a free frame is just
a matter of finding an empty bit.
Sharing memory between processes is also convenient: we need to set the page table entry for
each process sharing a page to poi nt to the same physical page frame. For a large shared
```

#### Chunk 5

- Chunk ID: `aecf0c0ac2d7a3b2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `-0.465864 rerank_score`

```text
each process sharing a page to poi nt to the same physical page frame. For a large shared
region that spans multiple page frames, such as a shared library, this may require setting up a
number of page table entries. Since we need to know when to release memory when a
process finishes, shared memory requires some extra book keeping to keep track of whether
the shared page is still in use. The data structure for this is called a core map; it records
information about each physical page frame such as which page table entries point to it.
Many of the optimizations we discussed under segmentation can also be done with paging.
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
```

### Method C

- Retrieval latency: 0.579s
- Generation latency: 5.462s

**Answer:**

Paging solves the problem that physical memory does **not need to contain each process in one contiguous block**.

If each process needs one contiguous physical region, the OS has to find a large enough free chunk. Over time, memory can become fragmented: there may be enough total free memory, but not enough **contiguous** free memory for a process.

With paging:

- A process’s virtual memory still looks linear to the program.
- Physical memory is split into fixed-size **page frames**.
- The process’s pages can be placed in any free frames, scattered throughout physical memory.
- The page table maps each virtual page to its physical frame.

So paging makes allocation much easier: the OS only needs to find free page frames, not one large continuous region. This greatly reduces the external fragmentation problem.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `7ec889852a25ae7c`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `28`
- Score: `0.668439 vector_distance`

```text
segmentation. Instead of a segment table whose entries contain pointers to variable-sized
segments, there is a page table for each process whose entries contain pointers to page
frames. Because page frames are fixed-sized and a pow er of two, the page table entries only
need to provide the upper bits of the page frame address, so they are more compact. There is
no need for a “bound” on the offset; the entire page in physical memory is allocated as a unit.
Figure 8.6 illustrates address translation with paged memory.
What will seem odd, a nd perhaps cool, about paging is that while a program thinks of its
memory as linear, in fact its memory can be, and usually is, scattered throughout physical
memory in a kind of abstract mosaic. The processor will execute one instruction after another
```

#### Chunk 2

- Chunk ID: `e28d7934c3207e46`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.670687 vector_distance`

```text
however, the decks of all the processes currently running will be shuffled together, apparently
at random. The page tables are the magician’s assistant: able to instantly find the queen of
hearts from among the shuffled decks.
Paging addresses the principal limitation of segmentation: free-space allocation is very
straightforward. The operating system can represent physical memory as a bit map, with each
bit representing a physical page frame that is either free or in use. Finding a free frame is just
a matter of finding an empty bit.
Sharing memory between processes is also convenient: we need to set the page table entry for
each process sharing a page to poi nt to the same physical page frame. For a large shared
```

#### Chunk 3

- Chunk ID: `aecf0c0ac2d7a3b2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.707884 vector_distance`

```text
each process sharing a page to poi nt to the same physical page frame. For a large shared
region that spans multiple page frames, such as a shared library, this may require setting up a
number of page table entries. Since we need to know when to release memory when a
process finishes, shared memory requires some extra book keeping to keep track of whether
the shared page is still in use. The data structure for this is called a core map; it records
information about each physical page frame such as which page table entries point to it.
Many of the optimizations we discussed under segmentation can also be done with paging.
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
```

#### Chunk 4

- Chunk ID: `7782e63ed2f7e473`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `0.713099 vector_distance`

```text
multiple applications from different users, for example, running in different virtual machines.
It is in the interest of any single application to acquire as many physical resources as
possible, even if that hurts performance for other users.
A widely adopted solution is self-paging. With self-paging, each process or user is assigned
its fair share of page frames, using the max-min scheduling algorithm we described in
Chapter 7. If all of the active processes can fit in memory at the same time, the system does
not need to page. As the system starts to page, it evicts the page from whichever process has
the most allocated to it. Thus, the pig would only be able to allocate its fair share of page
frames, and beyond that any page faults it triggers would evict its own pages.
```

#### Chunk 5

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `0.724176 vector_distance`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

## q5

**Question:** I read that FAT file systems follow a chain of entries to find all the parts of a file. Why would anyone design a file system that way instead of just storing the full list of block locations in one place?

### Method A

- Retrieval latency: 0.218s
- Generation latency: 10.064s

**Answer:**

Because it is **simple and flexible**, especially for the hardware and operating systems FAT was originally designed for.

In FAT, a directory entry only needs to store something like:

> “this file starts at block 9”

Then the File Allocation Table says:

```text
FAT[9]  = 14
FAT[14] = 3
FAT[3]  = 20
FAT[20] = EOF
```

So the file’s blocks are found by following the chain.

Why design it this way?

1. **Easy file growth**  
   If a file gets bigger, the file system can just find a free block and link it onto the end of the chain. It does not need to move or resize a big “list of blocks” stored somewhere else.

2. **Simple metadata**  
   The directory only needs to store the first block number. The FAT itself stores the rest of the structure.

3. **Free space tracking is built in**  
   The FAT also tells which blocks are free. For example, if `FAT[i] = 0`, block `i` is free. So one table handles both file block chains and free-space management.

4. **Historically practical**  
   FAT was designed for relatively small disks and simple operating systems. A linked-list table was easy to implement and required little complex metadata management.

The downside is that it is not great for random access. If you want block 1000 of a file, you may have to follow 999 FAT entries first, unless the FAT is cached in memory. It can also lead to fragmentation, where one file’s blocks are scattered across the disk.

So the basic reason is:

> FAT trades performance and elegance for simplicity, easy file growth, and simple free-space management.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ece18c6fcf983cc0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `80`
- Score: `0.731684 vector_distance`

```text
Figure 13.9: A FAT file system with one 5-block file and one 2-block file.
Figure 13.9 illustrates a FAT file system with two files. The first begins at block 9 and
contains five blocks. The second begins at block 12 a nd contains two blocks.
Directories map file names to file numbers, and in the FAT file system, a file’s number is the
index of the file’s first entry in the FAT. Thus, given a file’s number, we can find the first FAT
entry and block of a file, and given the first FAT entry, we can find the rest of the file’s FAT
entries and blocks.
Free space tracking. The FAT is also used for free space tracking. If data block i is free,
then FAT[i] contains 0. Thus, the file system can find a free block by scanning through the
FAT to find a zeroed entry.
```

#### Chunk 2

- Chunk ID: `7870277a2fa350a3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `0.742994 vector_distance`

```text
files with up to 232 - 1 by tes.
Index structures. The FAT file system is named for its file allocation table, an array of 32-
bit entries in a reserved area of the volume. Each file in the system corresponds to a linked
list of FAT entries, with each FAT entry containing a pointer to the next FAT entry of the file
(or a special “end of file” value). The FAT has one entry for each block in the volume, and
the file’s blocks are the blocks that correspond to the file’s FAT entries: if FAT entry i is the
jth FAT entry of a file, then storage block i is the jth data block of the file.
```

#### Chunk 3

- Chunk ID: `1b3eab4ee3b9540c`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `0.761461 vector_distance`

```text
Locality heuristics. Different implementations of FAT may use different allocation strategies,
but FAT implementations’ allocation strategies are usually simple. For example, some
implementations use a next fit algorithm that scans sequentially through the FAT starting from
the last entry that was allocated and that returns the next free entry found.
Simple allocation strategies like this may fragment a file, spreading the file’s blocks across
the volume rather than achieving the desired sequential layout. To improve performance,
users can run a defragmentation tool that reads files from their existing locations and
rewrites them to new locations with better spatial locality. The FAT defragmenter in
Windows XP, for example, attempts to copy the blocks of each file that is spread across
```

#### Chunk 4

- Chunk ID: `9f29f1faa6b20490`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `0.762815 vector_distance`

```text
Windows XP, for example, attempts to copy the blocks of each file that is spread across
multiple extents to a single, sequential extent that holds all the blocks of a file.
Discussion The FAT file system is widely used because it is simple and supported by many
operating systems. For example, many flash storage USB keys and camera storage cards use
the FAT file system, allowing them to be read and written by almost any computer running
almost any modern operating system.
Variations of the FAT file system are even used by applications for organizing data within
individual files. For example, Microsoft .doc  files produced by versions of Microsoft Word
from 1997 t o 2007 a re actually compound doc uments with many internal pieces. The .doc
```

#### Chunk 5

- Chunk ID: `2bcc6fa4c5c0b72f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `0.778698 vector_distance`

```text
Finally, some file systems like NTFS, ext4, and btrfs store data in variable-length arrays of contiguous tracks called extents in
most file systems and runs in NTFS. For consistency, we will use the term extent in our discussions.
13.3.1 FAT: Linked List
The Microsoft File Allocation Table (FAT) file system was first implemented in the late
1970s  and was the main file system for MS-DOS and early versions of Microsoft Windows.
The FAT file system has been enhanced in many ways over the years. Our discussion will
focus on the most recent version, FAT-32, w hich supports volumes with up to 228 blocks and
files with up to 232 - 1 by tes.
Index structures. The FAT file system is named for its file allocation table, an array of 32-
```

### Method B

- Retrieval latency: 0.873s
- Generation latency: 7.786s

**Answer:**

Because it makes the file system very simple.

In FAT, each data block has one entry in the File Allocation Table. That entry says either:

- “the next block of this file is block X”, or
- “this is the end of the file”, or
- “this block is free”

So a file is represented as a linked list of blocks.

Why design it this way?

1. Easy to grow files  
   If a file needs one more block, the file system just finds a free FAT entry and links it onto the end of the chain. It does not need to resize some separate “block list” structure.

2. Simple free-space tracking  
   The same FAT table also records which blocks are free. If `FAT[i] = 0`, then block `i` is free. So allocation and file indexing use one shared structure.

3. Small directory entries  
   A directory only needs to store the file name and the first block number. From that first block, the FAT chain gives the rest.

4. Good enough for small/simple systems  
   FAT was designed for relatively simple storage devices and small disks. Its simplicity made it easy to implement and widely compatible.

But there is a downside:

- To find block 1000 of a file, the system may have to follow 999 FAT entries first.
- If the file is fragmented, the blocks may be scattered across the disk.
- It also makes features like hard links difficult, because the file’s metadata is tied to its directory entry rather than to a separate inode-like object.

So the basic reason is: FAT chooses simplicity and easy allocation over fast random access and richer metadata.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `885b54784249ab28`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `2.61247 rerank_score`

```text
control information like the file’s owner or group ID, so any user can read or write any
file stored in a FAT file system.
No support for hard links. FAT represents each file as a linked list of 32-bit entries in
the file allocation table. This representation does not include room for any other file
metadata. Instead, file metadata in stored with directory entries with the file’s name.
This approach demands that each file be accessed via exactly one directory entry, ruling
out multiple hard links to a file.
Limitations on volume and file size. FAT table entries are 32 bi ts, but the top four bits
are reserved. Thus, a FAT volume can have at most 228 blocks. With 4 KB blocks, the
maximum volume size is limited (e.g., 228 blocks/volume × 212 bytes/block = 240
```

#### Chunk 2

- Chunk ID: `7870277a2fa350a3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `2.37368 rerank_score`

```text
files with up to 232 - 1 by tes.
Index structures. The FAT file system is named for its file allocation table, an array of 32-
bit entries in a reserved area of the volume. Each file in the system corresponds to a linked
list of FAT entries, with each FAT entry containing a pointer to the next FAT entry of the file
(or a special “end of file” value). The FAT has one entry for each block in the volume, and
the file’s blocks are the blocks that correspond to the file’s FAT entries: if FAT entry i is the
jth FAT entry of a file, then storage block i is the jth data block of the file.
```

#### Chunk 3

- Chunk ID: `ece18c6fcf983cc0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `80`
- Score: `1.85019 rerank_score`

```text
Figure 13.9: A FAT file system with one 5-block file and one 2-block file.
Figure 13.9 illustrates a FAT file system with two files. The first begins at block 9 and
contains five blocks. The second begins at block 12 a nd contains two blocks.
Directories map file names to file numbers, and in the FAT file system, a file’s number is the
index of the file’s first entry in the FAT. Thus, given a file’s number, we can find the first FAT
entry and block of a file, and given the first FAT entry, we can find the rest of the file’s FAT
entries and blocks.
Free space tracking. The FAT is also used for free space tracking. If data block i is free,
then FAT[i] contains 0. Thus, the file system can find a free block by scanning through the
FAT to find a zeroed entry.
```

#### Chunk 4

- Chunk ID: `9f29f1faa6b20490`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `1.84619 rerank_score`

```text
Windows XP, for example, attempts to copy the blocks of each file that is spread across
multiple extents to a single, sequential extent that holds all the blocks of a file.
Discussion The FAT file system is widely used because it is simple and supported by many
operating systems. For example, many flash storage USB keys and camera storage cards use
the FAT file system, allowing them to be read and written by almost any computer running
almost any modern operating system.
Variations of the FAT file system are even used by applications for organizing data within
individual files. For example, Microsoft .doc  files produced by versions of Microsoft Word
from 1997 t o 2007 a re actually compound doc uments with many internal pieces. The .doc
```

#### Chunk 5

- Chunk ID: `da62f7f8511f5d6d`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `110`
- Score: `1.43532 rerank_score`

```text
problem in practice.
8. When user tries to write a file, the file system needs to detect if that file is a directory so
that it can restrict writes to maintain the directory’s internal consistency.
Given a file’s name, how would you design each file system listed below to keep track
of whether each file is a regular file or a directory?
a. The FAT file system
b. FFS
c. NTFS
9. Why would it be difficult to add hard links to the FAT file system?
10. For the FFS file system illustrated in Figure 13.25 , what reads and writes of inodes and
blocks would occur to create a new file /foo/sparse and write blocks 1 and 2,000,000 of
that file. Assume that inodes have pointers for 11 direct blocks, 1 indirect block, 1
```

### Method C

- Retrieval latency: 0.663s
- Generation latency: 10.233s

**Answer:**

Because it is **simple and space-efficient for growing files**, especially on older systems.

In FAT, the directory only needs to store something like:

> file name → first block number

Then the FAT table tells you:

> block 9 → block 16 → block 4 → block 20 → EOF

So the file system can find the whole file by following the chain.

Why design it this way instead of storing the full block list in one place?

1. **Files can grow easily**  
   If a file needs another block, FAT just finds a free block and changes the last FAT entry to point to it.  
   No need to resize a per-file block list.

2. **No need to know file size in advance**  
   A linked chain works naturally for files that expand over time.

3. **Simple metadata structure**  
   FAT has one global table with one entry per disk block. That same table is used both to:
   - link file blocks together
   - mark free blocks, e.g. `FAT[i] = 0` means block `i` is free

4. **Good enough for small/early systems**  
   FAT was designed for relatively simple storage devices and operating systems. Simplicity and compatibility mattered a lot.

But your intuition is right: there are disadvantages.

If the full block list were stored in one place, it would be faster to jump directly to the middle of a file. With FAT, to reach the 1000th block of a file, the system may have to follow 999 links first. FAT can also lead to fragmentation, where one file’s blocks are scattered across the disk.

So the short answer is:

> FAT uses chains because they make allocation and file growth simple, but the tradeoff is slower random access and possible fragmentation. Later file systems often use more advanced structures like extents or indexes to avoid those problems.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ece18c6fcf983cc0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `80`
- Score: `n/a `

```text
Figure 13.9: A FAT file system with one 5-block file and one 2-block file.
Figure 13.9 illustrates a FAT file system with two files. The first begins at block 9 and
contains five blocks. The second begins at block 12 a nd contains two blocks.
Directories map file names to file numbers, and in the FAT file system, a file’s number is the
index of the file’s first entry in the FAT. Thus, given a file’s number, we can find the first FAT
entry and block of a file, and given the first FAT entry, we can find the rest of the file’s FAT
entries and blocks.
Free space tracking. The FAT is also used for free space tracking. If data block i is free,
then FAT[i] contains 0. Thus, the file system can find a free block by scanning through the
FAT to find a zeroed entry.
```

#### Chunk 2

- Chunk ID: `7870277a2fa350a3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `n/a `

```text
files with up to 232 - 1 by tes.
Index structures. The FAT file system is named for its file allocation table, an array of 32-
bit entries in a reserved area of the volume. Each file in the system corresponds to a linked
list of FAT entries, with each FAT entry containing a pointer to the next FAT entry of the file
(or a special “end of file” value). The FAT has one entry for each block in the volume, and
the file’s blocks are the blocks that correspond to the file’s FAT entries: if FAT entry i is the
jth FAT entry of a file, then storage block i is the jth data block of the file.
```

#### Chunk 3

- Chunk ID: `9f29f1faa6b20490`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `n/a `

```text
Windows XP, for example, attempts to copy the blocks of each file that is spread across
multiple extents to a single, sequential extent that holds all the blocks of a file.
Discussion The FAT file system is widely used because it is simple and supported by many
operating systems. For example, many flash storage USB keys and camera storage cards use
the FAT file system, allowing them to be read and written by almost any computer running
almost any modern operating system.
Variations of the FAT file system are even used by applications for organizing data within
individual files. For example, Microsoft .doc  files produced by versions of Microsoft Word
from 1997 t o 2007 a re actually compound doc uments with many internal pieces. The .doc
```

#### Chunk 4

- Chunk ID: `1b3eab4ee3b9540c`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `81`
- Score: `n/a `

```text
Locality heuristics. Different implementations of FAT may use different allocation strategies,
but FAT implementations’ allocation strategies are usually simple. For example, some
implementations use a next fit algorithm that scans sequentially through the FAT starting from
the last entry that was allocated and that returns the next free entry found.
Simple allocation strategies like this may fragment a file, spreading the file’s blocks across
the volume rather than achieving the desired sequential layout. To improve performance,
users can run a defragmentation tool that reads files from their existing locations and
rewrites them to new locations with better spatial locality. The FAT defragmenter in
Windows XP, for example, attempts to copy the blocks of each file that is spread across
```

#### Chunk 5

- Chunk ID: `2bcc6fa4c5c0b72f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `n/a `

```text
Finally, some file systems like NTFS, ext4, and btrfs store data in variable-length arrays of contiguous tracks called extents in
most file systems and runs in NTFS. For consistency, we will use the term extent in our discussions.
13.3.1 FAT: Linked List
The Microsoft File Allocation Table (FAT) file system was first implemented in the late
1970s  and was the main file system for MS-DOS and early versions of Microsoft Windows.
The FAT file system has been enhanced in many ways over the years. Our discussion will
focus on the most recent version, FAT-32, w hich supports volumes with up to 228 blocks and
files with up to 232 - 1 by tes.
Index structures. The FAT file system is named for its file allocation table, an array of 32-
```
