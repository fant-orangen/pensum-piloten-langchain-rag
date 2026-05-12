# Anonymized Retrieval Review

Method identities are hidden in this document. Use the separate key file after review.
Each method is normalized to the same final chunk count before answer generation.

## q1

**Question:** If I put a lock around my shared counter so that only one thread at a time can touch it, and my program still sometimes produces the wrong total, does that mean the lock is broken?

### Method A

- Retrieval latency: 1.728s
- Generation latency: 9.637s

**Answer:**

Not necessarily. It usually means **something about how the lock is used or implemented is wrong**, not that the idea of locking is broken.

If a shared counter is always accessed like this:

```c
lock(m);
counter++;
unlock(m);
```

and **every thread uses the same lock**, then the final total should be correct.

Common reasons it can still be wrong:

1. **Some accesses are outside the lock**
   ```c
   counter++;   // unprotected somewhere else
   ```

2. **Different threads use different locks**
   ```c
   lock(m1); counter++; unlock(m1);
   lock(m2); counter++; unlock(m2);
   ```
   That does not protect the same critical section.

3. **The lock implementation is incorrect**
   For example, a homemade spinlock must use atomic operations like `test_and_set`, not an ordinary variable check.

4. **Missing memory-ordering rules**
   On multiprocessors, lock acquire/release must include the right memory barriers or atomic semantics.

5. **The program reads the total before all threads finish**
   You still need to `join`/wait for all worker threads before checking the result.

6. **Integer overflow**
   The counter may wrap around if the total exceeds the integer type’s limit.

So the short answer is: **a correct lock used consistently should prevent lost updates. If the total is wrong, look for an unprotected access, the wrong lock, an incorrect lock implementation, or reading too early.**

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

- Retrieval latency: 4.954s
- Generation latency: 9.061s

**Answer:**

Not necessarily. A wrong total usually means the **locking discipline is wrong**, not that the lock itself is broken.

A lock only protects the counter if **every access that can affect the counter uses the same lock**.

For example, this is safe:

```c
lock.acquire();
counter++;
lock.release();
```

But this is not safe:

```c
temp = counter;
lock.acquire();
counter = temp + 1;
lock.release();
```

because the read happened outside the lock.

Also unsafe:

```c
lock1.acquire();
counter++;
lock1.release();
```

in one thread, but:

```c
lock2.acquire();
counter++;
lock2.release();
```

in another thread. Those are different locks, so they do not exclude each other.

The key rule is:

> The shared counter and all operations on it must be protected by the same lock.

So if the total is still wrong, check for things like:

- some increments happen without the lock
- reads/writes are partly outside the locked section
- different threads use different lock objects
- the lock is accidentally copied instead of shared
- the program reads the final total before all threads have finished

A correct lock used consistently should prevent lost updates to the counter.

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

- Retrieval latency: 7.107s
- Generation latency: 12.523s

**Answer:**

Not necessarily. A wrong total usually means **the locking discipline is wrong**, not that the lock primitive itself is broken.

If **every access** to the shared counter is protected by the **same lock**, and all worker threads have finished before you read the final value, then the counter update should be correct.

Common causes of a wrong total:

```cpp
lock();
counter++;
unlock();
```

is correct only if:

1. **All threads use the same lock**
   - Not one lock per thread.
   - Not accidental copies of the lock.

2. **Every read/write of `counter` is protected**
   - No code elsewhere does `counter++` without the lock.

3. **You wait for all threads to finish**
   - For example, using `join()` before printing the total.

4. **The counter is initialized correctly**
   - e.g. `counter = 0` before threads start.

5. **The lock is actually around the critical section**
   - This would be wrong:

```cpp
lock();
int temp = counter;
unlock();

temp++;

lock();
counter = temp;
unlock();
```

The read-modify-write operation must be protected as one unit:

```cpp
lock();
counter++;
unlock();
```

So the lock is probably not broken. More likely, some access to the shared counter is happening outside the lock, under a different lock, or before all threads have completed.

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

- Retrieval latency: 0.188s
- Generation latency: 9.152s

**Answer:**

Not necessarily.

If **every access to a shared variable** is protected by the **same lock**, then you usually eliminate **data races** on that variable.

Example:

```c
lock(m);
x++;
unlock(m);
```

If all threads use `m` whenever they access `x`, then two threads cannot simultaneously read/write `x` unsafely.

But your program can still have **race conditions**.

A **data race** is a low-level problem: two threads access the same memory concurrently, at least one writes, and there is no proper synchronization.

A **race condition** is broader: the program’s correctness depends on the timing/order of threads.

For example:

```c
lock(m);
if (balance >= 100) {
    unlock(m);

    // later...

    lock(m);
    balance -= 100;
}
unlock(m);
```

Even though each individual access to `balance` is locked, the overall operation is not atomic. Another thread could change `balance` between the check and the update.

The correct version would keep the lock across the whole logical operation:

```c
lock(m);
if (balance >= 100) {
    balance -= 100;
}
unlock(m);
```

So the rule is:

> Locks prevent races only if they protect the entire shared state and the entire critical operation, not just individual reads and writes.

Also, locks do not automatically prevent other concurrency bugs like deadlock, starvation, or incorrect use of condition variables.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6cfd5e2ab6193607`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `116`
- Score: `0.706432 vector_distance`

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
- Score: `0.748282 vector_distance`

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
- Score: `0.753746 vector_distance`

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
- Score: `0.766306 vector_distance`

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
- Score: `0.779722 vector_distance`

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

- Retrieval latency: 0.699s
- Generation latency: 9.119s

**Answer:**

Not necessarily.

If **every access to a shared variable is protected by the same appropriate lock**, then you usually eliminate **data races** on that variable: two threads cannot concurrently read/write or write/write it unsafely.

But your program can still have **race conditions** if the program’s correctness depends on timing or ordering between threads.

Example:

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

Each read/write of `balance` is inside a lock, but the whole operation “check balance and withdraw” is **not atomic**. Another thread can interfere between the check and the update.

Better:

```c
lock.acquire();
if (balance >= 100) {
    balance -= 100;
}
lock.release();
```

So the key idea is:

> Locks must protect the entire critical operation, not just individual reads and writes.

Also, race conditions can happen through other shared state or ordering assumptions, such as:

- using different locks for related shared variables
- checking a condition without holding the lock long enough
- relying on one thread to “go first” without synchronization
- incorrect use of condition variables/signals

So: **locking every access is a good start, but it does not automatically prove the program is free of race conditions.** You need to ensure the intended shared-state invariants are protected atomically.

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

- Retrieval latency: 0.945s
- Generation latency: 8.147s

**Answer:**

Not necessarily.

If **every access to a shared variable is protected by the same lock**, then you usually eliminate **data races** on that variable: two threads cannot concurrently access it with at least one write.

But your program can still have **race conditions** at a higher level.

Example:

```c
lock();
if (balance >= 100) {
    unlock();

    // another thread may change balance here

    lock();
    balance -= 100;
}
unlock();
```

Each read/write of `balance` is protected by a lock, but the logic is still racy because the check and update are not done as one atomic operation.

The correct version would keep the whole critical section locked:

```c
lock();
if (balance >= 100) {
    balance -= 100;
}
unlock();
```

So:

- **Locks can prevent data races** if used consistently.
- But they do **not automatically prevent all race conditions**.
- You must lock around the whole operation that needs to be atomic, not just individual reads and writes.

Also, all threads must follow the same locking rule. One unprotected access to the shared variable can reintroduce a race.

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

- Retrieval latency: 0.940s
- Generation latency: 11.552s

**Answer:**

Yes — **if every memory access required a full page-table lookup in memory, it would be far too slow**.

Modern systems avoid that with hardware caching, mainly the **TLB**.

### The key idea: translation is cached

A virtual address is translated to a physical address by the MMU, using page tables. But recently used translations are stored in a small, fast hardware cache called the:

> **TLB — Translation Lookaside Buffer**

So most of the time:

1. CPU generates a virtual address.
2. MMU checks the TLB.
3. If the translation is there, the physical address is found very quickly.
4. Memory access continues almost as if there were no translation cost.

A TLB hit is designed to be extremely fast, often happening in parallel with other CPU/cache work.

### What if the TLB misses?

Then the system has to walk the page table to find the translation. That is slower.

But programs usually have **locality**: they access the same pages repeatedly for a while. So once a translation is cached in the TLB, many later accesses reuse it.

### Why accept the overhead at all?

Because virtual memory gives huge benefits:

- **Protection**: one process cannot freely access another process’s memory.
- **Isolation**: each program gets its own private address space.
- **Convenience**: programs can pretend they have a large, continuous memory space.
- **Efficient physical memory use**: the OS can move pages, share pages, or load pages only when needed.
- **Support for sparse memory regions**: heap, stack, memory-mapped files, etc. can grow independently.
- **Security and kernel protection**: user programs cannot directly access privileged memory.

So the tradeoff is:

> A small average translation cost, greatly reduced by hardware caches, in exchange for protection, flexibility, and efficient memory management.

Without TLBs and other cache optimizations, virtual memory would indeed be impractically slow. But with them, the overhead is usually acceptable.

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

- Retrieval latency: 0.305s
- Generation latency: 10.146s

**Answer:**

Yes — **if translation required a full page-table lookup in memory on every access, it would be far too slow**.

Modern systems accept virtual addressing because they make translation fast, mainly with hardware caching.

### The key idea: translation is cached

The CPU has a small, very fast cache called a **TLB** — Translation Lookaside Buffer.

It stores recent mappings like:

```text
virtual page  →  physical frame
```

So when a program accesses memory:

1. CPU checks the TLB.
2. If the mapping is there, translation is very fast.
3. Only if it is missing does the CPU/page-table mechanism do a slower lookup.

Because programs usually show **locality** — they repeatedly access nearby or recently used memory — most translations are found in the TLB.

So the common case is fast.

### Why accept the overhead at all?

Virtual memory gives major advantages:

- **Process isolation**  
  One program cannot directly access another program’s memory.

- **Each process gets its own address space**  
  Programs can behave as if they start at address `0`, even if physically they are placed elsewhere.

- **Flexible memory management**  
  The OS can move, map, protect, share, or swap memory more easily.

- **Sparse address spaces**  
  Programs can have large heaps, stacks, memory-mapped files, etc., without needing all of that memory physically allocated at once.

- **Protection and permissions**  
  Pages can be marked read-only, executable, kernel-only, and so on.

### So the tradeoff is:

```text
Small translation cost
in exchange for
protection, flexibility, isolation, and efficient memory management
```

Without caching, it would be impractical. But with hardware support like the TLB, virtual address translation is usually fast enough that the benefits are worth it.

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

- Retrieval latency: 0.619s
- Generation latency: 8.801s

**Answer:**

Yes, address translation *does* add work in principle — every instruction fetch, load, and store uses a virtual address that must be translated to a physical address.

But systems accept it because:

1. **Translation is done by hardware**
   The CPU/MMU performs address translation automatically, not by running OS code on every access. So the common case is very fast.

2. **Translations are cached in the TLB**
   Modern CPUs use a **Translation Lookaside Buffer (TLB)**, a small fast cache of recent virtual-to-physical address translations.

   So most memory accesses do **not** require walking page tables. They hit in the TLB and translation is nearly as fast as normal cache lookup.

3. **Virtual memory gives huge benefits**
   The overhead buys the OS a lot:
   - Each process gets its own private address space.
   - Programs can start at address `0` as if they own memory.
   - Processes cannot easily access each other’s memory.
   - Memory can be moved, shared, protected, or swapped more flexibly.
   - Physical memory does not need to be one large contiguous block.

4. **Without virtual addresses, memory management is much harder**
   If programs used physical addresses directly, the OS would have trouble relocating programs, isolating processes, avoiding fragmentation, and enforcing protection.

So the short answer is:

> Address translation would be too slow if done naively, but hardware support and TLB caching make it fast enough, while the flexibility and protection benefits are enormous.

In practice, the cost is usually small compared with the advantages virtual memory provides.

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

- Retrieval latency: 0.812s
- Generation latency: 5.751s

**Answer:**

Paging solves the problem of needing to find one large contiguous block of physical memory for each process.

If each process must occupy a contiguous physical region, the OS can run into:

- **External fragmentation**: free memory exists, but it is split into many small holes.
- **Hard allocation**: starting a large process may fail even if total free memory is enough.
- **Compaction overhead**: the OS may need to move processes around to create a large enough free block.

With **paging**, a process’s virtual memory is split into fixed-size **pages**, and physical memory is split into fixed-size **page frames**. The pages of one process do **not** need to be adjacent in physical memory.

So a process can think it has one linear address space, while the OS stores its pages scattered across available frames.

In short:

> Paging makes physical memory allocation easier by removing the requirement that each process occupy one contiguous chunk of RAM.

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

- Retrieval latency: 0.385s
- Generation latency: 7.195s

**Answer:**

Paging solves the problem that **each process no longer needs one contiguous block of physical memory**.

With contiguous physical allocation, the OS has to find a large enough free region for the whole process. This causes problems like:

- **External fragmentation**: free memory may exist, but scattered in small pieces.
- **Hard process growth**: heap, stack, thread stacks, or memory-mapped regions may need more space later.
- **Hard sharing**: sharing part of memory between processes is awkward if each process must occupy one continuous physical region.

With **paging**, a process’s virtual address space can look contiguous to the program, but its pages can be placed in **any free physical page frames**. The OS only needs to find free frames, not one large contiguous region.

So the key benefit is:

> Paging makes physical memory allocation simpler by allowing a process to be stored in scattered fixed-size frames instead of one contiguous physical block.

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

- Retrieval latency: 0.291s
- Generation latency: 5.134s

**Answer:**

Paging solves the problem that **each process would otherwise need one large contiguous block of physical memory**.

With contiguous allocation, the OS can run into **external fragmentation**: there may be enough free physical memory total, but it is split into small pieces, so a large process cannot fit.

With paging:

- a process’s virtual memory is split into fixed-size **pages**
- physical memory is split into fixed-size **page frames**
- each virtual page can be placed in **any free frame**
- the page table maps the process’s pages to those frames

So the process still sees a linear address space, but physically its memory can be scattered across RAM. This makes free-space allocation much simpler: the OS just needs to find free page frames, not one big contiguous region.

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
- Generation latency: 10.730s

**Answer:**

Because FAT was designed to be **simple and flexible**, especially for small disks and limited-memory systems.

In FAT, the directory only needs to store something like:

> file name → first block number

Then the file allocation table says:

> block 9 → block 14 → block 20 → end

So the FAT itself acts like a linked list of the file’s blocks.

Why do this instead of storing the full list in one place?

1. **Files can grow easily**  
   If a file needs another block, FAT just finds a free block and updates the chain.  
   It does not need to resize a separate “block list” structure.

2. **No need to reserve space for block lists**  
   A full list of block locations could be tiny for small files or huge for large files. FAT avoids needing a separate variable-sized index per file.

3. **The FAT also tracks free space**  
   In FAT, an entry can mean “this block is free” or “this block points to the next block.”  
   So one table handles both allocation and free-space tracking.

4. **Very simple implementation**  
   FAT was created for systems like MS-DOS, where simplicity and low overhead mattered a lot.

The downside is exactly what you noticed: to find block 1000 of a file, the system may have to follow 999 links first. So FAT is bad for fast random access and can suffer from fragmentation.

Modern file systems often do store block locations more directly, commonly using structures like **extents**, where one entry can say:

> this file uses 500 contiguous blocks starting at block 10000

That is more efficient, but also more complex. FAT chose simplicity over performance.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ece18c6fcf983cc0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `80`
- Score: `0.73142 vector_distance`

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
- Score: `0.742825 vector_distance`

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
- Score: `0.761283 vector_distance`

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
- Score: `0.762585 vector_distance`

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
- Score: `0.77848 vector_distance`

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

- Retrieval latency: 0.402s
- Generation latency: 8.742s

**Answer:**

Because FAT was designed to be **simple and space-efficient for small systems**.

In FAT, each file only needs one starting number in its directory entry: the index of its **first FAT entry**. Then the file system follows the chain:

```text
first block → next block → next block → ... → EOF
```

This design has some practical advantages:

1. **Small directory entries**
   - The directory does not need to store a whole list of every block in the file.
   - It just stores the file’s first block/FAT index.

2. **Files can grow easily**
   - If a file needs another block, the file system finds a free FAT entry and links it onto the end of the chain.
   - It does not need to resize or relocate a big “block list” structure.

3. **The FAT table also tracks free space**
   - If `FAT[i] = 0`, block `i` is free.
   - So the same table is used both for file block chains and free-space management.

4. **Simple implementation**
   - FAT was meant for relatively small disks and simple operating systems.
   - A linked-list style allocation table is easy to implement and understand.

The downside is that it can be inefficient for random access. For example, to find block 1000 of a file, the system may have to follow 999 FAT entries first. A file system that stores a full index of block locations can jump more directly.

So the short answer is:

> FAT uses chains because it keeps metadata simple and makes file growth easy, but it sacrifices fast random access and richer metadata support.

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

- Retrieval latency: 0.632s
- Generation latency: 12.035s

**Answer:**

Because it is a simple tradeoff: FAT makes file allocation easy, especially on small/simple systems.

In FAT, the directory only needs to store the file’s first block number. Then the FAT entry for that block points to the next block, and so on until an “end of file” marker.

So instead of storing:

```text
file A -> [9, 14, 20, 21, 7]
```

in one separate list, FAT stores something like:

```text
FAT[9]  = 14
FAT[14] = 20
FAT[20] = 21
FAT[21] = 7
FAT[7]  = EOF
```

The advantages are:

1. **Very simple directory entries**  
   A directory only needs to remember the first block of the file.

2. **Files can grow easily**  
   To append a block, the file system finds a free block and links it onto the end of the chain. It does not need to resize a separate “list of all blocks.”

3. **Free space tracking is built in**  
   FAT entries with value `0` can mean “this block is free,” so the same table tracks both file chains and free blocks.

4. **Works well enough for small/simple storage**  
   FAT was designed for relatively simple systems, and it remains common on USB drives and memory cards because it is easy to implement and widely supported.

The downside is that following a chain is inefficient for random access. If you want block 1000 of a file, FAT may have to follow 999 links first. Also, simple FAT allocation can fragment files across the disk.

So the answer is: **FAT uses chains because they are simple and flexible, not because they are the fastest design.** More advanced file systems often do store block locations using richer index structures or extents.

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

#### Chunk 4

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

## q6

**Question:** When I save a file, my computer seems to know exactly where to find it later even though I never told it where on the disk to put it. How does it actually keep track of this?

### Method A

- Retrieval latency: 0.800s
- Generation latency: 10.153s

**Answer:**

Your computer uses the **file system** to keep track of where files are stored.

When you save a file, you usually give it a **name** and choose a **folder**, but you do not choose the exact disk locations. The operating system handles that.

Roughly, it works like this:

1. **The folder stores the file name**
   - A folder/directory is basically a mapping from names to file records.
   - Example:  
     ```text
     Documents/report.docx → file record #12345
     ```

2. **The file record stores metadata**
   - The file system keeps a record for each file.
   - This record may be called an **inode** on Unix/Linux systems or a similar file record on other systems.
   - It stores information like:
     - file size
     - permissions
     - timestamps
     - where the file’s data blocks are located on disk

3. **The actual file data is stored in blocks**
   - Disks/SSDs store data in chunks called **blocks**.
   - A file may be stored across many blocks, not necessarily next to each other.
   - The file record contains pointers or extents saying something like:
     ```text
     This file’s data is in blocks 1040–1055, 2088–2092, 9001–9010
     ```

4. **When you open the file later**
   - The OS looks up the path:
     ```text
     /home/alex/Documents/report.docx
     ```
   - It finds the directory entry for `report.docx`.
   - That points to the file’s metadata record.
   - The metadata tells the OS which disk blocks contain the file contents.

So the short answer is:

> The computer keeps a directory entry mapping the file name to a metadata record, and that metadata record tells the file system where the file’s data blocks are stored on disk.

You only choose the human-friendly name and folder; the file system manages the physical storage locations.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `69e0bfb86e0fd180`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `n/a `

```text
servers also keep copies of frequently requested pages in memory so that they can be
transmitted more quickly.
Web search. Both Google and Bing keep a cached copy of every web page they index.
This allows them to provide the copy of the web page if the original is unavailable for
some reason. The cached copy may be out of date — the search engines do n ot guarantee
that the copy instantaneously reflects any change in the original web page.
Email clients. Many email clients store a copy of mail messages on the client computer
to improve the client performance and to allow disconnected ope ration. In the
background, the client communicates with the server to keep the two copies in sync.
Incremental compilation. If you have ever built a program from multiple source files,
```

#### Chunk 2

- Chunk ID: `ad67d87468a57fd8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `n/a `

```text
method w hen the user hits “save” — just append any changes from the previous version,
rather than writing a fresh copy of the entire file. This means that the old version of a file can
potentially still be recovered from a file. So if you write a memo insulting your boss, and then
edit it to tone it dow n, it is best to save a completely new version of your file before you send
it off!
Will this method w ork for persistent memory? Keeping a log of every change to every
memory location in the process would be too slow. We would need to trap on every store
instruction and save the value to disk. In other words, we would run at the speed of the trap
handler, rather than the speed of the processor.
However, we can come close. When we take a checkpoint, we mark all pages as read-only to
```

#### Chunk 3

- Chunk ID: `bdcb15ce0dd48d36`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `n/a `

```text
structuring their data so that the underlying file system can better meet their performance and
reliability requirements.
For example, a word processor might use a sophisticated doc ument format, allowing it to, for
example, add and remove embedded images and to always update a document by appending
updates to the end of the file.
As another example, a data analysis program might improve its performance by organizing its
accesses to input files in a way that ensures that each input file is read only once and that it is
read sequentially from its start to its end.
Or, a browser with a 1 GB on-disk cache might create 100 f iles, each containing 10 M B of
data, and group a given web site’s objects in a sequential region of a randomly selected file.
```

#### Chunk 4

- Chunk ID: `635d507f10a72aa1`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `n/a `

```text
document at all.
Programs use a range of techniques to deal with these types of issues. For example, some
structure their code to take advantage of the detailed semantics of specific operating systems.
Some operating systems guarantee that when a file is renamed and a file with the target name
already exists, the target name will always refer to either the old or new file, even after a
crash in the middle of the rename operation. In such a case, an implementation can create a
new file with the new version of the data and use the rename command to atomically replace
the old version with the new one.
Other programs essentially build a miniature file system over the top of  the underlying one,
structuring their data so that the underlying file system can better meet their performance and
```

#### Chunk 5

- Chunk ID: `203ad54f9c92365f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `n/a `

```text
file. Instead, a text editor will write a version of the file, and then it will append a sequence
of every change the user makes to that version. To avoid having to separately write every
typed character to disk, the editor will batch changes, e.g., all of the changes the user made in
the past 100 m illiseconds, and write those to disk as a unit. Even if the very latest batch has
not been written to disk, the user can usually recover the state of the file at almost the instant
immediately before the machine crash.
A dow nside of this algorithm for text editors is that it can cause information to be leaked
without it being visible in the current version of the file. Text editors sometimes use this same
method w hen the user hits “save” — just append any changes from the previous version,
```

### Method B

- Retrieval latency: 0.800s
- Generation latency: 8.576s

**Answer:**

Your computer uses the **file system** to keep track of files.

When you save a file, you usually give it a **name** and choose a **folder**, but you do not choose the physical disk location. The file system handles that mapping.

Conceptually, it works like this:

1. **You save a file with a name**
   Example:

   ```text
   /Users/alex/Documents/report.txt
   ```

2. **Folders/directories store name mappings**
   A directory is like a table saying:

   ```text
   report.txt → file metadata record
   ```

3. **The file metadata record stores where the data is**
   The metadata record is often called an **inode** on Unix/Linux systems, or a similar structure in other file systems.

   It contains information such as:

   - file size
   - permissions
   - timestamps
   - which disk blocks contain the file’s data

4. **The disk stores the actual contents in blocks**
   The file system chooses free blocks on disk and records something like:

   ```text
   report.txt → inode 1527 → blocks 9001, 9002, 9050, ...
   ```

So when you later open the file, the operating system follows the path:

```text
folder name → file name → metadata → disk blocks → file contents
```

You do not need to know the physical disk location because the **file system maintains that bookkeeping persistently on disk**. That way, even after the computer shuts down, it can still find the file later.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4f01a0801a136798`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `116`
- Score: `-1.04255 rerank_score`

```text
the file system can be separated in time: the writer of the file does not need to be running
at the same time as the file reader. Therefore, data needs to be stored persistently on
disk or other stable storage, and the data needs to be named so that you can find the file
when needed later on.
All three models are widely used bot h on a single system and ove r a network. For example,
the Google MapReduce utility operates over a network in a producer-consumer fashion: the
output of the map function is sent to the machines running the reduce function. The web is an
example of client-server computing, and many enterprises and universities run centralized file
servers to connect a text editor on one computer with a compiler running on another.
```

#### Chunk 2

- Chunk ID: `ad67d87468a57fd8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `-2.22345 rerank_score`

```text
method w hen the user hits “save” — just append any changes from the previous version,
rather than writing a fresh copy of the entire file. This means that the old version of a file can
potentially still be recovered from a file. So if you write a memo insulting your boss, and then
edit it to tone it dow n, it is best to save a completely new version of your file before you send
it off!
Will this method w ork for persistent memory? Keeping a log of every change to every
memory location in the process would be too slow. We would need to trap on every store
instruction and save the value to disk. In other words, we would run at the speed of the trap
handler, rather than the speed of the processor.
However, we can come close. When we take a checkpoint, we mark all pages as read-only to
```

#### Chunk 3

- Chunk ID: `a1181288210a7c85`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `135`
- Score: `-2.5109 rerank_score`

```text
saves a file, the program might call fsync() to tell the file system to make sure the
updates are stored on disk. Forcing the user to wait several seconds to save a file is not
acceptable.
ZFS’s solution is the ZFS Intent Log (ZIL), which is essentially a redo log. The ZIL is a
linked list of ZFS blocks that contain updates that have been forced to disk but whose
batch update may not yet have been stored. The ZIL is replayed when the file system is
mounted.
ZFS includes several optimizations in the ZIL implementation. First, by default writes
are buffered and committed in their batch update without being written to the ZIL; only
writes that are explicitly forced to disk are written to the ZIL. Second, the ZIL may
```

#### Chunk 4

- Chunk ID: `203ad54f9c92365f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `-4.15973 rerank_score`

```text
file. Instead, a text editor will write a version of the file, and then it will append a sequence
of every change the user makes to that version. To avoid having to separately write every
typed character to disk, the editor will batch changes, e.g., all of the changes the user made in
the past 100 m illiseconds, and write those to disk as a unit. Even if the very latest batch has
not been written to disk, the user can usually recover the state of the file at almost the instant
immediately before the machine crash.
A dow nside of this algorithm for text editors is that it can cause information to be leaked
without it being visible in the current version of the file. Text editors sometimes use this same
method w hen the user hits “save” — just append any changes from the previous version,
```

#### Chunk 5

- Chunk ID: `7197cd7f65f98917`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `-5.37724 rerank_score`

```text
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
of the old and new versions. For example, if a section is cut from one location and
pasted in another, after a crash the saved doc ument may end up with copies of the
section in both locations, one location, or neither location; or it may end up with a
region that is a mix of the old and new text.
Lost file. Third, if instead of overwriting the document file, the application writes
updates to a new file, then deletes the original file, and finally moves the new file to the
original file’s location, an untimely crash can leave the system with no copies of the
document at all.
Programs use a range of techniques to deal with these types of issues. For example, some
```

### Method C

- Retrieval latency: 0.196s
- Generation latency: 8.449s

**Answer:**

Your computer uses the **file system** to keep track of files.

When you save a file, you usually give it a **name** and maybe choose a **folder**, like:

```text
/home/Bob/Documents/report.txt
```

You are not choosing the physical disk location. Instead, the file system does that for you.

Conceptually, it keeps metadata like:

- the file’s name
- which folder/directory it belongs to
- its size
- permissions
- timestamps
- which disk blocks contain the file’s data

So the disk might contain something like:

```text
Directory entry:
"report.txt" → file ID 12345

File metadata for ID 12345:
size = 20 KB
data blocks = 801, 802, 945, 946
```

When you later open `report.txt`, the file system:

1. Looks in the directory for the name `report.txt`
2. Finds the internal file record for it
3. Uses that record to find the actual disk blocks
4. Reads those blocks and gives the data back to the program

So the key idea is:

> You name the file; the file system maps that name to metadata, and the metadata maps to the actual disk locations.

This is why files are described as **persistent, named data**: they survive after the program exits or the computer restarts, and you can find them again using a human-readable name.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `203ad54f9c92365f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `0.938334 vector_distance`

```text
file. Instead, a text editor will write a version of the file, and then it will append a sequence
of every change the user makes to that version. To avoid having to separately write every
typed character to disk, the editor will batch changes, e.g., all of the changes the user made in
the past 100 m illiseconds, and write those to disk as a unit. Even if the very latest batch has
not been written to disk, the user can usually recover the state of the file at almost the instant
immediately before the machine crash.
A dow nside of this algorithm for text editors is that it can cause information to be leaked
without it being visible in the current version of the file. Text editors sometimes use this same
method w hen the user hits “save” — just append any changes from the previous version,
```

#### Chunk 2

- Chunk ID: `bdcb15ce0dd48d36`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `1.02616 vector_distance`

```text
structuring their data so that the underlying file system can better meet their performance and
reliability requirements.
For example, a word processor might use a sophisticated doc ument format, allowing it to, for
example, add and remove embedded images and to always update a document by appending
updates to the end of the file.
As another example, a data analysis program might improve its performance by organizing its
accesses to input files in a way that ensures that each input file is read only once and that it is
read sequentially from its start to its end.
Or, a browser with a 1 GB on-disk cache might create 100 f iles, each containing 10 M B of
data, and group a given web site’s objects in a sequential region of a randomly selected file.
```

#### Chunk 3

- Chunk ID: `69e0bfb86e0fd180`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `1.0318 vector_distance`

```text
servers also keep copies of frequently requested pages in memory so that they can be
transmitted more quickly.
Web search. Both Google and Bing keep a cached copy of every web page they index.
This allows them to provide the copy of the web page if the original is unavailable for
some reason. The cached copy may be out of date — the search engines do n ot guarantee
that the copy instantaneously reflects any change in the original web page.
Email clients. Many email clients store a copy of mail messages on the client computer
to improve the client performance and to allow disconnected ope ration. In the
background, the client communicates with the server to keep the two copies in sync.
Incremental compilation. If you have ever built a program from multiple source files,
```

#### Chunk 4

- Chunk ID: `ad67d87468a57fd8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `1.03458 vector_distance`

```text
method w hen the user hits “save” — just append any changes from the previous version,
rather than writing a fresh copy of the entire file. This means that the old version of a file can
potentially still be recovered from a file. So if you write a memo insulting your boss, and then
edit it to tone it dow n, it is best to save a completely new version of your file before you send
it off!
Will this method w ork for persistent memory? Keeping a log of every change to every
memory location in the process would be too slow. We would need to trap on every store
instruction and save the value to disk. In other words, we would run at the speed of the trap
handler, rather than the speed of the processor.
However, we can come close. When we take a checkpoint, we mark all pages as read-only to
```

#### Chunk 5

- Chunk ID: `c42705ca3902362a`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `21`
- Score: `1.04277 vector_distance`

```text
periods of time. For example, Bob’s computer might store a collection of applications such as
/Applications/Calculator and /Program Files/Text Edit and a collection of data files such as
/home/Bob/correspondence/letter-to-mom.txt, and /home/Bob/Classes/OS/hw1.txt.
More precisely, a file system is an operating system abstraction that provides persistent,
named data. Persistent data is stored until it is explicitly deleted, even if the computer
storing it crashes or loses pow er. Named dat a can be accessed via a human-readable
identifier that the file system associates with the file. Having a name allows a file to be
accessed even after the program that created it has exited, and allows it to be shared by
multiple applications.
```

## q7

**Question:** If threads in the same process share the same address space, why don’t they also each need their own completely separate copy of the program’s code and global variables?

### Method A

- Retrieval latency: 0.182s
- Generation latency: 8.796s

**Answer:**

Because threads are not separate programs — they are separate **flows of execution inside the same process**.

So they share the process’s memory layout:

- **Code segment**: one copy of the program instructions
- **Global/static variables**: one shared set of process-wide variables
- **Heap**: shared dynamically allocated memory

Each thread only needs its own **execution state**, such as:

- program counter / instruction pointer
- CPU registers
- stack
- thread control block
- possibly thread-local variables

The key idea is:

> The code is just instructions. Multiple threads can execute the same instructions at the same time, each with its own registers and stack telling it where it is and what local data it is using.

For example, if two threads call the same function, they use the same machine code, but each has its own stack frame for that function call.

Global variables are shared because they belong to the **process**, not to an individual thread. If every thread had its own separate copy of globals, then they would behave more like separate processes.

That is also why shared globals can cause race conditions:

```c
int counter = 0; // shared by all threads
```

If two threads modify `counter` at the same time, they are modifying the same variable, so synchronization may be needed.

If a thread needs its own version of something “global-like,” it can use **thread-local storage**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `03e10455e217735a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `0.7674 vector_distance`

```text
processor).
4.4.2 Shared State
As oppos ed to per-thread state that is allocated for each thread, some state is shared between
threads running in the same process or within the operating system kernel (Figure 4.8). In
particular, program code is shared by all threads in a process, although each thread may be
executing at a different place within that code. Additionally, statically allocated global
variables and dynamically allocated heap variables can store information that is accessible
to all threads.
Other per-thread state: Thread-local variables
In addition to the per-thread state that corresponds to execution state in the single-threaded case, some systems include
additional thread-local variables. These variables are similar to global variables in that their scope spans different
```

#### Chunk 2

- Chunk ID: `402dc1a93def9ec4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `0.802716 vector_distance`

```text
Heap internals. Although a program’s heap is logically shared — it is acceptable for one thread to allocate an object
on the heap and then pass a pointer to that object to another thread — for performance reasons heaps may internally
subdivide their space into per-thread regions. The advantage of subdividing the heap is that multiple threads can each
allocate objects at the same time without interfering with one another. Further, by allocating objects used by the same
thread from the same memory region, cache hit rates may improve. To implement these optimizations, each
subdivision of the heap has thread-local variables that track what parts of the thread-local heap are in use, what parts
```

#### Chunk 3

- Chunk ID: `9473821b6a0a4e47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `92`
- Score: `0.80823 vector_distance`

```text
variables, then a thread’s code can refer to an object’s global name to reference it; the
compiler computes the corresponding address. If shared obj ects are dynamically allocated,
then each thread that uses an object needs a pointer or reference to it.
Two common ways to provide a thread a pointer to a shared obj ect are: (1) provide a pointer
to the shared obj ect when the thread is created, and (2) store references to shared obj ects in
other shared obj ects (e.g., containers). For example, a program might have a global, shared
(and synchronized!) hash table that threads can use to store and retrieve references to other
shared obj ects.
Figure 5.5 shows a simple program that creates three queues and then creates some threads
```

#### Chunk 4

- Chunk ID: `57b6d1fb0988a6ea`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `25`
- Score: `0.821858 vector_distance`

```text
processes can share a code segment by setting up an entry in their segment tables to poi nt to
the same region of physical memory — to use the same base and bou nds. The processes can
share the same code while working off different data, by setting up the segment table to poi nt
to different regions of physical memory for the data segment. We illustrate this in Figure 8.4.
Likewise, shared library routines, such as a graphics library, can be placed into a segment
and shared between processes. As before, the library data would be in a separate, non-shared
segment. This is frequently done in modern operating systems with dynamically linked
libraries. A practical issue is that different processes may load different numbers of libraries,
```

#### Chunk 5

- Chunk ID: `d6663386a50dc468`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `0.835595 vector_distance`

```text
subdivision of the heap has thread-local variables that track what parts of the thread-local heap are in use, what parts
are free, and so on. Then, the code that allocates new memory (e.g., malloc and new) is written to use these thread-
local data structures and only take memory from the shared heap if the local heap is empty.
Thread-local variables are often useful, but, for simplicity, the rest of our discussion focuses only on the TCB, registers, and
stack as the core pieces of per-thread state.
```

### Method B

- Retrieval latency: 0.562s
- Generation latency: 10.586s

**Answer:**

Because threads in the same process are meant to be **multiple execution streams inside one shared program instance**.

Each thread needs its own:

- **program counter**: where it currently is in the code
- **registers**
- **stack**: for its function calls and local variables

But they do **not** need their own separate copy of:

- the program’s **code**
- global/static variables
- heap objects

because those live in the process’s **shared address space**.

So you can think of it like this:

```text
Process
 ├── code segment        shared by all threads
 ├── global variables    shared by all threads
 ├── heap                shared by all threads
 ├── stack for thread 1  private
 ├── stack for thread 2  private
 └── stack for thread 3  private
```

The code is usually read-only, so many threads can safely execute the same instructions at the same time. They may just be at different places in that code, because each thread has its own program counter.

Global variables are shared because they represent the process’s common state. For example:

```c
int counter = 0;  // global variable shared by all threads
```

If two threads access `counter`, they are accessing the same variable. That is useful, but it also means synchronization may be needed to avoid race conditions.

If every thread had its own full copy of the code and globals, then they would be more like separate processes, not threads. It would waste memory and make sharing data between them harder.

If you want a “global-like” variable that is separate per thread, many systems provide **thread-local storage**, e.g.:

```c
__thread int my_counter;
```

So the key idea is:

> Threads share the process’s code, globals, and heap, but each thread has its own execution state: stack, registers, and program counter.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `03e10455e217735a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `1.55359 rerank_score`

```text
processor).
4.4.2 Shared State
As oppos ed to per-thread state that is allocated for each thread, some state is shared between
threads running in the same process or within the operating system kernel (Figure 4.8). In
particular, program code is shared by all threads in a process, although each thread may be
executing at a different place within that code. Additionally, statically allocated global
variables and dynamically allocated heap variables can store information that is accessible
to all threads.
Other per-thread state: Thread-local variables
In addition to the per-thread state that corresponds to execution state in the single-threaded case, some systems include
additional thread-local variables. These variables are similar to global variables in that their scope spans different
```

#### Chunk 2

- Chunk ID: `345705ff3bf2d6b9`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `52`
- Score: `0.927509 rerank_score`

```text
receiving network input. Each of these separate activities has its own program counter and
stack but operates on the same code and data as the other threads. The operating system runs
multiple threads in a process, in much the same way that it runs multiple processes in
physical memory. We generalize on the process abstraction to allow multiple activities in the
same protection dom ain in Chapter 4.
```

#### Chunk 3

- Chunk ID: `402dc1a93def9ec4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `-0.0564711 rerank_score`

```text
Heap internals. Although a program’s heap is logically shared — it is acceptable for one thread to allocate an object
on the heap and then pass a pointer to that object to another thread — for performance reasons heaps may internally
subdivide their space into per-thread regions. The advantage of subdividing the heap is that multiple threads can each
allocate objects at the same time without interfering with one another. Further, by allocating objects used by the same
thread from the same memory region, cache hit rates may improve. To implement these optimizations, each
subdivision of the heap has thread-local variables that track what parts of the thread-local heap are in use, what parts
```

#### Chunk 4

- Chunk ID: `38803452a731c236`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `25`
- Score: `-0.0961892 rerank_score`

```text
Figure 8.4: Two processes sharing a code segment, but with separate data and stack segments. In this case, each process
uses the same virtual addresses, but these virtual addresses map to either the same region of physical memory (if code) or
different regions of physical memory (if data).
Although simple to implement and manage, segmented memory is both remarkably pow erful
and widely used. For example, the x86 architecture is segmented (with some enhancements
that we will describe later). With segments, the operating system can allow processes to
share some regions of memory while keeping other regions protected. For example, two
processes can share a code segment by setting up an entry in their segment tables to poi nt to
```

#### Chunk 5

- Chunk ID: `a70fedc19b3ddee2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `69`
- Score: `-0.28553 rerank_score`

```text
5. Synchronizing Access to Shared Objects
It is not enough to be industrious. So are the ants. The question is: What are we industrious
about? —Henry David Thoreau
Multi-threaded programs extend the traditional, single-threaded programming model so that
each thread provides a single sequential stream of execution composed of familiar
instructions. If a program has independent threads that operate on completely separate
subsets of memory, we can reason about each thread separately. In this case, reasoning about
independent threads differs little from reasoning about a series of independent, single-
threaded programs.
However, most multi-threaded programs have both per-thread state (e.g., a thread’s stack
```

### Method C

- Retrieval latency: 0.766s
- Generation latency: 8.498s

**Answer:**

Because threads in the same process are meant to be multiple execution paths **inside one program instance**.

They share the process’s address space, so they can all refer to the same:

- **program code**
- **global/static variables**
- **heap objects**

They do **not** need separate copies of the code because code is usually read-only. Each thread just has its own **program counter/registers** saying *where* in that shared code it is currently executing.

For example:

```c
void work() {
    printf("hello\n");
}
```

If three threads run `work()`, there is still only one copy of the machine instructions for `work()`. Each thread may be at a different instruction in that same code.

Global variables are also shared because they represent process-wide state:

```c
int counter = 0;
```

All threads see the same `counter`. That is useful, but it also means access must be synchronized if multiple threads modify it.

What each thread needs separately is its **execution state**, such as:

- registers
- program counter
- stack
- thread control block
- possibly thread-local variables

So the idea is:

```text
Shared by threads:
  code
  global variables
  heap

Private per thread:
  registers
  stack
  program counter
```

Separate copies of code and globals would make the threads behave more like separate processes rather than threads in the same process.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `03e10455e217735a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `n/a `

```text
processor).
4.4.2 Shared State
As oppos ed to per-thread state that is allocated for each thread, some state is shared between
threads running in the same process or within the operating system kernel (Figure 4.8). In
particular, program code is shared by all threads in a process, although each thread may be
executing at a different place within that code. Additionally, statically allocated global
variables and dynamically allocated heap variables can store information that is accessible
to all threads.
Other per-thread state: Thread-local variables
In addition to the per-thread state that corresponds to execution state in the single-threaded case, some systems include
additional thread-local variables. These variables are similar to global variables in that their scope spans different
```

#### Chunk 2

- Chunk ID: `402dc1a93def9ec4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `n/a `

```text
Heap internals. Although a program’s heap is logically shared — it is acceptable for one thread to allocate an object
on the heap and then pass a pointer to that object to another thread — for performance reasons heaps may internally
subdivide their space into per-thread regions. The advantage of subdividing the heap is that multiple threads can each
allocate objects at the same time without interfering with one another. Further, by allocating objects used by the same
thread from the same memory region, cache hit rates may improve. To implement these optimizations, each
subdivision of the heap has thread-local variables that track what parts of the thread-local heap are in use, what parts
```

#### Chunk 3

- Chunk ID: `9473821b6a0a4e47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `92`
- Score: `n/a `

```text
variables, then a thread’s code can refer to an object’s global name to reference it; the
compiler computes the corresponding address. If shared obj ects are dynamically allocated,
then each thread that uses an object needs a pointer or reference to it.
Two common ways to provide a thread a pointer to a shared obj ect are: (1) provide a pointer
to the shared obj ect when the thread is created, and (2) store references to shared obj ects in
other shared obj ects (e.g., containers). For example, a program might have a global, shared
(and synchronized!) hash table that threads can use to store and retrieve references to other
shared obj ects.
Figure 5.5 shows a simple program that creates three queues and then creates some threads
```

#### Chunk 4

- Chunk ID: `57b6d1fb0988a6ea`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `25`
- Score: `n/a `

```text
processes can share a code segment by setting up an entry in their segment tables to poi nt to
the same region of physical memory — to use the same base and bou nds. The processes can
share the same code while working off different data, by setting up the segment table to poi nt
to different regions of physical memory for the data segment. We illustrate this in Figure 8.4.
Likewise, shared library routines, such as a graphics library, can be placed into a segment
and shared between processes. As before, the library data would be in a separate, non-shared
segment. This is frequently done in modern operating systems with dynamically linked
libraries. A practical issue is that different processes may load different numbers of libraries,
```

#### Chunk 5

- Chunk ID: `d6663386a50dc468`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `37`
- Score: `n/a `

```text
subdivision of the heap has thread-local variables that track what parts of the thread-local heap are in use, what parts
are free, and so on. Then, the code that allocates new memory (e.g., malloc and new) is written to use these thread-
local data structures and only take memory from the shared heap if the local heap is empty.
Thread-local variables are often useful, but, for simplicity, the rest of our discussion focuses only on the TCB, registers, and
stack as the core pieces of per-thread state.
```

## q8

**Question:** If a program uses multiple threads instead of multiple processes, does that automatically make it faster?

### Method A

- Retrieval latency: 0.773s
- Generation latency: 8.572s

**Answer:**

No — using multiple threads instead of multiple processes does **not automatically** make a program faster.

Threads can be faster in some cases because:

- creating/switching threads is often cheaper than processes,
- threads share the same address space, so communication between them can be easier/faster,
- on multiple CPU cores, threads can run in parallel.

But threads can also **fail to improve performance** or even make it worse if:

- the work is not parallelizable,
- threads spend time waiting for locks,
- there is too much synchronization overhead,
- they compete for the same CPU, memory, disk, or network resource,
- the program becomes more complex and less efficient.

For example, if a program is mostly doing one sequential calculation, adding threads may not help. But if it has independent tasks, or many I/O operations, threads may improve responsiveness or throughput.

So the short answer is:

> Multiple threads can make a program faster, especially on multiple processors, but only if the workload and implementation actually benefit from parallelism. Otherwise, they may provide little or no speedup.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `c1d23ef43d344a6a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `62`
- Score: `n/a `

```text
poor performance when processes had many threads, Linux 2.6 revamped the thread
system, improving its scalability and absolute performance.
Anecdotal evidence suggests that the performance gap between the two approaches has
greatly narrowed. For some applications, highly optimized thread management code and
synchronous I/O paths can out-perform less-optimized application code and
asynchronous I/O paths. In most cases, the performance difference is small enough that
other factors (e.g., code simplicity and ease of maintenance) are more important than
raw performance. If performance is crucial for a particular application, then, as is often
the case, there is no substitute for careful benchmarking before making your decision.
```

#### Chunk 2

- Chunk ID: `0c33128c8c17401d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `62`
- Score: `n/a `

```text
the case, there is no substitute for careful benchmarking before making your decision.
Performance: Exploiting multiple processors. By itself, the event-driven approach
does not help a program exploit multiple processors. In practice, event-driven and
thread approaches are often combined: a program that uses n processors can have n
threads, each of which uses the event-driven pattern to multiplex multiple I/O-bound
tasks on each processor.
Responsiveness: Shifting work to run in the background. While event-driven
programming can be effective when tasks are usually short-lived, threads can be more
convenient when there is a mixture of foreground and background tasks. At some cost in
coding complexity, the event-driven model can be adapted to this case, e.g., by cutting
```

#### Chunk 3

- Chunk ID: `7cd935cd1e5b2cdf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `66`
- Score: `n/a `

```text
based on threads. At about the same time, the interface to thread libraries became
standardized, starting with POSIX in 1995. L ikewise, modern programming languages such as
Java were designed with constructs for creating and synchronizing threads.
The increasing importance of parallel processing led to the development of very lightweight
user-level thread implementations, as there is little point to parallelizing an application
unless it improves performance. By the early 90’s, scheduler activations were developed to
integrate user-level and kernel threads [2].
Even so, the topic of whether threads are a better programming model than the alternatives
remains an active one [159]. Several prominent operating systems researchers have argued
```

#### Chunk 4

- Chunk ID: `35983b4f94a93422`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `22`
- Score: `n/a `

```text
loops , calls/returns from procedures, etc. However, a program can now have several such
threads executing at the same time.
When is it appropriate to use multiple threads within the same program? Threads have
become widely used in both operating system and application code, and based on that
experience, we can identify several common themes. We illustrate these themes by describing
one application in some detail, to show how and why it leverages threads.
```

#### Chunk 5

- Chunk ID: `ce01248ab14e5f75`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `25`
- Score: `n/a `

```text
returns immediately to the application. In the background, the operating system kernel
runs a separate thread to flush the modified data out to disk. Another example is on file
reads: the kernel can have a thread which attempts to anticipate which blocks are likely
to be read next (e.g., if the application is reading a large file from beginning to end), and
to bring those blocks from disk before the application asks for them.
Performance: exploiting multiple processors. Programs can use threads on a
multiprocessor to do w ork in parallel; they can do the same work in less time or more
work in the same elapsed time. Today, a server might have more than a dozen
processors; a desktop or laptop may include eight processor cores; even most
```

### Method B

- Retrieval latency: 0.207s
- Generation latency: 6.349s

**Answer:**

No — using multiple threads instead of multiple processes does **not automatically** make a program faster.

Threads can be faster in some cases because:

- creating/switching threads is often cheaper than processes,
- threads share the same address space, so communication can be easier,
- multiple threads can run in parallel on multiple CPU cores.

But performance depends on the workload.

A multithreaded program may **not** be faster if:

- the task is mostly sequential,
- threads spend time waiting for locks,
- there is too much synchronization overhead,
- all threads compete for the same CPU, memory, or I/O resource,
- the program has only one CPU core available,
- the implementation is poorly designed.

Multiple processes can also run in parallel on multiple cores, so threads are not automatically superior.

A good rule of thumb:

> Threads can improve performance when there is real parallel work or useful background work to do, but they can also add overhead and complexity.

If performance really matters, the best answer is to **benchmark** both designs for the specific program.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `35983b4f94a93422`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `22`
- Score: `0.745617 vector_distance`

```text
loops , calls/returns from procedures, etc. However, a program can now have several such
threads executing at the same time.
When is it appropriate to use multiple threads within the same program? Threads have
become widely used in both operating system and application code, and based on that
experience, we can identify several common themes. We illustrate these themes by describing
one application in some detail, to show how and why it leverages threads.
```

#### Chunk 2

- Chunk ID: `ce01248ab14e5f75`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `25`
- Score: `0.759881 vector_distance`

```text
returns immediately to the application. In the background, the operating system kernel
runs a separate thread to flush the modified data out to disk. Another example is on file
reads: the kernel can have a thread which attempts to anticipate which blocks are likely
to be read next (e.g., if the application is reading a large file from beginning to end), and
to bring those blocks from disk before the application asks for them.
Performance: exploiting multiple processors. Programs can use threads on a
multiprocessor to do w ork in parallel; they can do the same work in less time or more
work in the same elapsed time. Today, a server might have more than a dozen
processors; a desktop or laptop may include eight processor cores; even most
```

#### Chunk 3

- Chunk ID: `c1d23ef43d344a6a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `62`
- Score: `0.763397 vector_distance`

```text
poor performance when processes had many threads, Linux 2.6 revamped the thread
system, improving its scalability and absolute performance.
Anecdotal evidence suggests that the performance gap between the two approaches has
greatly narrowed. For some applications, highly optimized thread management code and
synchronous I/O paths can out-perform less-optimized application code and
asynchronous I/O paths. In most cases, the performance difference is small enough that
other factors (e.g., code simplicity and ease of maintenance) are more important than
raw performance. If performance is crucial for a particular application, then, as is often
the case, there is no substitute for careful benchmarking before making your decision.
```

#### Chunk 4

- Chunk ID: `0c33128c8c17401d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `62`
- Score: `0.767101 vector_distance`

```text
the case, there is no substitute for careful benchmarking before making your decision.
Performance: Exploiting multiple processors. By itself, the event-driven approach
does not help a program exploit multiple processors. In practice, event-driven and
thread approaches are often combined: a program that uses n processors can have n
threads, each of which uses the event-driven pattern to multiplex multiple I/O-bound
tasks on each processor.
Responsiveness: Shifting work to run in the background. While event-driven
programming can be effective when tasks are usually short-lived, threads can be more
convenient when there is a mixture of foreground and background tasks. At some cost in
coding complexity, the event-driven model can be adapted to this case, e.g., by cutting
```

#### Chunk 5

- Chunk ID: `7cd935cd1e5b2cdf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `66`
- Score: `0.773589 vector_distance`

```text
based on threads. At about the same time, the interface to thread libraries became
standardized, starting with POSIX in 1995. L ikewise, modern programming languages such as
Java were designed with constructs for creating and synchronizing threads.
The increasing importance of parallel processing led to the development of very lightweight
user-level thread implementations, as there is little point to parallelizing an application
unless it improves performance. By the early 90’s, scheduler activations were developed to
integrate user-level and kernel threads [2].
Even so, the topic of whether threads are a better programming model than the alternatives
remains an active one [159]. Several prominent operating systems researchers have argued
```

### Method C

- Retrieval latency: 0.567s
- Generation latency: 8.310s

**Answer:**

No — using multiple threads does **not automatically** make a program faster.

Threads can help when:

- the work can actually run in parallel on multiple CPU cores,
- one thread can do useful work while another waits for I/O,
- sharing memory between tasks is useful and avoids expensive inter-process communication.

But threads can also make a program **slower** because of:

- thread creation and scheduling overhead,
- locking and synchronization costs,
- contention for shared data,
- cache/memory effects,
- bugs or delays caused by unpredictable interleavings.

A useful rule of thumb:

> Threads improve performance only if the program has independent work that can overlap or run in parallel.

For example:

- **Good use of threads:** processing different chunks of a large image on multiple cores.
- **Not necessarily faster:** multiple threads all waiting for the same lock or modifying the same shared structure.

So the answer is: **threads may be faster than processes in some cases, but speed is not automatic; you need to consider the workload and often benchmark it.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `35983b4f94a93422`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `22`
- Score: `3.97089 rerank_score`

```text
loops , calls/returns from procedures, etc. However, a program can now have several such
threads executing at the same time.
When is it appropriate to use multiple threads within the same program? Threads have
become widely used in both operating system and application code, and based on that
experience, we can identify several common themes. We illustrate these themes by describing
one application in some detail, to show how and why it leverages threads.
```

#### Chunk 2

- Chunk ID: `0c33128c8c17401d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `62`
- Score: `3.40181 rerank_score`

```text
the case, there is no substitute for careful benchmarking before making your decision.
Performance: Exploiting multiple processors. By itself, the event-driven approach
does not help a program exploit multiple processors. In practice, event-driven and
thread approaches are often combined: a program that uses n processors can have n
threads, each of which uses the event-driven pattern to multiplex multiple I/O-bound
tasks on each processor.
Responsiveness: Shifting work to run in the background. While event-driven
programming can be effective when tasks are usually short-lived, threads can be more
convenient when there is a mixture of foreground and background tasks. At some cost in
coding complexity, the event-driven model can be adapted to this case, e.g., by cutting
```

#### Chunk 3

- Chunk ID: `deb1b9004b45d8e1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `28`
- Score: `3.39026 rerank_score`

```text
the processor, starving other threads and making the system’s user interface sluggish or non-responsive. Additionally, modern
multiprocessor machines run multiple threads at a time, so one would still have to reason about the possible interactions
between threads even if cooperative multi-threading were used. Thus, although cooperative multi-threading was used in some
significant systems in the past, including early versions of Apple’s MacOS operating system, it is less often used today.
The alternative we describe in this book is sometimes called preemptive multi-threading since running threads can be
switched at any time. Whenever the book uses the term “multi-threading,” it means preemptive multi-threading unless we
explicitly state otherwise.
4.2.2 Why “U npredictable Speed”?
```

#### Chunk 4

- Chunk ID: `30c2658b07291031`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `3.31145 rerank_score`

```text
It may seem strange to require programmers to assume that a thread’s virtual processor runs at
an unpredictable speed and that any interleaving with other threads is possible. Surely, the
programmer should be able to take advantage of the fact that some interleavings are more
likely than others?
The thread programming model adopts this assumption as a way to guide programmers when
reasoning about correctness. Rather than assuming that one thread runs at the same speed as
another (or faster or slower) and trying to write programs that coordinate threads based on
their relative speed of execution, multi-threaded programs should make no assumptions about
the behavior of the thread scheduler. In turn, the kernel’s scheduling decisions — w hen to
```

#### Chunk 5

- Chunk ID: `c9a24201072d05d8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `26`
- Score: `3.23539 rerank_score`

```text
it preempts one of the running threads so the kernel can run the interrupt handler; when the handler finishes, the kernel
resumes that thread.
Many single-threaded processes. As recently as twenty years ago, many operating systems supported multiple
processes but only one thread per process. To the kernel, however, each process looks like a thread: a separate
sequence of instructions, executing sometimes in the kernel and sometimes at user level. For example, on a
multiprocessor, if multiple processes perform system calls at the same time, the kernel, in effect, has multiple threads
executing concurrently in kernel mode.
Many kernel threads. To manage complexity, shift work to the background, exploit parallelism, and hide I/O latency,
```

## q9

**Question:** People say race conditions are “timing-dependent bugs.” Does that just mean they only happen on slow machines or under heavy load?

### Method A

- Retrieval latency: 0.785s
- Generation latency: 6.920s

**Answer:**

No. “Timing-dependent” does **not** mean “only on slow machines” or “only under heavy load.”

It means the bug depends on the **relative ordering of operations between threads**.

For example, suppose two threads both do:

```text
read x
add 1
write x
```

If they interleave like this:

```text
Thread A reads x = 0
Thread B reads x = 0
Thread A writes x = 1
Thread B writes x = 1
```

then one increment is lost. But if one thread finishes before the other starts, the result may be correct.

So the bug depends on *which thread gets to which instruction first*, not simply on whether the machine is slow.

Heavy load, cache misses, different CPU speeds, debugging, `printf`, or scheduling changes can make the bad interleaving **more or less likely**, which is why race conditions can seem to appear randomly. But the underlying problem is missing or incorrect synchronization around shared state.

So a better definition is:

> A race condition is a bug where the program’s correctness depends on an unpredictable ordering of concurrent actions.

Slow machines and heavy load don’t create the race; they may just make it easier to observe.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `fd48fd852a20fb7d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `n/a `

```text
Even if we could ignore the issue of scheduling — e .g., if there are more processors than
threads so that each thread is assigned its own physical processor — the physical reality is
that the relative execution speed of different threads can be significantly affected by factors
outside their control. An extreme example is that the programmer may be debugging one
thread by single-stepping it, while other threads run at full speed on other processors. If the
programmer is to have any hope of understanding concurrent program behavior, the program’s
correctness cannot depend on which threads are being observed.
Variability in execution speed occurs during normal operation as well. Accessing memory
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
```

#### Chunk 2

- Chunk ID: `1be8686b3adb84e0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `70`
- Score: `n/a `

```text
How can w e reason about  all possible interleavings of threads’ actions in a multi-
million line program?
2. Program execution can be nondeterministic. Different runs of the same program may
produce different results. For example, the scheduler may make different scheduling
decisions, the processor may run at a different frequency, or another concurrently
running program may affect the cache hit rate. Even common debugging techniques —
such as running a program under a debugger, recompiling with the -g option instead of -
O, or adding a printf — c an change how a program behaves.
Jim Gray, the 1998 A CM Turing Award winner, coined the term Heisenbugs  for bugs
that disappear or change behavior when you try to examine them. Multi-threaded
```

#### Chunk 3

- Chunk ID: `0eb7ae249bc0700d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `70`
- Score: `n/a `

```text
that disappear or change behavior when you try to examine them. Multi-threaded
programming is a common source of Heisenbugs. In contrast, Bohrbugs  are
deterministic and generally much easier to diagnose.
How can w e debug pr ograms with behaviors that change  across runs?
3. Compilers and processor hardware can reorder instructions. Modern compilers and
hardware reorder instructions to improve performance. This reordering is generally
invisible to single-threaded programs; compilers and processors take care to ensure that
dependencies within a single sequence of instructions — that is, within a thread — a re
preserved. However, reordering can become visible when multiple threads interact
through accessing shared variables.
```

#### Chunk 4

- Chunk ID: `4f0ef6aaddf73230`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `n/a `

```text
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
include how frequently the scheduler preempts the thread, how many physical processors are
present on a machine, how large the caches are, how fast the memory is, how the energy-
saving firmware adjusts the processors’ clock speeds, what network messages arrive, or
what input is received from the user. Execution speeds for the different threads of a program
are hard to predict, can vary on different hardware, and can even vary from run to run on the
same hardware. As a result, we must coordinate thread actions through explicit
synchronization rather than by trying to reason about their relative speed.
EXAMPLE: Is a kernel interrupt handler a thread?
```

#### Chunk 5

- Chunk ID: `dc7792a11218f240`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `121`
- Score: `n/a `

```text
provide deterministic execution in this setting. Provided that the program being debugged has
no race conditions — that is, no access to shared memory outside of a critical section — then
its behavior will be deterministic with one more piece of information. In addition to the
initial state, inputs, and asynchronous interrupts, we also need to record which thread
acquires each critical section in which order. If we replay the threads in that order and
deliver interrupts precisely and provide the same device input, the behavior will be the same.
Whether this is a practical solution is still an open question.
```

### Method B

- Retrieval latency: 0.734s
- Generation latency: 6.661s

**Answer:**

No. “Timing-dependent” does **not** mean “only on slow machines” or “only under heavy load.”

It means the bug depends on the **relative ordering/interleaving** of operations from different threads/processes.

For example, if two threads both do:

```text
read x
add 1
write x
```

then the result depends on whether their steps interleave like this:

```text
Thread A: read x = 0
Thread B: read x = 0
Thread A: write x = 1
Thread B: write x = 1
```

Now one increment is lost. That is a race condition.

A slow machine or heavy load can make certain interleavings **more likely**, because threads may be interrupted more often or scheduled differently. But a race condition can also happen on:

- fast machines
- lightly loaded machines
- only once in a million runs
- after years of apparently correct behavior

So “timing-dependent” really means:

> The program’s correctness depends on which thread happens to reach shared data first.

That is why race conditions are often hard to reproduce and debug.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `2fa7bd45f10af57b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `73`
- Score: `-5.26652 rerank_score`

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

#### Chunk 2

- Chunk ID: `b1c69f298d48bcb3`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `75`
- Score: `-5.35388 rerank_score`

```text
Because the problem required a rare sequence of events, the machine appeared to work successfully for almost all patients.
Years elapsed between the first incident and the final one, and during this period, the manufacturer repeatedly insisted that no
overdose was possible and that the patient injuries must be due to some other factor. It took the second occurrence of the
race condition at the same hospital to help reveal the system’s design flaw.
```

#### Chunk 3

- Chunk ID: `dc7792a11218f240`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `121`
- Score: `-6.71847 rerank_score`

```text
provide deterministic execution in this setting. Provided that the program being debugged has
no race conditions — that is, no access to shared memory outside of a critical section — then
its behavior will be deterministic with one more piece of information. In addition to the
initial state, inputs, and asynchronous interrupts, we also need to record which thread
acquires each critical section in which order. If we replay the threads in that order and
deliver interrupts precisely and provide the same device input, the behavior will be the same.
Whether this is a practical solution is still an open question.
```

#### Chunk 4

- Chunk ID: `e4069986d30cb2eb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `-8.24879 rerank_score`

```text
circumstances that affect whether deadlock or starvation occurs could include a broad range
of factors, such as: the choices made by the scheduler, the number of threads running, the
workload or sequence of requests processed by the system, which threads win races to
acquire locks, and which threads are enabled in what order when signals or broadcasts occur.
A system that is subject to starvation or deadlock may be live in many or most runs and starve
or deadlock only for particular workloads or “unlucky” interleavings. For example, in
mutually recursive locking, the deadlock only occurs if both threads obtain the outer locks at
about the same time. For the Dining Philosophers problem, philosophers may succeed in
```

#### Chunk 5

- Chunk ID: `ca84b9a9834d4148`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `148`
- Score: `-8.74531 rerank_score`

```text
you expect to wait longer the longer you have already waited.
Heisenbugs
Bugs in concurrent programs that disappear or change behavior when you try to examine
them. See also: Bohrbugs .
hint
```

### Method C

- Retrieval latency: 0.202s
- Generation latency: 6.813s

**Answer:**

No. “Timing-dependent” does **not** mean “only on slow machines” or “only under heavy load.”

It means the bug depends on the **relative order and timing of operations between threads/processes**.

For example, suppose two threads both access the same shared variable:

```c
counter = counter + 1;
```

That operation is not really one step. It may involve:

1. read `counter`
2. add 1
3. write `counter`

A race can happen if two threads interleave like this:

```text
Thread A reads counter = 0
Thread B reads counter = 0
Thread A writes 1
Thread B writes 1
```

The final value is `1`, even though two increments happened.

That bug depends on **how the operations interleave**, not simply on whether the machine is slow.

A slow machine, heavy load, cache misses, debugger, or `printf` statements can make certain interleavings more or less likely. But the underlying problem is that the program’s correctness depends on timing instead of proper synchronization.

So a better way to think of it is:

> A race condition is a bug where the result depends on an uncontrolled ordering of concurrent actions.

The fix is usually to use synchronization, such as locks, atomics, semaphores, or message passing, so correctness no longer depends on lucky timing.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `fd48fd852a20fb7d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `0.909811 vector_distance`

```text
Even if we could ignore the issue of scheduling — e .g., if there are more processors than
threads so that each thread is assigned its own physical processor — the physical reality is
that the relative execution speed of different threads can be significantly affected by factors
outside their control. An extreme example is that the programmer may be debugging one
thread by single-stepping it, while other threads run at full speed on other processors. If the
programmer is to have any hope of understanding concurrent program behavior, the program’s
correctness cannot depend on which threads are being observed.
Variability in execution speed occurs during normal operation as well. Accessing memory
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
```

#### Chunk 2

- Chunk ID: `1be8686b3adb84e0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `70`
- Score: `0.988113 vector_distance`

```text
How can w e reason about  all possible interleavings of threads’ actions in a multi-
million line program?
2. Program execution can be nondeterministic. Different runs of the same program may
produce different results. For example, the scheduler may make different scheduling
decisions, the processor may run at a different frequency, or another concurrently
running program may affect the cache hit rate. Even common debugging techniques —
such as running a program under a debugger, recompiling with the -g option instead of -
O, or adding a printf — c an change how a program behaves.
Jim Gray, the 1998 A CM Turing Award winner, coined the term Heisenbugs  for bugs
that disappear or change behavior when you try to examine them. Multi-threaded
```

#### Chunk 3

- Chunk ID: `0eb7ae249bc0700d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `70`
- Score: `0.991295 vector_distance`

```text
that disappear or change behavior when you try to examine them. Multi-threaded
programming is a common source of Heisenbugs. In contrast, Bohrbugs  are
deterministic and generally much easier to diagnose.
How can w e debug pr ograms with behaviors that change  across runs?
3. Compilers and processor hardware can reorder instructions. Modern compilers and
hardware reorder instructions to improve performance. This reordering is generally
invisible to single-threaded programs; compilers and processors take care to ensure that
dependencies within a single sequence of instructions — that is, within a thread — a re
preserved. However, reordering can become visible when multiple threads interact
through accessing shared variables.
```

#### Chunk 4

- Chunk ID: `4f0ef6aaddf73230`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `1.01516 vector_distance`

```text
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
include how frequently the scheduler preempts the thread, how many physical processors are
present on a machine, how large the caches are, how fast the memory is, how the energy-
saving firmware adjusts the processors’ clock speeds, what network messages arrive, or
what input is received from the user. Execution speeds for the different threads of a program
are hard to predict, can vary on different hardware, and can even vary from run to run on the
same hardware. As a result, we must coordinate thread actions through explicit
synchronization rather than by trying to reason about their relative speed.
EXAMPLE: Is a kernel interrupt handler a thread?
```

#### Chunk 5

- Chunk ID: `ad63b53371885277`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `281`
- Score: `1.05197 vector_distance`

```text
you expect to wait longer the longer you have already waited.
Heisenbugs
Bugs in concurrent programs that disappear or change behavior when you try to examine
them. See also: Bohrbugs .
hint
```

## q10

**Question:** If a lock guarantees mutual exclusion, why do we need condition variables too?

### Method A

- Retrieval latency: 0.437s
- Generation latency: 8.062s

**Answer:**

A lock and a condition variable solve different problems.

A **lock** gives **mutual exclusion**:

> “Only one thread at a time may access this shared state.”

But often a thread also needs to wait until some **condition about the shared state** becomes true:

> “The queue is not empty.”  
> “The buffer is not full.”  
> “The task is finished.”

A **condition variable** lets a thread wait for that condition **without wasting CPU and without holding the lock while waiting**.

Example: producer/consumer queue

```c
lock.acquire();

while (queue.empty()) {
    cond.wait(lock);
}

item = queue.remove();

lock.release();
```

The lock protects `queue`, so only one thread modifies it at a time.

But if the queue is empty, the consumer cannot continue. If it just kept the lock and waited, the producer could never acquire the lock to add an item. That could cause deadlock.

So `cond.wait(lock)` does something special:

1. releases the lock,
2. puts the thread to sleep,
3. later, when signaled, wakes it up,
4. reacquires the lock before returning.

Then a producer can do:

```c
lock.acquire();

queue.add(item);
cond.signal();

lock.release();
```

So:

- **Lock**: protects shared state from simultaneous access.
- **Condition variable**: lets threads sleep until shared state reaches some desired condition.

In short:  
A lock answers **“who may access the state?”**  
A condition variable answers **“when is it useful to continue?”**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `842bfa77f8646f56`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `5.97523 rerank_score`

```text
mutual exclusion when accessing shared state.
5.7.6 Implementing Condition Variables
We can implement condition variables using a similar approach to the one used to implement
locks, with one simplification: since the lock is held whenever the wait, signal, or
broadcast is called, we already have mutually exclusive access to the condition wait queue.
As with locks, care is needed to prevent a waiting thread from being put back on the ready
list until it has completed its context switch; we can accomplish this by acquiring the
scheduler spinlock before we release the monitor lock. Another thread may acquire the
monitor lock and start to signal the waiting thread, bu t it will not be able to complete the
signal until the scheduler lock is released immediately after the context switch.
```

#### Chunk 2

- Chunk ID: `259c96c1742883cf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `85`
- Score: `4.11004 rerank_score`

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

- Chunk ID: `31adea97e6dd91ae`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `3.6602 rerank_score`

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

#### Chunk 4

- Chunk ID: `4989c76c1b2546a9`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `88`
- Score: `3.26346 rerank_score`

```text
1. Mutual Exclusion. At most one thread holds the lock.
2. Progress. If no thread holds the lock and any thread attempts to acquire the lock, then
eventually some thread succeeds in acquiring the lock.
3. Bounded waiting. If thread T attempts to acquire a lock, then there exists a bound on the
number of times other threads can successfully acquire the lock before T does.
Mutual exclusion is a safety property because locks prevent more than one thread from
accessing shared state.
Progress and bou nded waiting are liveness properties. If a lock is FREE, some thread must
be able to acquire it. Further, any particular thread that wants to acquire the lock must
eventually succeed in doing so.
If these definitions sound stilted, it is because we have carefully crafted them to avoid
```

#### Chunk 5

- Chunk ID: `bdb778584564720d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `3.02342 rerank_score`

```text
This implementation does provide the mutual exclusion property we need from locks. Some
uniprocessor kernels use this simple approach, but it does not suffice as a general
implementation for locks. If the code sequence the lock protects runs for a long time,
interrupts will be disabled for that long. This will prevent other threads from running, and it
will make the system unresponsive to handling user inputs or other real-time tasks.
Furthermore, although this approach can work in the kernel where all code is (presumably)
carefully crafted and trusted to release the lock quickly, we cannot let untrusted user-level
code run with interrupts turned off since a malicious or buggy program could then monopolize
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
```

### Method B

- Retrieval latency: 0.258s
- Generation latency: 9.574s

**Answer:**

A **lock** answers:

> “Who is allowed to access this shared state right now?”

A **condition variable** answers:

> “Can I wait until this shared state reaches a state I need?”

So they solve different problems.

Example: bounded buffer / queue.

```c
lock(mutex);

while (queue_is_empty()) {
    wait(not_empty, mutex);
}

item = remove_from_queue();

unlock(mutex);
```

The lock gives mutual exclusion while checking or modifying the queue.

But if the queue is empty, mutual exclusion alone does not help. The thread has two bad options without a condition variable:

1. **Keep holding the lock and wait**  
   Then no producer can acquire the lock to put something in the queue. Deadlock-like situation.

2. **Release the lock and repeatedly check**  
   This is busy waiting / polling, wasting CPU and still tricky to get right.

A condition variable lets the thread say:

> “I cannot continue until `queue_is_empty()` becomes false, so put me to sleep and release the lock atomically.”

Later, a producer does:

```c
lock(mutex);

add_to_queue(item);
signal(not_empty);

unlock(mutex);
```

The condition variable wakes a waiting thread.

So:

- **Lock**: protects shared state from concurrent access.
- **Condition variable**: lets threads sleep until some condition on that shared state may have changed.
- They are used together because the condition must be checked while holding the lock.

That is also why you usually write:

```c
while (!condition) {
    wait(cv, lock);
}
```

not just `if`, because after waking up, the condition may no longer be true.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `842bfa77f8646f56`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `0.581047 vector_distance`

```text
mutual exclusion when accessing shared state.
5.7.6 Implementing Condition Variables
We can implement condition variables using a similar approach to the one used to implement
locks, with one simplification: since the lock is held whenever the wait, signal, or
broadcast is called, we already have mutually exclusive access to the condition wait queue.
As with locks, care is needed to prevent a waiting thread from being put back on the ready
list until it has completed its context switch; we can accomplish this by acquiring the
scheduler spinlock before we release the monitor lock. Another thread may acquire the
monitor lock and start to signal the waiting thread, bu t it will not be able to complete the
signal until the scheduler lock is released immediately after the context switch.
```

#### Chunk 2

- Chunk ID: `829dc10a227f3564`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `97`
- Score: `0.587602 vector_distance`

```text
Discussion. Condition variables have been carefully designed to work in tandem with locks
and shared state. The precise definition of condition variables includes three properties
worth additional comment:
A condition variable is memoryless.
The condition variable, itself, has no internal state other than a queue of waiting threads.
Condition variables do n ot need their own state because they are always used inside
shared obj ects that have their own state.
If no threads are currently on the condition variable’s waiting list, a signal or
broadcast has no effect. No thread calls wait unless it holds the lock, checks the state
variables, and finds that it needs to wait. Thus, the condition variable has no “memory”
```

#### Chunk 3

- Chunk ID: `3802725647de0b9c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `98`
- Score: `0.6072 vector_distance`

```text
wait(&lock); 
    } 
    ...
and not:
    ... 
    if (predicateOnStateVariables(...)) { 
        wait(&lock); 
    } 
    ...
There are two fundamental reasons why condition variables impose this requirement: to
simplify the implementation and to improve modularity.
Simplifying the implementation. When a waiting thread is re-enabled, it may not run
immediately. Other threads may access the shared state before it runs, and the desired
predicate on the shared state may no longer hold when wait finally does return.
```

#### Chunk 4

- Chunk ID: `31adea97e6dd91ae`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `0.616669 vector_distance`

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

- Chunk ID: `259c96c1742883cf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `85`
- Score: `0.720503 vector_distance`

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

### Method C

- Retrieval latency: 0.781s
- Generation latency: 6.860s

**Answer:**

A lock guarantees **mutual exclusion**: only one thread at a time can access some shared state.

But a lock does **not** help a thread wait efficiently until the shared state has the right value.

That is what a **condition variable** is for.

Example: bounded buffer

```c
lock.acquire();

while (buffer.isEmpty()) {
    notEmpty.wait(lock);
}

item = buffer.remove();

lock.release();
```

Here:

- The **lock** protects the buffer from simultaneous access.
- The **condition variable** `notEmpty` lets a thread sleep until the buffer becomes non-empty.

Without a condition variable, a thread might do something like:

```c
lock.acquire();
while (buffer.isEmpty()) {
    lock.release();
    lock.acquire();
}
```

That is wasteful busy waiting, and it is easy to get wrong.

A condition variable solves this by doing three things safely:

1. Release the lock.
2. Put the thread to sleep.
3. Reacquire the lock when the thread wakes up.

So the short answer is:

> Locks protect shared state.  
> Condition variables let threads wait for shared state to change.  

They are usually used together: the lock gives mutual exclusion, and the condition variable gives efficient waiting and notification.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `842bfa77f8646f56`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `n/a `

```text
mutual exclusion when accessing shared state.
5.7.6 Implementing Condition Variables
We can implement condition variables using a similar approach to the one used to implement
locks, with one simplification: since the lock is held whenever the wait, signal, or
broadcast is called, we already have mutually exclusive access to the condition wait queue.
As with locks, care is needed to prevent a waiting thread from being put back on the ready
list until it has completed its context switch; we can accomplish this by acquiring the
scheduler spinlock before we release the monitor lock. Another thread may acquire the
monitor lock and start to signal the waiting thread, bu t it will not be able to complete the
signal until the scheduler lock is released immediately after the context switch.
```

#### Chunk 2

- Chunk ID: `259c96c1742883cf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `85`
- Score: `n/a `

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

- Chunk ID: `31adea97e6dd91ae`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `n/a `

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

#### Chunk 4

- Chunk ID: `8fa975fc78a3daa7`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `128`
- Score: `n/a `

```text
Now that we have described locks and condition variables and shown how to use them in
shared obj ects, we turn to how to implement these important building blocks.
Recall from Chapter 4 that threads can be implemented in the kernel or at user level. We start
by describing how to implement synchronization for kernel threads; at the end of this section
we discuss the changes needed to support these abstractions for user-level threads.
Both locks and condition variables have state. For locks, this is the state of the lock (FREE or
BUSY) and a queue of zero or more threads waiting for the lock to become FREE. For
condition variables, the state is the queue of threads waiting to be signaled. Either way, the
challenge is to atomically modify those data structures.
```

#### Chunk 5

- Chunk ID: `bdb778584564720d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `n/a `

```text
This implementation does provide the mutual exclusion property we need from locks. Some
uniprocessor kernels use this simple approach, but it does not suffice as a general
implementation for locks. If the code sequence the lock protects runs for a long time,
interrupts will be disabled for that long. This will prevent other threads from running, and it
will make the system unresponsive to handling user inputs or other real-time tasks.
Furthermore, although this approach can work in the kernel where all code is (presumably)
carefully crafted and trusted to release the lock quickly, we cannot let untrusted user-level
code run with interrupts turned off since a malicious or buggy program could then monopolize
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
```

## q11

**Question:** Why is it incorrect to replace every condition-variable wait with a simple loop that repeatedly checks the condition until it becomes true?

### Method A

- Retrieval latency: 0.797s
- Generation latency: 14.601s

**Answer:**

Because a condition-variable `wait` does **more** than just “check later”.

A correct condition-variable wait typically does this atomically:

```c
while (!condition) {
    cv.wait(lock);   // releases lock, sleeps, then reacquires lock before returning
}
```

If you replace it with:

```c
while (!condition) {
    // just keep checking
}
```

that is incorrect for two main reasons.

### 1. If you hold the lock, no one can change the condition

Usually the condition depends on shared state protected by a lock:

```c
lock.acquire();

while (!ready) {
    // spin
}

lock.release();
```

But if this thread keeps the lock while spinning, then the thread that needs to set `ready = true` cannot acquire the lock. So the condition may never become true.

That can cause deadlock/livelock.

### 2. If you do not hold the lock, the check is unsafe

If you repeatedly check the condition without the lock, then you are reading shared state unsafely. Another thread may modify it concurrently, causing race conditions or visibility problems.

### 3. It wastes CPU

A condition-variable wait puts the thread to sleep until another thread signals that the condition *might* have changed.

A simple loop is busy waiting:

```c
while (!condition) {
    // burn CPU doing nothing useful
}
```

That wastes processor time, especially if the condition may take a long time to become true.

### Key idea

A condition-variable wait is useful because it:

1. checks the condition while holding the lock,
2. releases the lock atomically when waiting,
3. sleeps without wasting CPU,
4. reacquires the lock before continuing.

So the correct pattern is:

```c
lock.acquire();

while (!condition) {
    cv.wait(lock);
}

lock.release();
```

Not a simple polling loop.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6775bdea4ddce8a1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `106`
- Score: `n/a `

```text
designers may use different numbers of condition variables for a given class. Like many
other design decisions, this is a matter of programmer taste, judgment, and experience.
Asking “When can this method wait?” will help you identify what is for you a natural
way of thinking about a shared obj ect’s condition variables.
4. Add loops to wait using the condition variables. Add a while(...) {cv.wait()} loop into
each method that you identified as potentially needing to wait before returning.
Remember that every call to wait must be enclosed in a while loop that tests an
appropriate predicate. Modern implementations almost invariably provide Mesa
semantics and often allow for spurious wakeups (i.e., a thread can return from
```

#### Chunk 2

- Chunk ID: `9469896e883a1df8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `111`
- Score: `n/a `

```text
Many libraries enforce this rule — that you cannot call condition variable methods
unless you hold the corresponding lock. However, some run-time systems and libraries
allow sloppiness, so take care.
5. Always wait in a while() loop
The pattern should always be:
 while (predicateOnStateVariables(...)) { 
     condition->wait(&lock); 
 }
and never:
 ... 
 if (predicateOnStateVariables(...)) { 
     wait(&lock); 
 } 
 ...
Here, predicateOnStateVariables(...) is code that looks at the state variables of the
current object to decide if the thread should proceed.
You may be tempted to guard a wait call with an if conditional rather than a while loop
when you can deduce from the global structure of the program that, despite Mesa
```

#### Chunk 3

- Chunk ID: `d13e60da0b3b6f07`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `99`
- Score: `n/a `

```text
applications programmers always assume that they can occur and so
always wait in a loop.
(From https://docs.oracle.com/javase/8/docs/api/)
Improving modularity. Waiting in a loop t hat checks the shared state makes shared
objects’ code more modular because we can reason about when the thread will continue
by looking only at the wait loop. I n particular, we do not need to examine the rest of the
shared obj ect’s code to understand where and why calls to signal and broadcast are
made to know the post-condition for the wait loop. F or example, in Figure 5.7, we
know the assert call will never fail without having to look at any other code.
Not only does waiting in a loop s implify writing and reasoning about the code that
```

#### Chunk 4

- Chunk ID: `0aa718802f424580`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `99`
- Score: `n/a `

```text
Not only does waiting in a loop s implify writing and reasoning about the code that
waits, it simplifies writing and reasoning about the code that signals or broadcasts.
Signaling at the wrong time will never cause a waiting thread to proceed when it should
not. Signal and broadcast can be regarded as hints that it might be a good t ime to
proceed; if the hints prove to be wrong, no damage is done. You can always convert a
signal to a broadcast, or add any number of signal or broadcast calls, without
changing the semantics of a shared object. Avoiding extra signal and broadcast calls
may matter for performance, but not for correctness.
Bottom line: Given the range of possible implementations and the modularity benefits,
```

#### Chunk 5

- Chunk ID: `3802725647de0b9c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `98`
- Score: `n/a `

```text
wait(&lock); 
    } 
    ...
and not:
    ... 
    if (predicateOnStateVariables(...)) { 
        wait(&lock); 
    } 
    ...
There are two fundamental reasons why condition variables impose this requirement: to
simplify the implementation and to improve modularity.
Simplifying the implementation. When a waiting thread is re-enabled, it may not run
immediately. Other threads may access the shared state before it runs, and the desired
predicate on the shared state may no longer hold when wait finally does return.
```

### Method B

- Retrieval latency: 0.949s
- Generation latency: 9.289s

**Answer:**

Because a simple “check in a loop” is **polling**, not proper synchronization.

A condition-variable wait does two important things that a plain loop does not:

1. **It sleeps efficiently**
   ```c
   while (!condition) {
       cv.wait(lock);
   }
   ```
   The thread is suspended and does not waste CPU time.

   A simple loop like:
   ```c
   while (!condition) {
       // keep checking
   }
   ```
   can burn an entire CPU core doing nothing useful.

2. **It atomically releases the lock and waits**
   A condition variable wait releases the associated lock and puts the thread to sleep as one atomic operation.

   That matters because usually the condition depends on shared state protected by a lock.

   If the thread keeps checking while holding the lock, then the other thread may never be able to acquire the lock to make the condition true:

   ```c
   lock.acquire();
   while (!ready) {
       // still holding lock
   }
   lock.release();
   ```

   This can deadlock or block progress, because the producer cannot do:

   ```c
   lock.acquire();
   ready = true;
   lock.release();
   ```

If you try to fix that by repeatedly unlocking, sleeping/yielding, and checking again, you get a polling loop:

```c
while (!ready) {
    lock.release();
    thread_sleep(100);
    lock.acquire();
}
```

That is still bad because it adds unnecessary delay, wastes scheduling effort, and may respond much later than needed.

So the correct pattern is:

```c
lock.acquire();

while (!ready) {
    cv.wait(&lock);
}

lock.release();
```

Use a condition variable when a thread is waiting for shared state to change. A repeated manual check is either inefficient, incorrect, or both.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `a80c93f30ee0494a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `112`
- Score: `3.77267 rerank_score`

```text
The correct way to wait for a condition to become true is to wait on a condition
variable.
In general, thread_sleep is appropriate only when there is a particular real-time
moment when you want to perform some action, such as a timeout for when to declare a
remote server non-responsive. If you catch yourself writing while(testOnObjectState())
{thread_sleep();}, treat this as a red flag that you are probably making a mistake.
Similarly, if a thread must wait for an object’s state to change, it should wait on a
condition variable, and not just call thread_yield. Use thread_yield only when a low-
priority thread that can still make progress wants to let a higher-priority thread to run.
5.5.3 Three Pitfalls
```

#### Chunk 2

- Chunk ID: `8b6103e31759a96d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `99`
- Score: `1.58294 rerank_score`

```text
predicate on the state is no longe r true, it is possible that the desired predicate on the
state was never true. For example, the Java definition of condition variables allows for
“spurious wakeups”:
When waiting upon a Condition, a “spurious wakeup” is permitted to
occur, in general, as a concession to the underlying platform semantics.
This has little practical impact on most application programs as a
Condition should always be waited upon in a loop, testing the state
predicate that is being waited for. An implementation is free to remove
the possibility of spurious wakeups but it is recommended that
applications programmers always assume that they can occur and so
always wait in a loop.
(From https://docs.oracle.com/javase/8/docs/api/)
```

#### Chunk 3

- Chunk ID: `85a07a67e5b4d6a2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `112`
- Score: `1.44645 rerank_score`

```text
Using if breaks portability. Some implementations of condition variables allow
spurious wakeups, while others do not. For example, implementations of condition
variables in both Java and the POSIX pthreads library are allowed to return from
wait even though no thread called signal or broadcast.
6. (Almost) never use thread_sleep.
Many thread libraries have a thread_sleep function that suspends execution of the
calling thread for some period of  wall clock time. Once that time passes, the thread is
returned to the scheduler’s ready queue and can run again.
Never use thread_sleep to have one thread wait for another thread to perform a task.
The correct way to wait for a condition to become true is to wait on a condition
variable.
```

#### Chunk 4

- Chunk ID: `2eecda95599dc874`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `95`
- Score: `1.30899 rerank_score`

```text
instead each took just over half a second. Fortunately, the performance was so poor that it was easy to track down the
problem: layers passed work to each other through bounded queues much like TSQueue, but the queue remove method was
implemented as a polling loop with a 100 ms delay. With five such layers of processing, the server became unusable.
Fortunately, the fix was simple: use condition variables instead.
5.4.1 Condition Variable Definition
A condition variable is a synchronization object that lets a thread efficiently wait for a
change to shared state that is protected by a lock. A condition variable has three methods:
CV::wait(Lock *lock). This call atomically releases the lock and suspends execution
```

#### Chunk 5

- Chunk ID: `9469896e883a1df8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `111`
- Score: `1.24648 rerank_score`

```text
Many libraries enforce this rule — that you cannot call condition variable methods
unless you hold the corresponding lock. However, some run-time systems and libraries
allow sloppiness, so take care.
5. Always wait in a while() loop
The pattern should always be:
 while (predicateOnStateVariables(...)) { 
     condition->wait(&lock); 
 }
and never:
 ... 
 if (predicateOnStateVariables(...)) { 
     wait(&lock); 
 } 
 ...
Here, predicateOnStateVariables(...) is code that looks at the state variables of the
current object to decide if the thread should proceed.
You may be tempted to guard a wait call with an if conditional rather than a while loop
when you can deduce from the global structure of the program that, despite Mesa
```

### Method C

- Retrieval latency: 0.193s
- Generation latency: 11.105s

**Answer:**

Because a condition-variable `wait` does **two essential things** that a simple polling loop does not:

1. **It releases the lock while waiting**
2. **It puts the thread to sleep until someone signals/broadcasts**

A naive loop like:

```c
while (!condition) {
    // keep checking
}
```

is incorrect or bad depending on where the lock is.

### Case 1: The thread keeps the lock

```c
lock();
while (!condition) {
    // spin
}
unlock();
```

This can deadlock or block progress.

The thread waiting for `condition` is holding the lock, so no other thread can acquire the lock to change the shared state and make `condition` true.

So the waiting thread may wait forever.

### Case 2: The thread releases and reacquires the lock manually

```c
while (!condition) {
    unlock();
    lock();
}
```

This avoids the deadlock, but it is still wrong/poor design because it causes **busy waiting**: the thread repeatedly consumes CPU just to check whether something changed.

A condition variable instead lets the thread sleep:

```c
while (!condition) {
    cv.wait(lock);
}
```

Here, `wait` atomically releases the lock and suspends the thread. When it wakes up, it reacquires the lock and rechecks the condition.

So the correct pattern is not:

```c
while (!condition) {
    // just keep checking
}
```

but:

```c
while (!condition) {
    wait(cv, lock);
}
```

The loop is still needed because after waking up, the condition might no longer be true, or the wakeup might be spurious. But the waiting itself must be done with the condition variable, not by repeatedly polling.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6775bdea4ddce8a1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `106`
- Score: `0.733708 vector_distance`

```text
designers may use different numbers of condition variables for a given class. Like many
other design decisions, this is a matter of programmer taste, judgment, and experience.
Asking “When can this method wait?” will help you identify what is for you a natural
way of thinking about a shared obj ect’s condition variables.
4. Add loops to wait using the condition variables. Add a while(...) {cv.wait()} loop into
each method that you identified as potentially needing to wait before returning.
Remember that every call to wait must be enclosed in a while loop that tests an
appropriate predicate. Modern implementations almost invariably provide Mesa
semantics and often allow for spurious wakeups (i.e., a thread can return from
```

#### Chunk 2

- Chunk ID: `3802725647de0b9c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `98`
- Score: `0.756305 vector_distance`

```text
wait(&lock); 
    } 
    ...
and not:
    ... 
    if (predicateOnStateVariables(...)) { 
        wait(&lock); 
    } 
    ...
There are two fundamental reasons why condition variables impose this requirement: to
simplify the implementation and to improve modularity.
Simplifying the implementation. When a waiting thread is re-enabled, it may not run
immediately. Other threads may access the shared state before it runs, and the desired
predicate on the shared state may no longer hold when wait finally does return.
```

#### Chunk 3

- Chunk ID: `d37f2bc4847022b2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `98`
- Score: `0.76669 vector_distance`

```text
making debugging very difficult. See the sidebar on Mesa vs. Hoare semantics for a
discussion of the history behind this property.
WARNING: The points above  have an important implication for programmers: wait must
always be called from within a loop.
Because wait releases the lock, and because there is no guarantee of atomicity between
signal or broadcast and the return of a call to wait, there is no guarantee that the checked-
for state still holds. Therefore, a waiting thread must always wait in a loop, r echecking the
state until the desired predicate holds. Thus, the design pattern is:
    ... 
    while (predicateOnStateVariables(...)) { 
      wait(&lock); 
    } 
    ...
and not:
    ... 
    if (predicateOnStateVariables(...)) { 
        wait(&lock); 
    } 
    ...
```

#### Chunk 4

- Chunk ID: `9469896e883a1df8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `111`
- Score: `0.776792 vector_distance`

```text
Many libraries enforce this rule — that you cannot call condition variable methods
unless you hold the corresponding lock. However, some run-time systems and libraries
allow sloppiness, so take care.
5. Always wait in a while() loop
The pattern should always be:
 while (predicateOnStateVariables(...)) { 
     condition->wait(&lock); 
 }
and never:
 ... 
 if (predicateOnStateVariables(...)) { 
     wait(&lock); 
 } 
 ...
Here, predicateOnStateVariables(...) is code that looks at the state variables of the
current object to decide if the thread should proceed.
You may be tempted to guard a wait call with an if conditional rather than a while loop
when you can deduce from the global structure of the program that, despite Mesa
```

#### Chunk 5

- Chunk ID: `d13e60da0b3b6f07`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `99`
- Score: `0.809148 vector_distance`

```text
applications programmers always assume that they can occur and so
always wait in a loop.
(From https://docs.oracle.com/javase/8/docs/api/)
Improving modularity. Waiting in a loop t hat checks the shared state makes shared
objects’ code more modular because we can reason about when the thread will continue
by looking only at the wait loop. I n particular, we do not need to examine the rest of the
shared obj ect’s code to understand where and why calls to signal and broadcast are
made to know the post-condition for the wait loop. F or example, in Figure 5.7, we
know the assert call will never fail without having to look at any other code.
Not only does waiting in a loop s implify writing and reasoning about the code that
```

## q12

**Question:** If a thread signals a condition variable, shouldn’t the waiting thread run immediately?

### Method A

- Retrieval latency: 0.200s
- Generation latency: 7.597s

**Answer:**

Not necessarily.

In most real systems, condition variables use **Mesa semantics**:

- `signal()` wakes one waiting thread, meaning it becomes **eligible to run**.
- But it does **not immediately run**.
- The signaling thread usually keeps running until it releases the lock or gets scheduled out.
- The awakened thread must then reacquire the lock before returning from `wait()`.

So the flow is usually:

```text
T1 waits on condition variable
T2 acquires lock
T2 changes shared state
T2 signals condition variable
T2 continues running
T2 releases lock
T1 eventually wakes up and reacquires lock
T1 rechecks condition
```

That is why condition-variable waits are normally written with a `while`, not an `if`:

```c
lock.acquire();

while (!condition) {
    cv.wait(lock);
}

/* condition is true here */

lock.release();
```

Because by the time the waiting thread actually runs, another thread may have changed the shared state again.

There is another model, called **Hoare semantics**, where the signaling thread immediately hands control and the lock to the waiting thread. Under that model, the waiting thread really does run immediately. But most practical systems, like POSIX pthreads and Java-style monitors, use Mesa-style behavior instead.

So: **`signal()` wakes a waiter, but it does not guarantee the waiter runs immediately.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b8ab35c08595a8d4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `97`
- Score: `0.653582 vector_distance`

```text
variables, and finds that it needs to wait. Thus, the condition variable has no “memory”
of earlier calls to signal or broadcast. After signal is called, if sometime later
another thread calls wait, it will block until the next signal (or broadcast) is called,
regardless of how many times signal has been called in the past.
CV::wait atomically releases the lock.
A thread always calls wait while holding a lock. The call to wait atomically releases
the lock and puts the thread on the condition variable’s waiting list. Atomicity ensures
that there is no separation between checking the shared obj ect’s state, deciding to wait,
adding the waiting thread to the condition variable’s queue, and releasing the lock so
that some other thread can access the shared obj ect.
```

#### Chunk 2

- Chunk ID: `6e33aaa1e692624d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `143`
- Score: `0.675858 vector_distance`

```text
By contrast, consider what happens with a semaphore. What happens if a thread calls V and
no one is waiting? The value of the semaphore is incremented. W hat happens if a thread later
calls P? The value of the semaphore is decremented, and the thread continues.
In other words, P and V are commutative. The result is the same no matter what order they
occur. Condition variables are not commutative: wait does not return until the next signal.
This is why condition variables must be accessed while holding a lock — code using a
condition variable needs to access shared state variables to do i ts job.
With condition variables, if a thread calls signal a thousand times, when no one is waiting,
the next wait will still go to sleep. With the above  code, the next thousand threads that
```

#### Chunk 3

- Chunk ID: `7098016929665f99`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `97`
- Score: `0.682071 vector_distance`

```text
adding the waiting thread to the condition variable’s queue, and releasing the lock so
that some other thread can access the shared obj ect.
If threads released the lock before calling wait, they could miss a signal or broadcast
and wait forever. Consider the case where thread T1 checks an object’s state and
decides to wait, so it releases the lock in anticipation of putting itself on the condition
variable’s waiting list. At that precise moment, T2 preempts T1. T2 acquires the lock,
changes the object’s state to what T1 wants, and calls signal, but the waiting list is
empty so the call to signal has no effect. Finally, T1 runs again, puts itself on the
waiting list, and suspends execution. The lack of atomicity means that T1 missed the
signal and is now waiting, potentially forever.
```

#### Chunk 4

- Chunk ID: `dcb0f0a6b565bc3d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `100`
- Score: `0.688374 vector_distance`

```text
C.A.R. “Tony” Hoare proposed a different definition for condition variables. Under Hoare semantics, when a thread calls
signal, execution of the signaling thread is suspended, the ownership of the lock is immediately transferred to one of the
waiting threads, and execution of that thread is immediately resumed. Later, when the resumed thread releases the lock,
ownership of the lock reverts to the signaling thread, whose execution continues.
Under Hoare semantics, signaling is atomic with the resumption of a waiting thread, and a signaled thread may assume that
the state has not changed since the signal that woke it up was issued. Under Mesa semantics, waiting is always done in a
```

#### Chunk 5

- Chunk ID: `85a07a67e5b4d6a2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `112`
- Score: `0.712341 vector_distance`

```text
Using if breaks portability. Some implementations of condition variables allow
spurious wakeups, while others do not. For example, implementations of condition
variables in both Java and the POSIX pthreads library are allowed to return from
wait even though no thread called signal or broadcast.
6. (Almost) never use thread_sleep.
Many thread libraries have a thread_sleep function that suspends execution of the
calling thread for some period of  wall clock time. Once that time passes, the thread is
returned to the scheduler’s ready queue and can run again.
Never use thread_sleep to have one thread wait for another thread to perform a task.
The correct way to wait for a condition to become true is to wait on a condition
variable.
```

### Method B

- Retrieval latency: 0.696s
- Generation latency: 6.730s

**Answer:**

Usually, **no** — not immediately.

For most condition variables used in real systems, the semantics are **Mesa semantics**:

- `signal()` wakes one waiting thread by making it **ready/runnable**.
- But the signaling thread usually **continues running** and still holds the lock.
- The waiting thread can only continue after it is scheduled **and** re-acquires the monitor/condition lock.
- By then, another thread may have changed the shared state again.

That is why condition-variable waits are written like this:

```c
while (!condition) {
    wait(&lock);
}
```

not:

```c
if (!condition) {
    wait(&lock);
}
```

Because being signaled does **not** guarantee the condition is still true when the waiting thread resumes.

There is another model, called **Hoare semantics**, where `signal()` immediately transfers control and the lock to the waiting thread. But most practical condition-variable implementations use **Mesa semantics**, not Hoare semantics.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5d0ac831d2f2c780`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `138`
- Score: `7.5065 rerank_score`

```text
} 
 } 
Figure 5.18: Pseudo-code for implementing a condition variable. suspend and makeReady are defined in Figure 5.17.
Figure 5.18 shows an implementation with Mesa semantics — w hen we signal a waiting
thread, that thread becomes READY, but it may not run immediately and must still re-acquire
the monitor lock. It is possible for another thread to acquire the monitor lock first and to
change the state guarded by the lock before the waiting thread returns from CV::wait.
5.7.7 Implementing Application-level Synchronization
The preceding discussion focused on implementing locks and condition variables for kernel
threads. In that case, everything (code, shared state, lock data structures, thread control
```

#### Chunk 2

- Chunk ID: `3802725647de0b9c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `98`
- Score: `7.22219 rerank_score`

```text
wait(&lock); 
    } 
    ...
and not:
    ... 
    if (predicateOnStateVariables(...)) { 
        wait(&lock); 
    } 
    ...
There are two fundamental reasons why condition variables impose this requirement: to
simplify the implementation and to improve modularity.
Simplifying the implementation. When a waiting thread is re-enabled, it may not run
immediately. Other threads may access the shared state before it runs, and the desired
predicate on the shared state may no longer hold when wait finally does return.
```

#### Chunk 3

- Chunk ID: `7098016929665f99`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `97`
- Score: `6.34622 rerank_score`

```text
adding the waiting thread to the condition variable’s queue, and releasing the lock so
that some other thread can access the shared obj ect.
If threads released the lock before calling wait, they could miss a signal or broadcast
and wait forever. Consider the case where thread T1 checks an object’s state and
decides to wait, so it releases the lock in anticipation of putting itself on the condition
variable’s waiting list. At that precise moment, T2 preempts T1. T2 acquires the lock,
changes the object’s state to what T1 wants, and calls signal, but the waiting list is
empty so the call to signal has no effect. Finally, T1 runs again, puts itself on the
waiting list, and suspends execution. The lack of atomicity means that T1 missed the
signal and is now waiting, potentially forever.
```

#### Chunk 4

- Chunk ID: `dcb0f0a6b565bc3d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `100`
- Score: `6.31733 rerank_score`

```text
C.A.R. “Tony” Hoare proposed a different definition for condition variables. Under Hoare semantics, when a thread calls
signal, execution of the signaling thread is suspended, the ownership of the lock is immediately transferred to one of the
waiting threads, and execution of that thread is immediately resumed. Later, when the resumed thread releases the lock,
ownership of the lock reverts to the signaling thread, whose execution continues.
Under Hoare semantics, signaling is atomic with the resumption of a waiting thread, and a signaled thread may assume that
the state has not changed since the signal that woke it up was issued. Under Mesa semantics, waiting is always done in a
```

#### Chunk 5

- Chunk ID: `6b5933646f6c2f1f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `142`
- Score: `6.15357 rerank_score`

```text
void CV::signal() { 
        semaphore.V(); 
    }
ANSWER: No. Condition variables are stateless, while semaphores have state. We can
illustrate this difference with a counterexample.
What happens if a thread calls signal and no one is waiting? Nothing. What happens if
another thread later calls wait? The thread waits.
```

### Method C

- Retrieval latency: 1.174s
- Generation latency: 6.984s

**Answer:**

Not necessarily.

In most modern systems, condition variables use **Mesa semantics**:

- `signal()` wakes one waiting thread by moving it to the **ready/runnable queue**.
- The signaling thread usually **keeps running** until it releases the lock or is preempted.
- The woken thread runs **later**, when the scheduler chooses it.
- Before continuing, the woken thread must usually **re-acquire the lock**.

So the waiting thread does **not** automatically run immediately.

That is why condition variable waits are usually written like this:

```c
lock(m);

while (!condition) {
    wait(cv, m);
}

// condition is true here
unlock(m);
```

The `while` matters because by the time the waiting thread actually runs, the condition may no longer be true, or it may have woken spuriously.

There is an alternative model called **Hoare semantics**, where `signal()` immediately transfers control and the lock to the waiting thread. But that is not how most modern condition variables work, including POSIX pthreads and Java-style monitors.

So the short answer is:

> `signal()` makes a waiting thread eligible to run; it does not guarantee that it runs immediately.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6e33aaa1e692624d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `143`
- Score: `n/a `

```text
By contrast, consider what happens with a semaphore. What happens if a thread calls V and
no one is waiting? The value of the semaphore is incremented. W hat happens if a thread later
calls P? The value of the semaphore is decremented, and the thread continues.
In other words, P and V are commutative. The result is the same no matter what order they
occur. Condition variables are not commutative: wait does not return until the next signal.
This is why condition variables must be accessed while holding a lock — code using a
condition variable needs to access shared state variables to do i ts job.
With condition variables, if a thread calls signal a thousand times, when no one is waiting,
the next wait will still go to sleep. With the above  code, the next thousand threads that
```

#### Chunk 2

- Chunk ID: `7098016929665f99`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `97`
- Score: `n/a `

```text
adding the waiting thread to the condition variable’s queue, and releasing the lock so
that some other thread can access the shared obj ect.
If threads released the lock before calling wait, they could miss a signal or broadcast
and wait forever. Consider the case where thread T1 checks an object’s state and
decides to wait, so it releases the lock in anticipation of putting itself on the condition
variable’s waiting list. At that precise moment, T2 preempts T1. T2 acquires the lock,
changes the object’s state to what T1 wants, and calls signal, but the waiting list is
empty so the call to signal has no effect. Finally, T1 runs again, puts itself on the
waiting list, and suspends execution. The lack of atomicity means that T1 missed the
signal and is now waiting, potentially forever.
```

#### Chunk 3

- Chunk ID: `dcb0f0a6b565bc3d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `100`
- Score: `n/a `

```text
C.A.R. “Tony” Hoare proposed a different definition for condition variables. Under Hoare semantics, when a thread calls
signal, execution of the signaling thread is suspended, the ownership of the lock is immediately transferred to one of the
waiting threads, and execution of that thread is immediately resumed. Later, when the resumed thread releases the lock,
ownership of the lock reverts to the signaling thread, whose execution continues.
Under Hoare semantics, signaling is atomic with the resumption of a waiting thread, and a signaled thread may assume that
the state has not changed since the signal that woke it up was issued. Under Mesa semantics, waiting is always done in a
```

#### Chunk 4

- Chunk ID: `85a07a67e5b4d6a2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `112`
- Score: `n/a `

```text
Using if breaks portability. Some implementations of condition variables allow
spurious wakeups, while others do not. For example, implementations of condition
variables in both Java and the POSIX pthreads library are allowed to return from
wait even though no thread called signal or broadcast.
6. (Almost) never use thread_sleep.
Many thread libraries have a thread_sleep function that suspends execution of the
calling thread for some period of  wall clock time. Once that time passes, the thread is
returned to the scheduler’s ready queue and can run again.
Never use thread_sleep to have one thread wait for another thread to perform a task.
The correct way to wait for a condition to become true is to wait on a condition
variable.
```

#### Chunk 5

- Chunk ID: `67e51d9c2a90ea70`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `100`
- Score: `n/a `

```text
In modern condition variables, signal or broadcast calls take waiting threads from a condition variable’s waiting list and put
them on the ready list. Later, when these threads are scheduled, they may block for some time while they try to re-acquire
the lock. Thus, modern condition variables implement what are often called Mesa Semantics (for Mesa, an early
programming language at Xerox PARC that implemented these semantics). Despite the name, Mesa was not the first system
to use “Mesa” semantics; Brinch Hansen had proposed their use five years earlier. However, PARC was the first to use
Mesa semantics extensively in a very large operating system, and the name stuck.
C.A.R. “Tony” Hoare proposed a different definition for condition variables. Under Hoare semantics, when a thread calls
```

## q13

**Question:** If deadlock means two threads are stuck waiting forever, how is that different from starvation?

### Method A

- Retrieval latency: 0.272s
- Generation latency: 7.135s

**Answer:**

Deadlock and starvation both mean “some thread may not make progress,” but the reason is different.

**Deadlock**:  
A set of threads are stuck because they are waiting on each other in a cycle.

Example:

- Thread A holds `lock1` and waits for `lock2`
- Thread B holds `lock2` and waits for `lock1`

Neither can continue, because each needs the other to release something. That is a **cycle of waiting**.

**Starvation**:  
A thread waits for a very long time, possibly forever, but not because of a waiting cycle. Instead, other threads keep getting priority or keep acquiring the resource first.

Example:

- A writer is waiting to write.
- Readers keep arriving and are allowed to read before the writer.
- The writer never gets a turn.

The writer is starving, but the active readers are not waiting for the writer, so there is no deadlock cycle.

So:

> **Deadlock = threads are waiting on each other.**  
> **Starvation = a thread keeps being denied progress, but not necessarily because of a cycle.**

Deadlock implies starvation, because deadlocked threads starve forever.  
But starvation does **not** necessarily imply deadlock.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1ce2ce29b35917ac`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `0.501918 vector_distance`

```text
progress for an indefinite period of  time. Deadlock is a form of starvation but with the
stronger condition: a group of threads forms a cycle where none of the threads make progress
because each thread is waiting for some other thread in the cycle to take action. Thus,
deadlock implies starvation (literally, for the dining philosophers), but starvation does not
imply deadlock.
For example, recall the readers/writers example discussed in Section 5.6.1 . A writer only
waits if a reader or writer is active. In the writers-preferred solution we gave, waiting
readers can starve if new writers arrive sufficiently frequently; likewise, waiting writers can
starve if there is an active reader, and new readers arrive and become active before the last
```

#### Chunk 2

- Chunk ID: `12ad4571a11bd814`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `0.616902 vector_distance`

```text
starve if there is an active reader, and new readers arrive and become active before the last
one completes. Note that such starvation would not be deadlock because there is no cycle.
The waiting readers are waiting on the active writers to finish, and the waiting writers are
waiting on the active readers to finish, but no active thread is waiting on a waiting reader or
writer.
Just because a system can suffer deadlock or starvation does not mean that it always will. A
system is subject to starvation if a thread could starve in some circumstances. A system is
subject to deadlock if a group of threads could deadlock in some circumstances. Here, the
circumstances that affect whether deadlock or starvation occurs could include a broad range
```

#### Chunk 3

- Chunk ID: `e4069986d30cb2eb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `0.651507 vector_distance`

```text
circumstances that affect whether deadlock or starvation occurs could include a broad range
of factors, such as: the choices made by the scheduler, the number of threads running, the
workload or sequence of requests processed by the system, which threads win races to
acquire locks, and which threads are enabled in what order when signals or broadcasts occur.
A system that is subject to starvation or deadlock may be live in many or most runs and starve
or deadlock only for particular workloads or “unlucky” interleavings. For example, in
mutually recursive locking, the deadlock only occurs if both threads obtain the outer locks at
about the same time. For the Dining Philosophers problem, philosophers may succeed in
```

#### Chunk 4

- Chunk ID: `b2ba74cf0365cf54`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `178`
- Score: `0.753903 vector_distance`

```text
A deadlock is a cycle of waiting among a set of threads, where each thread waits for some
other thread in the cycle to take some action.
Deadlock can occur in many different situations, but one of the simplest is mutually recursive
locking, shown in the code fragment below:
    // Thread A 
     
    lock1.acquire(); 
    lock2.acquire(); 
    lock2.release(); 
    lock1.release();
    // Thread B 
     
    lock2.acquire(); 
    lock1.acquire(); 
    lock1.release(); 
    lock2.release();
Suppos e two shared obj ects with mutual exclusion locks can call into each other while
holding their locks. Deadlock can occur when one thread holds the lock on the first object,
and another thread holds the lock on the second obj ect. If the first thread calls into the second
```

#### Chunk 5

- Chunk ID: `351cb2d32a30bc43`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `181`
- Score: `0.804423 vector_distance`

```text
approach, there can be a deadlock: each philosopher takes the chopstick on the left but can be
stuck waiting for the philosopher on the right to release the chopstick.
Note that mutually recursive locking is equivalent to Dining Philosophers with n = 2.
The rest of this section addresses the following questions:
Deadlock vs. Starvation. How does deadlock relate to the concepts of liveness and
starvation?
```

### Method B

- Retrieval latency: 0.876s
- Generation latency: 7.113s

**Answer:**

Deadlock and starvation can both mean “a thread waits forever,” but the reason is different.

**Deadlock**:  
A group of threads are stuck because they are waiting on each other in a cycle.

Example:

- Thread A holds lock 1 and waits for lock 2.
- Thread B holds lock 2 and waits for lock 1.

Neither can continue, so the whole group is permanently blocked.

**Starvation**:  
A thread waits forever because other threads keep getting the resource first, even though the system as a whole is still making progress.

Example:

- A writer is waiting to write.
- Readers keep arriving.
- The system keeps letting readers go first.
- The writer may never get a turn.

So:

| Concept | What happens? | Is the system still doing work? |
|---|---|---|
| **Deadlock** | Threads are waiting on each other in a cycle | Usually no, the involved threads are stuck |
| **Starvation** | One thread keeps being denied access | Yes, other threads may continue |

In short:

**Deadlock = circular waiting.**  
**Starvation = unfair waiting while others keep progressing.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `12ad4571a11bd814`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `n/a `

```text
starve if there is an active reader, and new readers arrive and become active before the last
one completes. Note that such starvation would not be deadlock because there is no cycle.
The waiting readers are waiting on the active writers to finish, and the waiting writers are
waiting on the active readers to finish, but no active thread is waiting on a waiting reader or
writer.
Just because a system can suffer deadlock or starvation does not mean that it always will. A
system is subject to starvation if a thread could starve in some circumstances. A system is
subject to deadlock if a group of threads could deadlock in some circumstances. Here, the
circumstances that affect whether deadlock or starvation occurs could include a broad range
```

#### Chunk 2

- Chunk ID: `e4069986d30cb2eb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `n/a `

```text
circumstances that affect whether deadlock or starvation occurs could include a broad range
of factors, such as: the choices made by the scheduler, the number of threads running, the
workload or sequence of requests processed by the system, which threads win races to
acquire locks, and which threads are enabled in what order when signals or broadcasts occur.
A system that is subject to starvation or deadlock may be live in many or most runs and starve
or deadlock only for particular workloads or “unlucky” interleavings. For example, in
mutually recursive locking, the deadlock only occurs if both threads obtain the outer locks at
about the same time. For the Dining Philosophers problem, philosophers may succeed in
```

#### Chunk 3

- Chunk ID: `c91b785046c70943`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `180`
- Score: `n/a `

```text
buffer1.get(); 
    buffer1.get();
If the buffers are almost full, both threads will need to wait for there to be room, and so
neither will be able to reach the point where they can pull data out of the other buffer to allow
the other thread to make progress.
Figure 6.14: An example of deadlock where three tractor-trailer trucks enter an intersection without first checking whether
they can clear the intersection.
Deadlocks also occur in real life. We encourage you to develop your intuition about
deadlocks by considering why deadlocks occur and how we might prevent them. For
example, if we lived in a world without stop signs, we might see the deadlock in Figure 6.14
more often.
```

#### Chunk 4

- Chunk ID: `eefededb630d9b06`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `186`
- Score: `n/a `

```text
three approaches:
1. Exploit or limit the behavior of the program. Often, we can change the behavior of a
program to prevent one of the four necessary conditions for deadlock, and thereby
eliminate the possibility of deadlock. In the above  example, we can eliminate deadlock
by changing the program to never wait for B while holding C.
2. Predict the future. If we can know what threads may or will do, t hen we can avoid
deadlock by having threads wait (e.g., thread 2 c an wait at step 2 above ) before they
would head into a possible deadlock.
3. Detect and recover. Another alternative is to allow threads to recover or “undo”
actions that take a system into a deadlock; in the above  example, when thread 2 finds
itself in deadlock, it can recover by reverting to an earlier state.
```

#### Chunk 5

- Chunk ID: `fa6d0436cbb03746`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `184`
- Score: `n/a `

```text
Figure 6.16: Graph representation of the state of a deadlocked Dining Philosophers system. Circles represent threads,
boxes represent resources, an arrow from a box/resource to a circle/thread represents an owned by relationship, and an
arrow from a circle/thread to a box/resource represents a waiting for relationship.
EXAMPLE: Show that the Dining Philosophers meet all four conditions for deadlock.
ANSWER: To see that all four conditions are met, obs erve that
1. Bounded resources. Each chopstick can be held by a single philosopher at a time.
2. No preemption. Once a philosopher picks up a chopstick, she does not release it until
she is done eating, even if that means no one will ever eat.
3. Wait while holding. When a philosopher needs to wait for a chopstick, she continues to
```

### Method C

- Retrieval latency: 0.429s
- Generation latency: 6.222s

**Answer:**

Deadlock and starvation both mean “some thread doesn’t make progress,” but the reason is different.

**Deadlock**:  
A group of threads are stuck in a **cycle of waiting**.

Example:

- Thread A holds `lock1` and waits for `lock2`
- Thread B holds `lock2` and waits for `lock1`

Neither can continue, because each needs the other to release something. So they are permanently stuck unless something external intervenes.

**Starvation**:  
A thread waits for a very long time, possibly forever, because other threads keep getting priority or access first — but there is **no waiting cycle**.

Example:

- A writer wants to write.
- Readers keep arriving and are allowed to read first.
- The writer keeps waiting indefinitely.

The system is still doing work — readers are progressing — but the writer is starved.

So the key difference is:

> **Deadlock = circular waiting.**  
> **Starvation = unfair or unlucky waiting without necessarily having a cycle.**

Also:

> Every deadlock causes starvation, but not every starvation is deadlock.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1ce2ce29b35917ac`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `5.1115 rerank_score`

```text
progress for an indefinite period of  time. Deadlock is a form of starvation but with the
stronger condition: a group of threads forms a cycle where none of the threads make progress
because each thread is waiting for some other thread in the cycle to take action. Thus,
deadlock implies starvation (literally, for the dining philosophers), but starvation does not
imply deadlock.
For example, recall the readers/writers example discussed in Section 5.6.1 . A writer only
waits if a reader or writer is active. In the writers-preferred solution we gave, waiting
readers can starve if new writers arrive sufficiently frequently; likewise, waiting writers can
starve if there is an active reader, and new readers arrive and become active before the last
```

#### Chunk 2

- Chunk ID: `12ad4571a11bd814`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `3.65654 rerank_score`

```text
starve if there is an active reader, and new readers arrive and become active before the last
one completes. Note that such starvation would not be deadlock because there is no cycle.
The waiting readers are waiting on the active writers to finish, and the waiting writers are
waiting on the active readers to finish, but no active thread is waiting on a waiting reader or
writer.
Just because a system can suffer deadlock or starvation does not mean that it always will. A
system is subject to starvation if a thread could starve in some circumstances. A system is
subject to deadlock if a group of threads could deadlock in some circumstances. Here, the
circumstances that affect whether deadlock or starvation occurs could include a broad range
```

#### Chunk 3

- Chunk ID: `351cb2d32a30bc43`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `181`
- Score: `2.90376 rerank_score`

```text
approach, there can be a deadlock: each philosopher takes the chopstick on the left but can be
stuck waiting for the philosopher on the right to release the chopstick.
Note that mutually recursive locking is equivalent to Dining Philosophers with n = 2.
The rest of this section addresses the following questions:
Deadlock vs. Starvation. How does deadlock relate to the concepts of liveness and
starvation?
```

#### Chunk 4

- Chunk ID: `e4069986d30cb2eb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `182`
- Score: `2.25468 rerank_score`

```text
circumstances that affect whether deadlock or starvation occurs could include a broad range
of factors, such as: the choices made by the scheduler, the number of threads running, the
workload or sequence of requests processed by the system, which threads win races to
acquire locks, and which threads are enabled in what order when signals or broadcasts occur.
A system that is subject to starvation or deadlock may be live in many or most runs and starve
or deadlock only for particular workloads or “unlucky” interleavings. For example, in
mutually recursive locking, the deadlock only occurs if both threads obtain the outer locks at
about the same time. For the Dining Philosophers problem, philosophers may succeed in
```

#### Chunk 5

- Chunk ID: `b2ba74cf0365cf54`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `178`
- Score: `1.68248 rerank_score`

```text
A deadlock is a cycle of waiting among a set of threads, where each thread waits for some
other thread in the cycle to take some action.
Deadlock can occur in many different situations, but one of the simplest is mutually recursive
locking, shown in the code fragment below:
    // Thread A 
     
    lock1.acquire(); 
    lock2.acquire(); 
    lock2.release(); 
    lock1.release();
    // Thread B 
     
    lock2.acquire(); 
    lock1.acquire(); 
    lock1.release(); 
    lock2.release();
Suppos e two shared obj ects with mutual exclusion locks can call into each other while
holding their locks. Deadlock can occur when one thread holds the lock on the first object,
and another thread holds the lock on the second obj ect. If the first thread calls into the second
```

## q14

**Question:** Why can fine-grained locking improve performance in some programs but make others slower or more error-prone?

### Method A

- Retrieval latency: 0.679s
- Generation latency: 8.566s

**Answer:**

Fine-grained locking can improve performance when it reduces **contention** on a shared lock.

For example, instead of one lock protecting an entire data structure, you split the structure into parts and give each part its own lock. Then two threads can work on different parts at the same time. The source gives an example of a memory heap where different size “buckets” each have their own lock, so threads allocating different-sized blocks may not block each other.

But fine-grained locking can also make a program slower or more error-prone because:

1. **Lock overhead increases**  
   If a thread now has to acquire several locks instead of one, the cost of locking/unlocking may outweigh the benefit of extra concurrency.

2. **More complexity**  
   The programmer must decide which lock protects which data. If that design is unclear, bugs become more likely.

3. **Higher risk of deadlock**  
   If different threads acquire multiple locks in different orders, they can get stuck waiting for each other.

4. **Harder to maintain and tune**  
   Fine-grained locking may require careful tuning, such as choosing how many partitions or groups to use. A simple lock-based design may be easier to reason about.

5. **Not always faster**  
   If contention was not actually a bottleneck, adding fine-grained locks may just add overhead. As the source notes, premature attempts to reduce locking can produce code that is “buggy, hard to maintain, no faster than a clean implementation.”

So the basic trade-off is:

> Fine-grained locking can improve performance by allowing more parallelism, but it can hurt performance and correctness by adding overhead, complexity, and synchronization bugs.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `efd45a9ae61785d3`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `n/a `

```text
it is more complex and may require tuning the number of groups to get good pe rformance.
Further, these trade-offs may change as the implementation becomes more complex. For
example, to trigger resize at appropriate times, we probably need to maintain an additional
nObjects count of the number of objects currently stored in the hash table, so whatever
locking approach we use would need to be extended to cover this information.
EXAMPLE: How might you use fine-grained locking to reduce contention for the lock
protecting the shared memory heap in malloc/free or new/delete?
ANSWER: One approach would be to partition the heap into separate memory regions,
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
```

#### Chunk 2

- Chunk ID: `c881f80821687a9a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `n/a `

```text
should only be considered by experienced programmers who have mastered the basic lock-
based approaches. Many of you will probably never need to use these techniques. If you are
tempted to do s o, take extra care. Measure the performance of your system to ensure that these
techniques yield significant gains, and seek out extra peer review from trusted colleagues to
help ensure that the code works as intended.
Programmers often assume that acquiring a lock is an expensive operation, and therefore try
to reduce locking throughout their programs. The most likely result from premature
optimization is a program that is buggy, hard to maintain, no faster than a clean
implementation, and, ironically, harder to tune than a cleanly architected program. On most
```

#### Chunk 3

- Chunk ID: `e6e96d0fb06d465a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `71`
- Score: `n/a `

```text
slower code execution.
As long as the programmer uses structured synchronization for protecting shared data, the compiler can reorder instructions
as needed without changing program behavior, provided that the compiler does not reorder across synchronization operations.
A compiler making the more conservative assumption that all memory is shared would produce slow code even when it was
not necessary.
For processor architectures, the issue is also performance. Certain optimizations are possible if the programmer is using
structured synchronization but not otherwise. For example, modern processors buffer memory writes to allow instruction
execution to continue while the memory is written in the background. If two adjacent instructions issue memory writes to
```

#### Chunk 4

- Chunk ID: `74908584088ab2f8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `n/a `

```text
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
n buckets, where the ith bucket contains blocks of size 2i, and serves requests of size 2i-1 + 1
to 2i. If there are no free blocks in the ith bucket, an item from the next larger bucket i + 1 is
split in two. Using fine-grained locking, each bucket can be given its own lock. □
6.2.2 Per-Processor Data Structures
A related technique to fine-grained locking is to partition the shared data structure based on
the number of processors on the machine. For example, instead of one shared hash table of
cached pages, an alternative design would have N separate hash tables, where N is the
number of processors. Each thread uses the hash table based on the processor where it is
```

#### Chunk 5

- Chunk ID: `0f37c38a0d4c34a4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `n/a `

```text
Which solution is best? It is not obvi ous. The first solution is simple and appears to allow
high concurrency, but acquiring the readers/writers lock even in read mode may have high
overhead. For example, we gave an implementation of a readers/writers lock in Chapter 5
where acquiring a read-only lock involves acquiring a mutual exclusion lock on both entrance
and exit. Access to the underlying mutual exclusion lock may become a bottleneck.
The second solution makes resize expensive, but if resize is a rare operation, that may be
acceptable. The third solution balances concurrency for get/put against the cost of resize, but
it is more complex and may require tuning the number of groups to get good pe rformance.
```

### Method B

- Retrieval latency: 0.518s
- Generation latency: 8.304s

**Answer:**

Fine-grained locking can improve performance because it lets more threads work in parallel.

Instead of protecting one large shared object with one lock, you split the object’s state into smaller parts, each with its own lock. For example, a hash table could use one lock per bucket. Then two threads accessing different buckets do not block each other, so contention is reduced.

But it can also make a program slower or more error-prone because it adds complexity.

Main trade-offs:

1. More concurrency, less waiting  
   If many threads usually access different parts of the data structure, fine-grained locking helps.  
   Example: different threads using different hash buckets can proceed in parallel.

2. More locking overhead  
   Managing many locks costs time. If contention was not a real bottleneck, the extra lock operations may make the program slower.

3. More complex correctness  
   Some operations need to touch multiple parts of the structure.  
   Example: a hash table resize affects many buckets, not just one. With one global lock, resize is simple. With per-bucket locks, you must carefully decide which locks to take and in what order.

4. Higher risk of bugs  
   Fine-grained locking can introduce deadlocks, race conditions, or inconsistent state if locks are acquired incorrectly.

5. More tuning required  
   The best partitioning depends on the workload. If most requests hit the same bucket or region, fine-grained locking may not help much.

So the basic idea is:

> Fine-grained locking improves performance when lock contention is the bottleneck and accesses are spread across independent parts of the data.  
> It can hurt performance or correctness when the extra locking complexity outweighs the concurrency benefit.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `448d97cf7e52fafa`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `156`
- Score: `1.4464 rerank_score`

```text
measurements can identify any bottlenecks. An adage to follow is: “It is easier to go from a
working system to a working, fast system than to go from a fast system to a fast, working
system.”
We discuss four design patterns to increase concurrency when it is necessary:
Fine-Grained Locking. Partition an object’s state into different subsets each protected
by a different lock.
```

#### Chunk 2

- Chunk ID: `ebdac9b11bc94717`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `157`
- Score: `1.29349 rerank_score`

```text
fine-grained locking.
The web server cache discussed above  provides an example. The cache can use a shared
hash table to store and locate recently used web pages; because the hash table is shared, it
needs a lock to provide mutual exclusion. The lock is acquired and released at the start and
end of each of the hash table methods: put(key, value), value = get(key), and value =
remove(key).
If the single lock limits performance, an alternative is to have one lock per hash bucket. The
methods acquire the lock for bucket b be fore accessing any record that hashes to that bucket.
Provided that the number of buckets is large enough, and no single bucket receives a large
fraction of requests, then different threads can use and update the hash table in parallel.
```

#### Chunk 3

- Chunk ID: `efd45a9ae61785d3`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `1.15538 rerank_score`

```text
it is more complex and may require tuning the number of groups to get good pe rformance.
Further, these trade-offs may change as the implementation becomes more complex. For
example, to trigger resize at appropriate times, we probably need to maintain an additional
nObjects count of the number of objects currently stored in the hash table, so whatever
locking approach we use would need to be extended to cover this information.
EXAMPLE: How might you use fine-grained locking to reduce contention for the lock
protecting the shared memory heap in malloc/free or new/delete?
ANSWER: One approach would be to partition the heap into separate memory regions,
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
```

#### Chunk 4

- Chunk ID: `1f753f66c50547ca`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `157`
- Score: `0.291436 rerank_score`

```text
fraction of requests, then different threads can use and update the hash table in parallel.
However, there is no free lunch. Dividing an object’s state into different pieces protected by
different locks can significantly increase the object’s complexity. Suppos e we want to
implement a hash table whose number of hash buckets grows as the number of objects it
stores increases. If we have a single lock, this is easy to do. B ut, what if we use fine-grained
locking? Then, the design becomes more complex because we have some methods, like put
and get, that operate on one bucket and other methods, like resize, that operate across multiple
buckets.
Several solutions are possible:
1. Introduce a readers/writers lock. Suppos e we have a readers/writers lock on the
```

#### Chunk 5

- Chunk ID: `74908584088ab2f8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `0.0790419 rerank_score`

```text
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
n buckets, where the ith bucket contains blocks of size 2i, and serves requests of size 2i-1 + 1
to 2i. If there are no free blocks in the ith bucket, an item from the next larger bucket i + 1 is
split in two. Using fine-grained locking, each bucket can be given its own lock. □
6.2.2 Per-Processor Data Structures
A related technique to fine-grained locking is to partition the shared data structure based on
the number of processors on the machine. For example, instead of one shared hash table of
cached pages, an alternative design would have N separate hash tables, where N is the
number of processors. Each thread uses the hash table based on the processor where it is
```

### Method C

- Retrieval latency: 0.189s
- Generation latency: 7.035s

**Answer:**

Fine-grained locking can improve performance because it reduces **contention**.

Instead of one large lock protecting an entire shared structure, the program uses multiple smaller locks. For example, a hash table might use one lock per bucket. Then two threads accessing different buckets can run in parallel instead of waiting for the same global lock.

So it helps when:

- many threads access shared data at the same time,
- their accesses usually touch different parts of the data,
- the single coarse lock was a bottleneck.

But fine-grained locking can also make programs slower or more error-prone.

It can be slower because:

- acquiring and releasing many locks has overhead,
- threads may need multiple locks for one operation,
- the program may need extra bookkeeping, such as counts or resize metadata,
- the added complexity may reduce cache efficiency or make tuning harder.

It can be more error-prone because:

- programmers must know exactly which lock protects which data,
- operations involving multiple pieces of data may require multiple locks,
- inconsistent lock ordering can cause deadlock,
- missing one lock can cause races,
- resizing or restructuring a data structure becomes harder to synchronize correctly.

So the trade-off is:

> Fine-grained locking can increase parallelism, but it also increases complexity.

A clean coarse-grained lock is often easier to reason about. Fine-grained locking is useful mainly when measurement shows that lock contention is actually limiting performance.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `efd45a9ae61785d3`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `0.694995 vector_distance`

```text
it is more complex and may require tuning the number of groups to get good pe rformance.
Further, these trade-offs may change as the implementation becomes more complex. For
example, to trigger resize at appropriate times, we probably need to maintain an additional
nObjects count of the number of objects currently stored in the hash table, so whatever
locking approach we use would need to be extended to cover this information.
EXAMPLE: How might you use fine-grained locking to reduce contention for the lock
protecting the shared memory heap in malloc/free or new/delete?
ANSWER: One approach would be to partition the heap into separate memory regions,
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
```

#### Chunk 2

- Chunk ID: `c881f80821687a9a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `0.750765 vector_distance`

```text
should only be considered by experienced programmers who have mastered the basic lock-
based approaches. Many of you will probably never need to use these techniques. If you are
tempted to do s o, take extra care. Measure the performance of your system to ensure that these
techniques yield significant gains, and seek out extra peer review from trusted colleagues to
help ensure that the code works as intended.
Programmers often assume that acquiring a lock is an expensive operation, and therefore try
to reduce locking throughout their programs. The most likely result from premature
optimization is a program that is buggy, hard to maintain, no faster than a clean
implementation, and, ironically, harder to tune than a cleanly architected program. On most
```

#### Chunk 3

- Chunk ID: `e6e96d0fb06d465a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `71`
- Score: `0.816367 vector_distance`

```text
slower code execution.
As long as the programmer uses structured synchronization for protecting shared data, the compiler can reorder instructions
as needed without changing program behavior, provided that the compiler does not reorder across synchronization operations.
A compiler making the more conservative assumption that all memory is shared would produce slow code even when it was
not necessary.
For processor architectures, the issue is also performance. Certain optimizations are possible if the programmer is using
structured synchronization but not otherwise. For example, modern processors buffer memory writes to allow instruction
execution to continue while the memory is written in the background. If two adjacent instructions issue memory writes to
```

#### Chunk 4

- Chunk ID: `74908584088ab2f8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `0.822204 vector_distance`

```text
each with its own lock. For example, a fast implementation of a heap on a uniprocessor uses
n buckets, where the ith bucket contains blocks of size 2i, and serves requests of size 2i-1 + 1
to 2i. If there are no free blocks in the ith bucket, an item from the next larger bucket i + 1 is
split in two. Using fine-grained locking, each bucket can be given its own lock. □
6.2.2 Per-Processor Data Structures
A related technique to fine-grained locking is to partition the shared data structure based on
the number of processors on the machine. For example, instead of one shared hash table of
cached pages, an alternative design would have N separate hash tables, where N is the
number of processors. Each thread uses the hash table based on the processor where it is
```

#### Chunk 5

- Chunk ID: `ebdac9b11bc94717`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `157`
- Score: `0.831746 vector_distance`

```text
fine-grained locking.
The web server cache discussed above  provides an example. The cache can use a shared
hash table to store and locate recently used web pages; because the hash table is shared, it
needs a lock to provide mutual exclusion. The lock is acquired and released at the start and
end of each of the hash table methods: put(key, value), value = get(key), and value =
remove(key).
If the single lock limits performance, an alternative is to have one lock per hash bucket. The
methods acquire the lock for bucket b be fore accessing any record that hashes to that bucket.
Provided that the number of buckets is large enough, and no single bucket receives a large
fraction of requests, then different threads can use and update the hash table in parallel.
```

## q15

**Question:** If one big lock is simpler and correct, why do operating systems ever bother with more complicated synchronization designs?

### Method A

- Retrieval latency: 0.821s
- Generation latency: 8.588s

**Answer:**

Because “one big lock” is often **correct but too restrictive**.

A big lock makes synchronization easy because only one thread can enter the protected code at a time. But operating systems often need many things to happen concurrently:

- **Performance/scalability:** On a multicore machine, one big kernel lock can force CPUs to wait even when they are working on unrelated data.
- **Reduced contention:** If many threads frequently need the same global lock, they spend more time waiting.
- **Responsiveness:** Some OS operations must not be delayed by unrelated long-running operations holding the big lock.
- **Different resources are independent:** For example, two processes accessing different files or different memory regions may not need to block each other.
- **Interrupts and scheduling constraints:** Kernel code often has strict rules about when it can sleep, block, or hold a lock.

So the usual idea is:

> Start with the simplest correct synchronization design, possibly even one big lock.  
> Only make it more complicated when measurement or system requirements show that the simple design is not good enough.

This matches the principle from the text: don’t make synchronization more advanced just because it seems elegant; do it when correctness, performance, or scalability actually require it.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bf113d61ca935ad0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `109`
- Score: `n/a `

```text
2. Always synchronize with locks and condition variables.
Many operating systems, such as Linux, Windows, and MacOS, provide a diversity of
synchronization primitives. At the end of this chapter, we will describe one such
primitive, semaphores, which is particularly widely used in operating system kernel
implementations. Compared to locks and condition variables, semaphores are equally
powerful: you can build condition variables using semaphores and vice versa. If so, why
pick one over the other?
We recommend that you be able to read and understand semaphores so you can
understand legacy code, but that you only write new code using locks and condition
variables. Almost always, code using locks and condition variables is clearer than the
```

#### Chunk 2

- Chunk ID: `4168d41e21de966f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `202`
- Score: `n/a `

```text
Advanced synchronization techniques should be approached with caution. Your first goal
should be to construct a program that works, even if doing so means putting “one big lock”
around everything in a data structure or even in an entire program.
Resist the temptation to do a nything more complicated unless you know that doing so is
necessary. How do y ou know? Do not guess. Measure your system’s performance. Measuring
the “before” and “after” performance of a program and its subsystems not only helps you
make good de cisions about the program on which you are working, but it also helps you
develop good i ntuition for the programs you write in the future.
Spend time early in the design process developing a clean structure for your program. Given
```

#### Chunk 3

- Chunk ID: `316180b92759ba2e`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `109`
- Score: `n/a `

```text
variables. Almost always, code using locks and condition variables is clearer than the
equivalent code using semaphores because it is more “self-documenting.” If the code is
well structured, what each synchronization action is doing should be obvi ous.
Admittedly, semaphores sometimes seem to fit what you are doing perfectly because you
can map the object’s invariants exactly onto the internal state of the semaphore; for
example, you can write an extremely concise version of our blocking bounded queue
```

#### Chunk 4

- Chunk ID: `b6932cd49fdadf9f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `n/a `

```text
Some researchers have posed a radical question: would it be better to write complex
concurrent programs without locks? By eliminating locking, we would remove lock
contention and deadlock as design considerations, fostering a more modular program
structure. However, these techniques can be much more complex to use. To date, concurrent
implementations without locks have only been used for a few carefully designed runtime
library modules written by expert programmers. We sketch the ideas because there is a
chance that they will become more important as the number of processors per computer
continues to increase.
Today, the cases where these approaches are warranted are rare. These advanced techniques
should only be considered by experienced programmers who have mastered the basic lock-
```

#### Chunk 5

- Chunk ID: `7c3cf678395bacec`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `122`
- Score: `n/a `

```text
is no longer important. For example, preempting a thread that holds a lock is immaterial to the behavior of the program.
Rather, the behavior of the program depends on the sequence of synchronization instructions: which thread is first to acquire
the lock, which thread waits on a condition variable, and so forth. Thus, a model checker can proceed in two steps: first
verify that there are no unlocked accesses to shared data, and then enumerate various sequences of synchronization
operations. Even with this, the number of possibilities can be prohibitively large, and so typically the model checker will verify
however many different interleavings it can within some time limit.
5.6.2 Synchronization Barriers
```

### Method B

- Retrieval latency: 0.209s
- Generation latency: 9.311s

**Answer:**

Because “one big lock” is often **correct**, but not always **good enough** for an operating system.

A big lock makes synchronization simple by forcing many operations to run one at a time. That reduces bugs, but it can hurt:

1. **Performance**
   - If every kernel operation needs the same lock, only one CPU can make progress in that part of the OS.
   - On a multicore machine, this wastes parallelism.

2. **Scalability**
   - A design that works fine on 2 cores may become a bottleneck on 32 or 128 cores.
   - More fine-grained locks let unrelated operations proceed at the same time.

3. **Responsiveness**
   - Some OS paths must be fast, such as interrupt handling, scheduling, or I/O completion.
   - Waiting behind a huge global lock can delay important work.

4. **Avoiding unnecessary contention**
   - If two threads are working on unrelated files, processes, or memory regions, they should not necessarily block each other.
   - More specific locks allow concurrency where it is safe.

So the usual principle is:

> Start with the simplest correct design, often a big lock.  
> Only use more complicated synchronization when measurement shows the simple design is a bottleneck.

That matches the idea from OS design: correctness first, then optimize synchronization only when there is evidence that the simpler approach is limiting performance.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bf113d61ca935ad0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `109`
- Score: `0.800283 vector_distance`

```text
2. Always synchronize with locks and condition variables.
Many operating systems, such as Linux, Windows, and MacOS, provide a diversity of
synchronization primitives. At the end of this chapter, we will describe one such
primitive, semaphores, which is particularly widely used in operating system kernel
implementations. Compared to locks and condition variables, semaphores are equally
powerful: you can build condition variables using semaphores and vice versa. If so, why
pick one over the other?
We recommend that you be able to read and understand semaphores so you can
understand legacy code, but that you only write new code using locks and condition
variables. Almost always, code using locks and condition variables is clearer than the
```

#### Chunk 2

- Chunk ID: `4168d41e21de966f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `202`
- Score: `0.815593 vector_distance`

```text
Advanced synchronization techniques should be approached with caution. Your first goal
should be to construct a program that works, even if doing so means putting “one big lock”
around everything in a data structure or even in an entire program.
Resist the temptation to do a nything more complicated unless you know that doing so is
necessary. How do y ou know? Do not guess. Measure your system’s performance. Measuring
the “before” and “after” performance of a program and its subsystems not only helps you
make good de cisions about the program on which you are working, but it also helps you
develop good i ntuition for the programs you write in the future.
Spend time early in the design process developing a clean structure for your program. Given
```

#### Chunk 3

- Chunk ID: `b6932cd49fdadf9f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `0.827628 vector_distance`

```text
Some researchers have posed a radical question: would it be better to write complex
concurrent programs without locks? By eliminating locking, we would remove lock
contention and deadlock as design considerations, fostering a more modular program
structure. However, these techniques can be much more complex to use. To date, concurrent
implementations without locks have only been used for a few carefully designed runtime
library modules written by expert programmers. We sketch the ideas because there is a
chance that they will become more important as the number of processors per computer
continues to increase.
Today, the cases where these approaches are warranted are rare. These advanced techniques
should only be considered by experienced programmers who have mastered the basic lock-
```

#### Chunk 4

- Chunk ID: `7c3cf678395bacec`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `122`
- Score: `0.836175 vector_distance`

```text
is no longer important. For example, preempting a thread that holds a lock is immaterial to the behavior of the program.
Rather, the behavior of the program depends on the sequence of synchronization instructions: which thread is first to acquire
the lock, which thread waits on a condition variable, and so forth. Thus, a model checker can proceed in two steps: first
verify that there are no unlocked accesses to shared data, and then enumerate various sequences of synchronization
operations. Even with this, the number of possibilities can be prohibitively large, and so typically the model checker will verify
however many different interleavings it can within some time limit.
5.6.2 Synchronization Barriers
```

#### Chunk 5

- Chunk ID: `316180b92759ba2e`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `109`
- Score: `0.849754 vector_distance`

```text
variables. Almost always, code using locks and condition variables is clearer than the
equivalent code using semaphores because it is more “self-documenting.” If the code is
well structured, what each synchronization action is doing should be obvi ous.
Admittedly, semaphores sometimes seem to fit what you are doing perfectly because you
can map the object’s invariants exactly onto the internal state of the semaphore; for
example, you can write an extremely concise version of our blocking bounded queue
```

### Method C

- Retrieval latency: 0.373s
- Generation latency: 9.049s

**Answer:**

Because **correctness is only the first goal**. A “one big lock” is often a good starting point because it is simple and easier to reason about, but operating systems sometimes need more complex synchronization when the big lock becomes a performance or latency bottleneck.

Main reasons:

1. **Scalability on multicore systems**  
   If one global lock protects a large part of the kernel, then many CPUs may be forced to wait even when they are doing unrelated work. That wastes parallelism.

2. **High contention**  
   If many threads frequently need the same lock, they spend more time waiting. Splitting the lock into smaller locks can let independent operations proceed at the same time.

3. **Latency requirements**  
   Operating systems often need to respond quickly to interrupts, I/O, scheduling events, or real-time tasks. A big lock can cause long delays if a thread holds it too long.

4. **Different access patterns**  
   Some data structures are read far more often than written. Designs like reader-writer locks or RCU allow many readers to proceed concurrently instead of blocking each other unnecessarily.

5. **Avoiding blocking in critical contexts**  
   Some OS code cannot safely sleep or wait, especially in interrupt handlers or low-level kernel paths. More specialized synchronization may be needed there.

But the important point is: **OS designers should not make synchronization complicated just because they can.** As the source says, the first goal is to build something correct, even with “one big lock.” More advanced designs are justified only when measurement shows that the simple design is too slow or causes unacceptable contention/latency.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4168d41e21de966f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `202`
- Score: `2.5084 rerank_score`

```text
Advanced synchronization techniques should be approached with caution. Your first goal
should be to construct a program that works, even if doing so means putting “one big lock”
around everything in a data structure or even in an entire program.
Resist the temptation to do a nything more complicated unless you know that doing so is
necessary. How do y ou know? Do not guess. Measure your system’s performance. Measuring
the “before” and “after” performance of a program and its subsystems not only helps you
make good de cisions about the program on which you are working, but it also helps you
develop good i ntuition for the programs you write in the future.
Spend time early in the design process developing a clean structure for your program. Given
```

#### Chunk 2

- Chunk ID: `ad35c70a70736a47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `153`
- Score: `0.0582588 rerank_score`

```text
Non-Blocking Synchronization. Are there ways to eliminate locks in complex multi-
object programs? (Section 6.6)
6.1 Multiprocessor Lock Performance
Client-server applications often have ample parallelism for modern multicore architectures
with dozens of processors. Each separate client request can be handled by a different thread
running on a different processor; this is called request parallelism. Likewise, server
operating systems often have ample parallelism – applications with large numbers of threads
can make a large number of concurrent system calls into the kernel.
Even with ample request parallelism, however, performance can often be disappointing.
Once locks and condition variables are added to a server application to allow it to process
```

#### Chunk 3

- Chunk ID: `bf113d61ca935ad0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `109`
- Score: `-0.342656 rerank_score`

```text
2. Always synchronize with locks and condition variables.
Many operating systems, such as Linux, Windows, and MacOS, provide a diversity of
synchronization primitives. At the end of this chapter, we will describe one such
primitive, semaphores, which is particularly widely used in operating system kernel
implementations. Compared to locks and condition variables, semaphores are equally
powerful: you can build condition variables using semaphores and vice versa. If so, why
pick one over the other?
We recommend that you be able to read and understand semaphores so you can
understand legacy code, but that you only write new code using locks and condition
variables. Almost always, code using locks and condition variables is clearer than the
```

#### Chunk 4

- Chunk ID: `2b97ce0c65a7b033`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `-1.09562 rerank_score`

```text
implementation, and, ironically, harder to tune than a cleanly architected program. On most
platforms, acquiring or releasing a lock is a highly tuned primitive — a cquiring an
uncontended lock is often nearly free. If there is contention, you probably needed the lock!
In Section 6.3, we saw an example of synchronization without locks. RCU lets reads proceed
without acquiring a lock or updating shared synchronization state, but it still requires updates
to acquire locks. If the thread that holds the lock is interrupted, has a bug that causes it to stop
making progress, or becomes deadlocked, other threads can be delayed for a long — pe rhaps
unlimited — pe riod of  time.
It is possible to build data structures that are completely non-blocking for both read and
```

#### Chunk 5

- Chunk ID: `2dcd9aa440114400`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `145`
- Score: `-2.13492 rerank_score`

```text
outlined a sequence of steps to writing correct synchronization code for coordinating
access to shared obj ects. Following this methodology has proven enormously helpful for
students in our classes by reducing the likelihood of  design errors.
Implementations of synchronization. Locks and condition variables can be efficiently
implemented using hardware support for atomic read-modify-write instructions and,
where necessary, the ability to temporarily defer hardware interrupts. In particular, we
showed that the overhead of acquiring and releasing a non-contested lock can be as low
as four instructions.
Semaphores. Semaphores are a widely implemented alternative to locks and condition
variables, with a constructive role in managing hardware I/O interrupts.
```

## q16

**Question:** Why can acquiring two locks in different orders be dangerous even if each individual lock is used correctly?

### Method A

- Retrieval latency: 0.482s
- Generation latency: 5.554s

**Answer:**

Acquiring two locks in different orders is dangerous because it can create a **deadlock**, even if each lock is individually used correctly.

Example:

- Thread 1 acquires lock **A**
- Thread 2 acquires lock **B**
- Thread 1 now tries to acquire **B**, but Thread 2 has it
- Thread 2 now tries to acquire **A**, but Thread 1 has it

Now both threads are waiting forever:

```text
Thread 1 holds A, waits for B
Thread 2 holds B, waits for A
```

Each thread followed the locking rules for the individual locks, but the **combination** of lock acquisitions creates a circular wait.

So the problem is not that lock A or lock B is misused individually. The problem is the **inconsistent ordering** across threads. A common solution is to enforce a fixed global order, e.g.:

```text
Always acquire A before B
```

Then circular waiting cannot happen in this simple case.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `43cd53a4cac41057`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `126`
- Score: `3.18573 rerank_score`

```text
disappear.
As we discussed in Chapter 6, two phase locking ensures a strong form of isolation called
serializability. Serializability across transactions ensures that the result of any execution of
the program is equivalent to an execution in which transactions are processed one at a time in
some sequential order. So, even if multiple transactions are executed concurrently, they can
only produce results that they could have produced had they been executed one at a time in
some order.
Although acquiring multiple locks in arbitrary orders normally risks deadlock, transactions
provide a simple solution. If a set of transactions deadlocks, one or more of the transactions
can be forced to roll back, release their locks, and restart at some later time.
Multiversion concurrency control
```

#### Chunk 2

- Chunk ID: `31adea97e6dd91ae`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `137`
- Score: `1.01885 rerank_score`

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

#### Chunk 3

- Chunk ID: `2b2f13d3f308100a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `0.757659 rerank_score`

```text
this may be difficult to determine. Without first executing the request, how can we know
which locks will be needed?
6.4.3 Two-Phase Locking
Two phas e locking refines the acquire-all/release-all pattern to address this concern. Instead
of acquiring all locks before processing the request, locks can be acquired as needed for each
operation. However, locks are not released until all locks needed by the request have been
acquired. Most implementations simply release all locks at the end of the request.
Two-phase locking avoids needing to know what locks to grab a priori. Therefore, programs
can avoid acquiring locks they do n ot need, and they may not need to hold locks as long.
EXAMPLE: The changeKey(item, k1, k2) function for a hash table with per-bucket locks
```

#### Chunk 4

- Chunk ID: `f46346321fc62c67`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `0.288098 rerank_score`

```text
EXAMPLE: The changeKey(item, k1, k2) function for a hash table with per-bucket locks
could be implemented to acquire k1’s lock, remove the item using key k1, acquire k2’s lock,
insert the item using key k2, and release both locks.
Like acquire-all/release-all, two-phase locking is serializable. If two requests have non-
overlapping data, they are commutative and therefore serializable. Otherwise, there is some
overlapping data between the two requests, protected by one or more locks. Provided a
request completes, it must have acquired all of those locks, and made its changes to the
```

#### Chunk 5

- Chunk ID: `72dfbe6fdc5dc3a2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `194`
- Score: `0.130315 rerank_score`

```text
ANSWER: Suppos e a thread needs to acquire locks A and B, in that order, while another
thread needs to acquire lock B first, then A. A thread is always allowed to acquire its
second lock. It may ac quire its first lock provided the other thread does not already hold
its first lock. □
6.5.5 Detecting and Recovering From Deadlocks
Rather than preventing deadlocks, some systems allow deadlocks to occur and recover from
them when they arise.
Why allow deadlocks to occur at all? Sometimes, it is difficult or expensive to enforce
sufficient structure on the system’s data and workloads to guarantee that deadlock will never
occur. If deadlocks are rare, why pay the overhead in the common case to prevent them?
For this approach to work, we need: (i) a way to recover from deadlock when it occurs,
```

### Method B

- Retrieval latency: 0.201s
- Generation latency: 5.134s

**Answer:**

Because the danger is not in either lock by itself, but in the **ordering between locks**.

Suppose two threads both need locks `A` and `B`:

- Thread 1 acquires `A`, then tries to acquire `B`
- Thread 2 acquires `B`, then tries to acquire `A`

Now this can happen:

1. Thread 1 holds `A`
2. Thread 2 holds `B`
3. Thread 1 waits for `B`
4. Thread 2 waits for `A`

Neither thread can continue, because each is waiting for a lock held by the other. This is a **deadlock**.

So even if:

- `A` is always locked correctly before accessing data protected by `A`
- `B` is always locked correctly before accessing data protected by `B`

the program can still fail because the threads acquire multiple locks in inconsistent orders.

A common rule to avoid this is:

> Always acquire multiple locks in the same global order.

For example, always acquire `A` before `B`, never the reverse.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b83691a10e1781c4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `0.801875 vector_distance`

```text
that all locks are acquired at the beginning and released at the end implies that one request is
completed before the other one begins.
Figure 6.13: Locking multiple objects using an acquire-all/release-all pattern results in a serializable execution that is
equivalent to an execution where requests are executed sequentially in some order.
One challenge to using this approach is knowing exactly what locks will be needed by a
request before beginning to process it. A potential solution is to conservatively acquire more
locks than needed (e.g., acquire any locks that may be needed by a particular request), but
this may be difficult to determine. Without first executing the request, how can we know
which locks will be needed?
6.4.3 Two-Phase Locking
```

#### Chunk 2

- Chunk ID: `2b2f13d3f308100a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `0.851383 vector_distance`

```text
this may be difficult to determine. Without first executing the request, how can we know
which locks will be needed?
6.4.3 Two-Phase Locking
Two phas e locking refines the acquire-all/release-all pattern to address this concern. Instead
of acquiring all locks before processing the request, locks can be acquired as needed for each
operation. However, locks are not released until all locks needed by the request have been
acquired. Most implementations simply release all locks at the end of the request.
Two-phase locking avoids needing to know what locks to grab a priori. Therefore, programs
can avoid acquiring locks they do n ot need, and they may not need to hold locks as long.
EXAMPLE: The changeKey(item, k1, k2) function for a hash table with per-bucket locks
```

#### Chunk 3

- Chunk ID: `a2618dd2233bfed8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `114`
- Score: `0.857622 vector_distance`

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

- Chunk ID: `72dfbe6fdc5dc3a2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `194`
- Score: `0.869985 vector_distance`

```text
ANSWER: Suppos e a thread needs to acquire locks A and B, in that order, while another
thread needs to acquire lock B first, then A. A thread is always allowed to acquire its
second lock. It may ac quire its first lock provided the other thread does not already hold
its first lock. □
6.5.5 Detecting and Recovering From Deadlocks
Rather than preventing deadlocks, some systems allow deadlocks to occur and recover from
them when they arise.
Why allow deadlocks to occur at all? Sometimes, it is difficult or expensive to enforce
sufficient structure on the system’s data and workloads to guarantee that deadlock will never
occur. If deadlocks are rare, why pay the overhead in the common case to prevent them?
For this approach to work, we need: (i) a way to recover from deadlock when it occurs,
```

#### Chunk 5

- Chunk ID: `1e2c394bc9680bc7`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `178`
- Score: `0.883443 vector_distance`

```text
overlapping data, before releasing any of them. Thus, any overlapping request must have read
or modified the data in the overlap either entirely before or after the other request.
Unlike acquire-all/release-all, however, two-phase locking can in some cases lead to
deadlock, the topic of the next section.
EXAMPLE: Suppos e one thread starts executing changeKey(item, k1, k2) and another thread
simultaneously tries to move a different item in the other direction from k2 to k1. If the first
thread acquires k1’s lock and the second thread acquires k2’s lock, neither will be able to
make progress.
6.5 Deadlock
A challenge to constructing complex multi-threaded programs is the possibility of deadlock.
A deadlock is a cycle of waiting among a set of threads, where each thread waits for some
```

### Method C

- Retrieval latency: 0.673s
- Generation latency: 5.467s

**Answer:**

Because the danger is not in either lock by itself, but in the **interaction between threads**.

If two threads need the same two locks but acquire them in different orders, they can deadlock:

```text
Thread A: lock L1
Thread B: lock L2

Thread A: tries to lock L2, but B has it
Thread B: tries to lock L1, but A has it
```

Now:

- Thread A is waiting for Thread B to release `L2`
- Thread B is waiting for Thread A to release `L1`
- Neither can continue
- So neither releases its lock

This is a **deadlock**: a cycle of waiting.

Each individual lock may be used “correctly” in the sense that threads acquire before accessing shared data and release afterward. But if the program does not enforce a **consistent lock acquisition order**, multiple correct-looking lock uses can combine into an unsafe global behavior.

A common fix is: always acquire locks in the same order, for example always lock `L1` before `L2`.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b83691a10e1781c4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `n/a `

```text
that all locks are acquired at the beginning and released at the end implies that one request is
completed before the other one begins.
Figure 6.13: Locking multiple objects using an acquire-all/release-all pattern results in a serializable execution that is
equivalent to an execution where requests are executed sequentially in some order.
One challenge to using this approach is knowing exactly what locks will be needed by a
request before beginning to process it. A potential solution is to conservatively acquire more
locks than needed (e.g., acquire any locks that may be needed by a particular request), but
this may be difficult to determine. Without first executing the request, how can we know
which locks will be needed?
6.4.3 Two-Phase Locking
```

#### Chunk 2

- Chunk ID: `2b2f13d3f308100a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `177`
- Score: `n/a `

```text
this may be difficult to determine. Without first executing the request, how can we know
which locks will be needed?
6.4.3 Two-Phase Locking
Two phas e locking refines the acquire-all/release-all pattern to address this concern. Instead
of acquiring all locks before processing the request, locks can be acquired as needed for each
operation. However, locks are not released until all locks needed by the request have been
acquired. Most implementations simply release all locks at the end of the request.
Two-phase locking avoids needing to know what locks to grab a priori. Therefore, programs
can avoid acquiring locks they do n ot need, and they may not need to hold locks as long.
EXAMPLE: The changeKey(item, k1, k2) function for a hash table with per-bucket locks
```

#### Chunk 3

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

#### Chunk 4

- Chunk ID: `1e2c394bc9680bc7`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `178`
- Score: `n/a `

```text
overlapping data, before releasing any of them. Thus, any overlapping request must have read
or modified the data in the overlap either entirely before or after the other request.
Unlike acquire-all/release-all, however, two-phase locking can in some cases lead to
deadlock, the topic of the next section.
EXAMPLE: Suppos e one thread starts executing changeKey(item, k1, k2) and another thread
simultaneously tries to move a different item in the other direction from k2 to k1. If the first
thread acquires k1’s lock and the second thread acquires k2’s lock, neither will be able to
make progress.
6.5 Deadlock
A challenge to constructing complex multi-threaded programs is the possibility of deadlock.
A deadlock is a cycle of waiting among a set of threads, where each thread waits for some
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

## q17

**Question:** If non-blocking synchronization avoids locks, does that mean it also avoids all concurrency bugs?

### Method A

- Retrieval latency: 0.182s
- Generation latency: 8.839s

**Answer:**

No. **Non-blocking synchronization avoids locks, but it does not avoid all concurrency bugs.**

It mainly avoids some **lock-related problems**, such as:

- deadlock caused by waiting for locks
- a thread being blocked because another thread holding a lock stopped or was interrupted
- some lock contention overhead

But non-blocking code can still have concurrency bugs, for example:

- **race conditions** if shared data is updated incorrectly
- **atomicity bugs**, where a multi-step operation is not made indivisible
- **livelock**, where threads keep retrying but no one makes useful progress
- **starvation**, where one thread repeatedly loses and never completes
- subtle hardware/compiler **memory ordering** issues
- problems like the **ABA problem** in compare-and-swap algorithms

So the key idea is:

> Non-blocking synchronization removes blocking on locks, but correctness still depends on carefully coordinating concurrent access to shared data.

In fact, non-blocking algorithms are often harder to design correctly than lock-based ones.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `2b97ce0c65a7b033`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `0.840254 vector_distance`

```text
implementation, and, ironically, harder to tune than a cleanly architected program. On most
platforms, acquiring or releasing a lock is a highly tuned primitive — a cquiring an
uncontended lock is often nearly free. If there is contention, you probably needed the lock!
In Section 6.3, we saw an example of synchronization without locks. RCU lets reads proceed
without acquiring a lock or updating shared synchronization state, but it still requires updates
to acquire locks. If the thread that holds the lock is interrupted, has a bug that causes it to stop
making progress, or becomes deadlocked, other threads can be delayed for a long — pe rhaps
unlimited — pe riod of  time.
It is possible to build data structures that are completely non-blocking for both read and
```

#### Chunk 2

- Chunk ID: `ad35c70a70736a47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `153`
- Score: `0.89264 vector_distance`

```text
Non-Blocking Synchronization. Are there ways to eliminate locks in complex multi-
object programs? (Section 6.6)
6.1 Multiprocessor Lock Performance
Client-server applications often have ample parallelism for modern multicore architectures
with dozens of processors. Each separate client request can be handled by a different thread
running on a different processor; this is called request parallelism. Likewise, server
operating systems often have ample parallelism – applications with large numbers of threads
can make a large number of concurrent system calls into the kernel.
Even with ample request parallelism, however, performance can often be disappointing.
Once locks and condition variables are added to a server application to allow it to process
```

#### Chunk 3

- Chunk ID: `5eab508b865e9e16`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `141`
- Score: `0.91981 vector_distance`

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

- Chunk ID: `b4124c78fb2e3620`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `195`
- Score: `0.94541 vector_distance`

```text
Because deadlocks are rare and hard to test for, this requires coding discipline to handle
error conditions systematically throughout the program.
Optimistic concurrency control
Transactions can also be used to avoid deadlocks. Optimistic concurrency control lets transactions execute in parallel
without locking any data, but it only lets a transaction commit if none of the objects accessed by the transaction have
been modified since the transaction began. Otherwise, the transaction must abort and retry.
```

#### Chunk 5

- Chunk ID: `7c3cf678395bacec`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `122`
- Score: `0.95255 vector_distance`

```text
is no longer important. For example, preempting a thread that holds a lock is immaterial to the behavior of the program.
Rather, the behavior of the program depends on the sequence of synchronization instructions: which thread is first to acquire
the lock, which thread waits on a condition variable, and so forth. Thus, a model checker can proceed in two steps: first
verify that there are no unlocked accesses to shared data, and then enumerate various sequences of synchronization
operations. Even with this, the number of possibilities can be prohibitively large, and so typically the model checker will verify
however many different interleavings it can within some time limit.
5.6.2 Synchronization Barriers
```

### Method B

- Retrieval latency: 0.539s
- Generation latency: 6.618s

**Answer:**

No. **Non-blocking synchronization avoids locks, but it does not avoid all concurrency bugs.**

It mainly avoids bugs caused by **blocking on locks**, such as:

- deadlock from circular lock waiting
- a thread being delayed forever because the lock holder stopped
- some forms of lock contention bottlenecks

But non-blocking code can still have concurrency problems, for example:

- **race conditions** if shared state is updated incorrectly
- **lost updates** if compare-and-swap logic is wrong
- **ABA problems**, where a value changes away and back again unnoticed
- **livelock** or repeated retries under contention
- **starvation**, unless the algorithm is wait-free
- subtle **memory ordering** bugs

So the idea is not “no concurrency bugs.” It is more like:

> Non-blocking synchronization avoids lock-based blocking, but correctness still depends on carefully designed concurrent algorithms.

That is why the text says designing efficient wait-free and lock-free data structures is still mostly the domain of experts.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ad35c70a70736a47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `153`
- Score: `1.5709 rerank_score`

```text
Non-Blocking Synchronization. Are there ways to eliminate locks in complex multi-
object programs? (Section 6.6)
6.1 Multiprocessor Lock Performance
Client-server applications often have ample parallelism for modern multicore architectures
with dozens of processors. Each separate client request can be handled by a different thread
running on a different processor; this is called request parallelism. Likewise, server
operating systems often have ample parallelism – applications with large numbers of threads
can make a large number of concurrent system calls into the kernel.
Even with ample request parallelism, however, performance can often be disappointing.
Once locks and condition variables are added to a server application to allow it to process
```

#### Chunk 2

- Chunk ID: `2b97ce0c65a7b033`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `1.26773 rerank_score`

```text
implementation, and, ironically, harder to tune than a cleanly architected program. On most
platforms, acquiring or releasing a lock is a highly tuned primitive — a cquiring an
uncontended lock is often nearly free. If there is contention, you probably needed the lock!
In Section 6.3, we saw an example of synchronization without locks. RCU lets reads proceed
without acquiring a lock or updating shared synchronization state, but it still requires updates
to acquire locks. If the thread that holds the lock is interrupted, has a bug that causes it to stop
making progress, or becomes deadlocked, other threads can be delayed for a long — pe rhaps
unlimited — pe riod of  time.
It is possible to build data structures that are completely non-blocking for both read and
```

#### Chunk 3

- Chunk ID: `65f7a8ea2d5885dc`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `199`
- Score: `0.545246 rerank_score`

```text
put us in a deadlocked state?” and then blocking any request that does. The Coffman et al.
algorithm highlights that deadlock is determined not just by what requests are granted but also
by what requests are waiting. The request that triggers deadlock (“circular wait”) will be a
request that waits, not one that is granted.
6.6 Non-Blocking Synchronization
Chapter 5 described a core abstraction for synchronization — s hared obj ects, with one lock
per object. This abstraction works well for building multi-threaded programs the vast
majority of the time. As concurrent programs become more complicated, however, issues of
lock contention, the semantics of operations that span multiple objects, and deadlock can
```

#### Chunk 4

- Chunk ID: `f11c92628d533ecb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `201`
- Score: `0.442972 rerank_score`

```text
designing efficient wait-free and lock-free data structures remains the dom ain of experts.
Nonetheless, non-blocking algorithms exist for a wide range of data structures, including
FIFO queues, dou ble-ended queues, LIFO stacks, sets, and balanced trees. Several of these
can be found in the Java Virtual Machine runtime library.
In addition, considerable effort has also gone into studying ways to automate the construction
of wait-free and lock-free data structures. For example, transactions with optimistic
concurrency control provide a very flexible approach to implementing lock-free applications.
Recall that optimistic concurrency control lets transactions proceed without locking the data
they access. Transactions abort if, at commit-time, any of their accessed data has changed in
```

#### Chunk 5

- Chunk ID: `b4124c78fb2e3620`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `195`
- Score: `0.0708559 rerank_score`

```text
Because deadlocks are rare and hard to test for, this requires coding discipline to handle
error conditions systematically throughout the program.
Optimistic concurrency control
Transactions can also be used to avoid deadlocks. Optimistic concurrency control lets transactions execute in parallel
without locking any data, but it only lets a transaction commit if none of the objects accessed by the transaction have
been modified since the transaction began. Otherwise, the transaction must abort and retry.
```

### Method C

- Retrieval latency: 0.790s
- Generation latency: 6.853s

**Answer:**

No. **Non-blocking synchronization avoids some lock-related problems, but not all concurrency bugs.**

It can help avoid bugs such as:

- **Deadlock** caused by threads waiting on locks forever
- **Lock convoying** or long delays when a lock holder is interrupted
- Some forms of **priority inversion**
- Blocking because another thread stopped while holding a lock

But non-blocking code can still have concurrency bugs, for example:

- **Race conditions** from incorrect shared-state updates
- **Atomicity bugs**, where several operations need to appear as one operation
- **Memory ordering bugs**, especially on modern CPUs
- **ABA problems**, where a value changes from `A → B → A` and a thread mistakenly thinks nothing changed
- **Starvation**, depending on the algorithm

So the key idea is:

> Non-blocking synchronization removes locks as the waiting mechanism, but it does not remove the need for careful synchronization.

It often makes progress guarantees better, but the algorithms can be harder to design and verify correctly than lock-based ones.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `2b97ce0c65a7b033`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `200`
- Score: `n/a `

```text
implementation, and, ironically, harder to tune than a cleanly architected program. On most
platforms, acquiring or releasing a lock is a highly tuned primitive — a cquiring an
uncontended lock is often nearly free. If there is contention, you probably needed the lock!
In Section 6.3, we saw an example of synchronization without locks. RCU lets reads proceed
without acquiring a lock or updating shared synchronization state, but it still requires updates
to acquire locks. If the thread that holds the lock is interrupted, has a bug that causes it to stop
making progress, or becomes deadlocked, other threads can be delayed for a long — pe rhaps
unlimited — pe riod of  time.
It is possible to build data structures that are completely non-blocking for both read and
```

#### Chunk 2

- Chunk ID: `ad35c70a70736a47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `153`
- Score: `n/a `

```text
Non-Blocking Synchronization. Are there ways to eliminate locks in complex multi-
object programs? (Section 6.6)
6.1 Multiprocessor Lock Performance
Client-server applications often have ample parallelism for modern multicore architectures
with dozens of processors. Each separate client request can be handled by a different thread
running on a different processor; this is called request parallelism. Likewise, server
operating systems often have ample parallelism – applications with large numbers of threads
can make a large number of concurrent system calls into the kernel.
Even with ample request parallelism, however, performance can often be disappointing.
Once locks and condition variables are added to a server application to allow it to process
```

#### Chunk 3

- Chunk ID: `5eab508b865e9e16`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `141`
- Score: `n/a `

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

- Chunk ID: `7c3cf678395bacec`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `122`
- Score: `n/a `

```text
is no longer important. For example, preempting a thread that holds a lock is immaterial to the behavior of the program.
Rather, the behavior of the program depends on the sequence of synchronization instructions: which thread is first to acquire
the lock, which thread waits on a condition variable, and so forth. Thus, a model checker can proceed in two steps: first
verify that there are no unlocked accesses to shared data, and then enumerate various sequences of synchronization
operations. Even with this, the number of possibilities can be prohibitively large, and so typically the model checker will verify
however many different interleavings it can within some time limit.
5.6.2 Synchronization Barriers
```

#### Chunk 5

- Chunk ID: `2dcd9aa440114400`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `145`
- Score: `n/a `

```text
outlined a sequence of steps to writing correct synchronization code for coordinating
access to shared obj ects. Following this methodology has proven enormously helpful for
students in our classes by reducing the likelihood of  design errors.
Implementations of synchronization. Locks and condition variables can be efficiently
implemented using hardware support for atomic read-modify-write instructions and,
where necessary, the ability to temporarily defer hardware interrupts. In particular, we
showed that the overhead of acquiring and releasing a non-contested lock can be as low
as four instructions.
Semaphores. Semaphores are a widely implemented alternative to locks and condition
variables, with a constructive role in managing hardware I/O interrupts.
```

## q18

**Question:** If disabling interrupts can prevent races on a uniprocessor, why not just use that technique everywhere instead of locks?

### Method A

- Retrieval latency: 0.209s
- Generation latency: 7.820s

**Answer:**

Disabling interrupts works only in a very limited setting: mainly **inside a uniprocessor kernel for very short critical sections**.

It is not a general replacement for locks because:

1. **It only stops context switches on the current CPU**  
   On a uniprocessor, if interrupts are disabled, the running thread cannot be preempted, so no other thread runs.  
   But on a **multiprocessor**, other CPUs keep running. Disabling interrupts on CPU 0 does not stop a thread on CPU 1 from accessing the same shared data.

2. **It can make the system unresponsive**  
   If interrupts are disabled for too long, the OS cannot handle timer interrupts, keyboard input, network packets, disk events, etc. The whole system may appear frozen.

3. **It is unsafe for user programs**  
   User-level code cannot be trusted with the ability to disable interrupts. A buggy or malicious program could disable interrupts and never re-enable them, monopolizing the processor.

4. **Interrupt handlers can deadlock**  
   If an interrupt handler tries to acquire a lock that was held by the interrupted thread, it could spin forever. Operating systems avoid this by keeping interrupt handlers simple and carefully controlling which locks are used with interrupts disabled.

So the idea is:

```cpp
Lock::acquire() { disableInterrupts(); }
Lock::release() { enableInterrupts(); }
```

can provide mutual exclusion on a **single CPU**, but it is too restrictive and dangerous as a general solution.

Locks are needed because they work in broader situations, especially when:
- there are multiple processors,
- critical sections may take longer,
- user-level code is involved,
- the OS needs to remain responsive.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `69f42079df361a8c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `128`
- Score: `0.668674 vector_distance`

```text
library functions that can trigger a context switch) during the sequence.
This observation suggests a trivial — bu t seriously limited — a pproach to implementing
locks on a uniprocessor:
    Lock::acquire() { disableInterrupts(); } 
     
    Lock::release() { enableInterrupts(); }
```

#### Chunk 2

- Chunk ID: `bdb778584564720d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `0.699436 vector_distance`

```text
This implementation does provide the mutual exclusion property we need from locks. Some
uniprocessor kernels use this simple approach, but it does not suffice as a general
implementation for locks. If the code sequence the lock protects runs for a long time,
interrupts will be disabled for that long. This will prevent other threads from running, and it
will make the system unresponsive to handling user inputs or other real-time tasks.
Furthermore, although this approach can work in the kernel where all code is (presumably)
carefully crafted and trusted to release the lock quickly, we cannot let untrusted user-level
code run with interrupts turned off since a malicious or buggy program could then monopolize
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
```

#### Chunk 3

- Chunk ID: `9c25ff221a7d2e24`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `132`
- Score: `0.705613 vector_distance`

```text
deadlock can result if the interrupt arrives at an inopportune moment. The handler could spin forever waiting for a lock held
by the thread it interrupted. Most likely, the system would need to be rebooted to clear the problem.
To avoid these types of errors, most operating systems keep interrupt handlers extremely simple. For example, many interrupt
handlers simply wake up a thread to do the heavy lifting of managing the I/O device. Waking up a thread requires mutually
exclusive access to the ready list, protected by a spinlock that is never used without first disabling interrupts.
5.7.4 Implementing Multiprocessor Queueing Locks
Often, we need to support critical sections of varying length. For example, we may want a
```

#### Chunk 4

- Chunk ID: `19edba12e90247fb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `130`
- Score: `0.780457 vector_distance`

```text
interrupts before performing a context switch. As a result, interrupts are always disabled
when the thread runs again after a context switch. Thus, whenever a thread returns from a
context switch, it must re-enable interrupts. For example, the Lock::acquire code in
Figure 5.15 re-enables interrupts before returning; the yield implementation in Chapter 4
disables interrupts before the context switch and then re-enables them afterwards. □
5.7.3 Implementing Multiprocessor Spinlocks
On a multiprocessor, however, disabling interrupts is insufficient. Even when interrupts are
turned off on one processor, other threads are running concurrently. Operations by a thread on
one processor are interleaved with operations by other threads on other processors.
```

#### Chunk 5

- Chunk ID: `1cc055af9a74f286`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `130`
- Score: `0.781605 vector_distance`

```text
one processor are interleaved with operations by other threads on other processors.
Since turning off interrupts is insufficient, most processor architectures provide atomic read-
modify-write instructions to support synchronization. These instructions can read a value
```

### Method B

- Retrieval latency: 0.946s
- Generation latency: 8.497s

**Answer:**

Because disabling interrupts is a very limited trick, not a general replacement for locks.

Main reasons:

1. **It only works on a uniprocessor**
   
   On one CPU, disabling interrupts prevents the current thread from being preempted, so no other thread can run and touch the shared data.

   But on a **multiprocessor**, other CPUs keep running even if one CPU disables interrupts. So another thread on another core can still access the same shared data. You still need locks or other synchronization.

2. **It makes the system unresponsive**
   
   If interrupts are disabled for too long, the CPU cannot respond to timer interrupts, keyboard input, network packets, disk events, etc.

   So if a critical section takes a long time, the whole system can become sluggish or miss real-time events.

3. **It is unsafe for user programs**
   
   User-level code cannot be trusted to run with interrupts disabled. A buggy or malicious program could disable interrupts and never re-enable them, effectively monopolizing the processor.

4. **It is too low-level and kernel-specific**
   
   Disabling interrupts is sometimes used inside kernels for very short critical sections, especially around scheduler or interrupt-handler data structures. But it is not suitable as a general synchronization mechanism for normal code.

So the short answer is:

> Disabling interrupts can prevent races only on a single processor and only for very short, trusted kernel code. Locks are needed because they work more generally, including with multiple CPUs and longer critical sections.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bdb778584564720d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `n/a `

```text
This implementation does provide the mutual exclusion property we need from locks. Some
uniprocessor kernels use this simple approach, but it does not suffice as a general
implementation for locks. If the code sequence the lock protects runs for a long time,
interrupts will be disabled for that long. This will prevent other threads from running, and it
will make the system unresponsive to handling user inputs or other real-time tasks.
Furthermore, although this approach can work in the kernel where all code is (presumably)
carefully crafted and trusted to release the lock quickly, we cannot let untrusted user-level
code run with interrupts turned off since a malicious or buggy program could then monopolize
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
```

#### Chunk 2

- Chunk ID: `9c25ff221a7d2e24`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `132`
- Score: `n/a `

```text
deadlock can result if the interrupt arrives at an inopportune moment. The handler could spin forever waiting for a lock held
by the thread it interrupted. Most likely, the system would need to be rebooted to clear the problem.
To avoid these types of errors, most operating systems keep interrupt handlers extremely simple. For example, many interrupt
handlers simply wake up a thread to do the heavy lifting of managing the I/O device. Waking up a thread requires mutually
exclusive access to the ready list, protected by a spinlock that is never used without first disabling interrupts.
5.7.4 Implementing Multiprocessor Queueing Locks
Often, we need to support critical sections of varying length. For example, we may want a
```

#### Chunk 3

- Chunk ID: `19edba12e90247fb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `130`
- Score: `n/a `

```text
interrupts before performing a context switch. As a result, interrupts are always disabled
when the thread runs again after a context switch. Thus, whenever a thread returns from a
context switch, it must re-enable interrupts. For example, the Lock::acquire code in
Figure 5.15 re-enables interrupts before returning; the yield implementation in Chapter 4
disables interrupts before the context switch and then re-enables them afterwards. □
5.7.3 Implementing Multiprocessor Spinlocks
On a multiprocessor, however, disabling interrupts is insufficient. Even when interrupts are
turned off on one processor, other threads are running concurrently. Operations by a thread on
one processor are interleaved with operations by other threads on other processors.
```

#### Chunk 4

- Chunk ID: `69f7c5d7d1fe5aad`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `73`
- Score: `n/a `

```text
I/O event to complete, but that is much less than one for every process.
Of course, now that memory is much cheaper, most systems keep things simple and allocate a kernel stack per process or
thread.
2.4.4 Interrupt Masking
Interrupts arrive asynchronously; the processor could be executing either user or kernel code
when an interrupt arrives. In certain regions of the kernel — s uch as inside interrupt handlers
themselves, or inside the CPU scheduler — taking an interrupt could cause confusion. If an
interrupt handler is interrupted, we cannot set the stack pointer to poi nt to the base of the
kernel’s interrupt stack — doi ng so would obl iterate the state of the first handler.
To simplify the kernel design, the hardware provides a privileged instruction to temporarily
```

#### Chunk 5

- Chunk ID: `ad35c70a70736a47`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `153`
- Score: `n/a `

```text
Non-Blocking Synchronization. Are there ways to eliminate locks in complex multi-
object programs? (Section 6.6)
6.1 Multiprocessor Lock Performance
Client-server applications often have ample parallelism for modern multicore architectures
with dozens of processors. Each separate client request can be handled by a different thread
running on a different processor; this is called request parallelism. Likewise, server
operating systems often have ample parallelism – applications with large numbers of threads
can make a large number of concurrent system calls into the kernel.
Even with ample request parallelism, however, performance can often be disappointing.
Once locks and condition variables are added to a server application to allow it to process
```

### Method C

- Retrieval latency: 0.456s
- Generation latency: 7.402s

**Answer:**

Because disabling interrupts is only a limited trick, not a general replacement for locks.

On a **uniprocessor**, disabling interrupts can prevent races because the running thread cannot be preempted, so no other thread runs in the middle of the critical section.

But it has major problems:

1. **It only works on one CPU**
   - On a multiprocessor, disabling interrupts on one processor does not stop threads running on other processors.
   - So another CPU could still access the same shared data.

2. **It makes the system unresponsive**
   - If interrupts are disabled for too long, the OS cannot respond to timers, keyboard input, network packets, disk events, etc.
   - The source notes that long critical sections with interrupts disabled can prevent other threads from running and make the system unresponsive.

3. **It is unsafe for user-level code**
   - You cannot let arbitrary user programs disable interrupts.
   - A buggy or malicious program could disable interrupts and monopolize the processor.

4. **It does not work well when waiting is needed**
   - If a resource is busy, the thread should usually block or yield.
   - But with interrupts disabled, blocking or context switching is problematic.

So disabling interrupts is sometimes used **briefly inside the kernel** to protect small scheduler or lock data structures, but general synchronization should use locks, especially queueing locks or spinlocks depending on the situation.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bdb778584564720d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `2.66095 rerank_score`

```text
This implementation does provide the mutual exclusion property we need from locks. Some
uniprocessor kernels use this simple approach, but it does not suffice as a general
implementation for locks. If the code sequence the lock protects runs for a long time,
interrupts will be disabled for that long. This will prevent other threads from running, and it
will make the system unresponsive to handling user inputs or other real-time tasks.
Furthermore, although this approach can work in the kernel where all code is (presumably)
carefully crafted and trusted to release the lock quickly, we cannot let untrusted user-level
code run with interrupts turned off since a malicious or buggy program could then monopolize
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
```

#### Chunk 2

- Chunk ID: `d5881305523260a4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `129`
- Score: `1.45419 rerank_score`

```text
the processor.
5.7.2 Implementing Uniprocessor Queueing Locks
A more general solution is based on the observation that if the lock is BUSY, there is no poi nt
in running the acquiring thread until the lock is free. Instead, we should context switch to the
next ready thread.
The implementation briefly disables interrupts to protect the lock’s data structures, but re-
enables them once a thread has acquired the lock or determined that the lock is BUSY. The
Lock implementation shown in Figure 5.15 illustrates this approach. If a lock is BUSY when
a thread tries to acquire it, the thread moves its TCB onto the lock’s waiting list. The thread
then suspends itself and switches to the next runnable thread. The call to suspend doe s not
```

#### Chunk 3

- Chunk ID: `9c25ff221a7d2e24`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `132`
- Score: `1.41572 rerank_score`

```text
deadlock can result if the interrupt arrives at an inopportune moment. The handler could spin forever waiting for a lock held
by the thread it interrupted. Most likely, the system would need to be rebooted to clear the problem.
To avoid these types of errors, most operating systems keep interrupt handlers extremely simple. For example, many interrupt
handlers simply wake up a thread to do the heavy lifting of managing the I/O device. Waking up a thread requires mutually
exclusive access to the ready list, protected by a spinlock that is never used without first disabling interrupts.
5.7.4 Implementing Multiprocessor Queueing Locks
Often, we need to support critical sections of varying length. For example, we may want a
```

#### Chunk 4

- Chunk ID: `0adcfec3e99d71a5`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `132`
- Score: `1.04592 rerank_score`

```text
Interrupt handlers and spinlocks
Whenever an interrupt handler accesses shared data, that data must be protected by a spinlock instead of a queueing lock.
As we explained in Chapter 2 and Chapter 4, interrupt handlers are not threads: they must run to completion without blocking
so that the hardware can deliver the next interrupt. With a queueing lock, the lock might be held when the interrupt handler
starts, making it impossible for the interrupt handler to work correctly.
Whenever any thread acquires a spinlock used within an interrupt handler, the thread must disable interrupts first. Otherwise,
deadlock can result if the interrupt arrives at an inopportune moment. The handler could spin forever waiting for a lock held
```

#### Chunk 5

- Chunk ID: `072c8e815bc51e5f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `128`
- Score: `0.881538 rerank_score`

```text
atomically read and update a word of memory. These instructions are globally atomic
with respect to the instructions on every processor.
Each of these primitives also serves as a memory barrier; they inform the compiler and
hardware that all prior instructions must complete before the atomic instruction is executed.
5.7.1 Implementing Uniprocessor Locks by Disabling Interrupts
On a uniprocessor, any sequence of instructions by one thread appears atomic to other threads
if no context switch occurs in the middle of the sequence. So, on  a uniprocessor, a thread can
make a sequence of actions atomic by disabling interrupts (and refraining from calling thread
library functions that can trigger a context switch) during the sequence.
```

## q19

**Question:** Why can a scheduler that maximizes throughput still make a system feel slow to users?

### Method A

- Retrieval latency: 0.248s
- Generation latency: 5.930s

**Answer:**

Because **throughput** and **user-perceived responsiveness** are different goals.

A scheduler that maximizes throughput tries to complete **as many tasks per unit time as possible**. That can favor long CPU-heavy jobs or reduce context switches. But users usually care about **response time**: how quickly the system reacts to actions like typing, clicking, or opening a menu.

So a high-throughput scheduler might:

- keep the CPU busy with large background tasks,
- delay small interactive tasks,
- reduce scheduling overhead by switching less often,
- allow some tasks to wait a long time.

Example: if a big file compression job is running, a throughput-focused scheduler may let it run for a long time because that is efficient overall. But then your keypress or mouse click may wait, making the system feel sluggish.

So the system can be doing a lot of work efficiently, but still feel slow because **the tasks users notice are not being scheduled quickly enough**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `9d5edc0692b990f9`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `0.724552 vector_distance`

```text
browser’s packets would have only a minimal impact on the dow nload speed and a large
impact on the perceived responsiveness of the system.
7.1.4 Max-Min Fairness
In many settings, a fair allocation of resources is as important to the design of a scheduler as
responsiveness and low overhead. On a multi-user machine or on a server, we do n ot want to
allow a single user to be able to monopolize the resources of the machine, degrading service
for other users. While it might seem that fairness has little value in single-user machines,
individual applications are often written by different companies, each with an interest in
making their application performance look good e ven if that comes at a cost of degrading
responsiveness for other applications.
```

#### Chunk 2

- Chunk ID: `d7027a807c6db7f6`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `207`
- Score: `0.741606 vector_distance`

```text
for multiple user requests or tasks. For example, in a word processor, each character typed is an individual user
request to add that character to the file and display the result on the screen.
Response time (or delay). The user-perceived time to do some task.
Predictability. Low variance in response times for repeated requests.
Throughput. The rate at which tasks are completed.
Scheduling overhead. The time to switch from one task to another.
Fairness. Equality in the number and timeliness of resources given to each task.
Starvation. The lack of progress for one task, due to resources given to a higher priority task.
Chapter roadmap:
Uniprocessor Scheduling. How do u niprocessor scheduling policies affect fairness,
response time, and throughput? (Section 7.1)
```

#### Chunk 3

- Chunk ID: `149f31d47200fa99`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `205`
- Score: `0.750185 vector_distance`

```text
improving user-perceived response time. Advertising that your operating system uses the
same scheduling algorithm as the DMV is probably not going to increase your sales!
You might think that the answer to this question is unimportant. With the million-fold
improvement in processor performance over the past thirty years, it might seem that we are a
million times less likely to have anything waiting for its turn on a processor. We disagree!
Server operating systems in particular are often overloaded. Parallel applications can create
more work than processors, and if care is not taken in the design of the scheduling policy,
performance can badly degrade. There are subtle relationships between scheduling policy
and energy management on battery-powered devices such as smartphones and laptops.
```

#### Chunk 4

- Chunk ID: `548da36b62b9a80f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `252`
- Score: `0.778093 vector_distance`

```text
More sophisticated scheduling can help at low to moderate load, bu t if the load is more than
system can handle, response time will spike, even for short tasks.
The key idea in overload management is to design your system to do l ess work when
overloaded. This will seem strange! After all, you want your system to work a particular
way; how can you cripple the user’s experience just when your system becomes popu lar?
Under overload conditions, however, your system is incapable of serving all of the requests
in the normal way. The only question is: do y ou choose what to disable, or do y ou let events
choose for you?
An obvi ous step is to simply reject some requests in order to preserve reasonable response
```

#### Chunk 5

- Chunk ID: `9eb0d5a7a4a7804c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `225`
- Score: `0.812101 vector_distance`

```text
scheduled, increasing overhead.
I/O. Many parallel applications do I/O, and this can cause problems if the operating
system scheduler is oblivious to the application decomposition into parallel work. If a
read or write request blocks in the kernel, the thread blocks as well. To reuse the
processor while the thread is waiting, the application program must have created more
threads than processors, so that the scheduler can have an extra one to run in place of the
blocked thread. However, if the thread doe s not block (e.g., on a file read when the file
is cached in memory), that means that the scheduler has more threads than processors,
and so needs to do t ime slicing to multiplex threads onto processors — c ausing all of the
problems we have listed above .
Gang Scheduling
```

### Method B

- Retrieval latency: 0.875s
- Generation latency: 7.477s

**Answer:**

A scheduler can maximize **throughput**—the number of tasks completed per unit time—while still giving users poor **response time**.

That happens because throughput cares about:

> “How much total work gets finished?”

but users often care about:

> “How quickly does my request get a visible response?”

For example, a scheduler might keep the CPU busy running long compute-heavy jobs because that reduces overhead and completes lots of work efficiently. But if an interactive task—like a keypress, mouse click, or browser request—has to wait behind those jobs, the system feels sluggish.

So the system may be doing a lot of work overall, but the user experiences delays.

In short:

- **High throughput** = many tasks completed efficiently.
- **Good responsiveness** = short delay for user-visible actions.
- A scheduler optimized only for throughput may sacrifice responsiveness and fairness, making the system feel slow even when it is technically productive.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `9d5edc0692b990f9`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `n/a `

```text
browser’s packets would have only a minimal impact on the dow nload speed and a large
impact on the perceived responsiveness of the system.
7.1.4 Max-Min Fairness
In many settings, a fair allocation of resources is as important to the design of a scheduler as
responsiveness and low overhead. On a multi-user machine or on a server, we do n ot want to
allow a single user to be able to monopolize the resources of the machine, degrading service
for other users. While it might seem that fairness has little value in single-user machines,
individual applications are often written by different companies, each with an interest in
making their application performance look good e ven if that comes at a cost of degrading
responsiveness for other applications.
```

#### Chunk 2

- Chunk ID: `d7027a807c6db7f6`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `207`
- Score: `n/a `

```text
for multiple user requests or tasks. For example, in a word processor, each character typed is an individual user
request to add that character to the file and display the result on the screen.
Response time (or delay). The user-perceived time to do some task.
Predictability. Low variance in response times for repeated requests.
Throughput. The rate at which tasks are completed.
Scheduling overhead. The time to switch from one task to another.
Fairness. Equality in the number and timeliness of resources given to each task.
Starvation. The lack of progress for one task, due to resources given to a higher priority task.
Chapter roadmap:
Uniprocessor Scheduling. How do u niprocessor scheduling policies affect fairness,
response time, and throughput? (Section 7.1)
```

#### Chunk 3

- Chunk ID: `149f31d47200fa99`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `205`
- Score: `n/a `

```text
improving user-perceived response time. Advertising that your operating system uses the
same scheduling algorithm as the DMV is probably not going to increase your sales!
You might think that the answer to this question is unimportant. With the million-fold
improvement in processor performance over the past thirty years, it might seem that we are a
million times less likely to have anything waiting for its turn on a processor. We disagree!
Server operating systems in particular are often overloaded. Parallel applications can create
more work than processors, and if care is not taken in the design of the scheduling policy,
performance can badly degrade. There are subtle relationships between scheduling policy
and energy management on battery-powered devices such as smartphones and laptops.
```

#### Chunk 4

- Chunk ID: `548da36b62b9a80f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `252`
- Score: `n/a `

```text
More sophisticated scheduling can help at low to moderate load, bu t if the load is more than
system can handle, response time will spike, even for short tasks.
The key idea in overload management is to design your system to do l ess work when
overloaded. This will seem strange! After all, you want your system to work a particular
way; how can you cripple the user’s experience just when your system becomes popu lar?
Under overload conditions, however, your system is incapable of serving all of the requests
in the normal way. The only question is: do y ou choose what to disable, or do y ou let events
choose for you?
An obvi ous step is to simply reject some requests in order to preserve reasonable response
```

#### Chunk 5

- Chunk ID: `9eb0d5a7a4a7804c`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `225`
- Score: `n/a `

```text
scheduled, increasing overhead.
I/O. Many parallel applications do I/O, and this can cause problems if the operating
system scheduler is oblivious to the application decomposition into parallel work. If a
read or write request blocks in the kernel, the thread blocks as well. To reuse the
processor while the thread is waiting, the application program must have created more
threads than processors, so that the scheduler can have an extra one to run in place of the
blocked thread. However, if the thread doe s not block (e.g., on a file read when the file
is cached in memory), that means that the scheduler has more threads than processors,
and so needs to do t ime slicing to multiplex threads onto processors — c ausing all of the
problems we have listed above .
Gang Scheduling
```

### Method C

- Retrieval latency: 0.540s
- Generation latency: 7.276s

**Answer:**

A scheduler can maximize **throughput** while still giving poor **response time**.

- **Throughput** = how much total work the system completes per unit time.
- **User-perceived speed** usually depends on **latency/response time** = how long a user waits before seeing a reaction.

So a scheduler might keep the CPU very busy and finish many tasks overall, but if it lets interactive tasks wait behind long CPU-heavy jobs, the system feels slow.

Example:

```text
Task A: long background computation
Task B: short UI click response
```

A throughput-oriented scheduler may keep running Task A because it uses the CPU efficiently. But the user only cares that Task B responds quickly. If Task B waits, the system feels laggy even though total work completed is high.

This is why “fair” or throughput-efficient policies, like doing work strictly in arrival order, can still produce bad perceived responsiveness. Short interactive tasks may get stuck behind long tasks.

In short:

> Maximizing throughput optimizes total completed work, not necessarily how quickly users get feedback.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bc2d066df4bcc681`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `205`
- Score: `-0.674569 rerank_score`

```text
released. W hen there are more runnable threads than processors, the processor scheduling
policy determines which threads to run first.
You might think the answer to this question is easy: just do the work in the order in which it
arrives. After all, that seems to be the only fair thing to do. B ecause it is obvi ously fair,
almost all government services work this way. When you go to your local Department of
Motor Vehicles (DMV) to get a driver’s license, you take a number and wait your turn.
Although fair, the DMV often feels slow. There’s a reason why: as we’ll see later in this
chapter, doing things in order of arrival is sometimes the worst thing you can do in terms of
improving user-perceived response time. Advertising that your operating system uses the
```

#### Chunk 2

- Chunk ID: `ac57bb031498500e`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `235`
- Score: `-1.21047 rerank_score`

```text
its original state, and the processor is re-assigned to the high priority, waiting, task.
7.5 Queueing Theory
Suppos e you build a new web service, and the week before you are to take it live, you test it
to see whether it will have reasonable response time. If your tests show that the performance
is terrible, what then? Is it because the implementation is too slow? Perhaps you have the
wrong scheduler? Quick, let’s re-implement that linked list with a hash table! And add m ore
levels to the multi-level feedback queue! Our advice: don’t panic. In this section, we
consider a third pos sibility, an effect that often trumps all of the others: response time
depends non-linearly on the rate that tasks arrive at a system. Understanding this relationship
is the topic of queueing theory.
```

#### Chunk 3

- Chunk ID: `674e8ef577b87bcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `99`
- Score: `-1.5168 rerank_score`

```text
processes. As we add w ork to the system, throughput increases as long as there is enough
processing capacity and I/O bandwidth. When we reach the point where there are too m any
tasks to fit entirely in memory, the system starts demand paging. Throughput can continue to
improve if there are enough lightly used pages to make room for new tasks, but eventually
throughput levels off and then falls off a cliff. In the limit, every instruction will trigger a page
fault, meaning that the processor executes at 100 i nstructions per second, rather than 10
billion instructions per second. Needless to say, the user will think the system is dead even if
it is in fact inching forward very slowly.
As we explained in the Chapter 7 discussion on overload control, the only way to achieve
```

#### Chunk 4

- Chunk ID: `548da36b62b9a80f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `252`
- Score: `-2.02308 rerank_score`

```text
More sophisticated scheduling can help at low to moderate load, bu t if the load is more than
system can handle, response time will spike, even for short tasks.
The key idea in overload management is to design your system to do l ess work when
overloaded. This will seem strange! After all, you want your system to work a particular
way; how can you cripple the user’s experience just when your system becomes popu lar?
Under overload conditions, however, your system is incapable of serving all of the requests
in the normal way. The only question is: do y ou choose what to disable, or do y ou let events
choose for you?
An obvi ous step is to simply reject some requests in order to preserve reasonable response
```

#### Chunk 5

- Chunk ID: `9d5edc0692b990f9`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `-2.31466 rerank_score`

```text
browser’s packets would have only a minimal impact on the dow nload speed and a large
impact on the perceived responsiveness of the system.
7.1.4 Max-Min Fairness
In many settings, a fair allocation of resources is as important to the design of a scheduler as
responsiveness and low overhead. On a multi-user machine or on a server, we do n ot want to
allow a single user to be able to monopolize the resources of the machine, degrading service
for other users. While it might seem that fairness has little value in single-user machines,
individual applications are often written by different companies, each with an interest in
making their application performance look good e ven if that comes at a cost of degrading
responsiveness for other applications.
```

## q20

**Question:** If round robin gives every job a turn, why isn’t it always the fairest or best scheduling policy?

### Method A

- Retrieval latency: 0.685s
- Generation latency: 7.679s

**Answer:**

Round Robin *feels* fair because every ready job gets a turn, but “everyone gets a turn” is not always the same as “best” or even “fair” in a useful sense.

Key reasons:

1. **It can make all jobs finish later**
   If several jobs arrive at the same time and are about the same length, Round Robin keeps switching among them:

   ```text
   A, B, C, A, B, C, A, B, C ...
   ```

   So they all finish around the same time. Under FIFO, one job might finish early, then the next, then the next. The average completion/response time can be better with FIFO.

2. **It adds context-switching overhead**
   Every time the CPU switches from one job to another, the OS spends time doing scheduling work instead of useful computation. If the time quantum is too small, this overhead becomes significant.

3. **Equal turns are not always equal fairness**
   An I/O-bound process may only need the CPU briefly before waiting for input/output again. A compute-bound process can use the CPU constantly. Round Robin gives them equal chances, but the effect is not equal: the I/O-bound job may be slowed down more noticeably.

4. **Different workloads need different policies**
   Round Robin is good when you want predictable progress for all tasks, such as interactive systems or streaming-like workloads. But if job lengths are predictable, policies like Shortest Job First can give much better average response time.

So the main idea is:

> Round Robin is fair in the sense that every job gets access to the CPU, but it is not always optimal for response time, completion time, overhead, or deeper notions of fairness.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `faa15ae2cae026ad`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `2.09242 rerank_score`

```text
Figure 7.3: Completion times with Round Robin (top) versus FIFO and SJF (bottom) when scheduling equal length tasks.
Unfortunately, Round Robin has some weaknesses. Figure 7.3 illustrates what happens for
FIFO, SJF, and Round Robin when several tasks start at roughly same time and are of the
same length. Round Robin will rotate through the tasks, doing a bit of each, finishing them all
at roughly the same time. This is nearly the worst possible scheduling policy for this
workload! FIFO does much better, picking a task and sticking with it until it finishes. Not only
does FIFO reduce average response time for this workload relative to Round Robin, no task
is worse off under FIFO — e very task finishes at least as early as it would have under Round
```

#### Chunk 2

- Chunk ID: `2613fc9ed2ff1eed`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `1.7283 rerank_score`

```text
are optimal for some workloads and pessimal for others, just different ones in each case.
Round Robin and streaming video
Round Robin is sometimes the best policy even when all tasks are roughly the same size. An example is managing the server
bandwidth for streaming video. When streaming, response time is much less of a concern than achieving a predictable, stable
rate of progress. For this, Round Robin is nearly ideal: all streams progress at the same rate. As long as Round Robin serves
the data as fast or faster than the viewer consumes the video stream, the time to completely download the stream is
unimportant.
```

#### Chunk 3

- Chunk ID: `2fc14e50cc4fa27a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `1.07927 rerank_score`

```text
What happens to the response time curve for other scheduling policies? It depends on the
burstiness and predictability of the workload.
If the distribution of arrivals or service times is less bursty than an exponential (e.g., evenly
spaced or Gaussian), FIFO will deliver nearly optimal response times, while Round Robin
will perform worse than FIFO.
If task service times are exponentially distributed but individual task times are unpredictable,
the average response time is the exactly the same for Round Robin as for FIFO. With a
memoryless distribution, every queued task has the same expected remaining service time, so
switching among tasks has no impact other than to increase overhead.
On the other hand, if task lengths can be predicted and there is variability of service times,
```

#### Chunk 4

- Chunk ID: `e7332601ee348be2`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `211`
- Score: `1.07352 rerank_score`

```text
pages, the aggregate bandwidth for small pages is low, so requests to large pages are not significantly slowed down. The only
difficulty comes when the web server is overloaded, because then the large page requests can be starved. As we will see
later, overload situations need their own set of solutions.
7.1.3 Round Robin
A policy that addresses starvation is to schedule tasks in a round robin fashion. With Round
Robin, tasks take turns running on the processor for a limited period of  time. The scheduler
assigns the processor to the first task in the ready list, setting a timer interrupt for some delay,
called the time quant um. At the end of the quantum, if the task has not completed, the task is
```

#### Chunk 5

- Chunk ID: `80f1dedd7f143dbf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `0.517125 rerank_score`

```text
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
One possible answer is to say that whatever Round Robin does is fair — a fter all, each
process gets an equal chance at the processor. As we saw above , however, Round Robin can
result in I/O-bound processes running at a much slower rate than they would if they had the
processor to themselves, while compute-bound processes are barely affected at all. That
hardly seems fair!
While there are many possible definitions of fairness, a particularly useful one is called max-
min fairness. Max-min fairness iteratively maximizes the minimum allocation given to a
particular process (user, application or thread) until all resources are assigned.
```

### Method B

- Retrieval latency: 0.691s
- Generation latency: 9.629s

**Answer:**

Round Robin *feels* fair because every job gets a turn, but “equal turns” is not always the same as “fair” or “best.”

Key reasons:

1. **It can make everyone finish later**
   If several jobs arrive at the same time and are about the same length, Round Robin keeps switching between them:

   ```text
   A B C A B C A B C ...
   ```

   So all jobs finish at roughly the same time. Under FIFO, job A could finish first, then B, then C. That gives a better average response/finish time, and no job necessarily benefits from the constant switching.

2. **Context switching has overhead**
   Each time the CPU switches from one process to another, the OS spends time doing scheduling work instead of useful work. If the time slice is small, this overhead can become significant.

3. **Equal CPU turns may not mean equal progress**
   Some processes are **CPU-bound** and can use all the CPU time they get. Others are **I/O-bound** and frequently block waiting for input/output.

   Round Robin gives them equal chances, but the I/O-bound process may still make slower progress than it would under a smarter policy. So equal treatment is not always fair treatment.

4. **Different goals require different policies**
   “Best” depends on what you care about:

   - For low average completion time: **SJF** is often better.
   - For simple batch workloads: **FIFO** may be better.
   - For interactive systems: **Round Robin** can be useful.
   - For streaming/video bandwidth: Round Robin can be very good because it gives steady progress to each stream.

So Round Robin is fair in the simple sense of “everyone gets a turn,” but not always fair in terms of response time, completion time, efficiency, or actual progress.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `faa15ae2cae026ad`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `n/a `

```text
Figure 7.3: Completion times with Round Robin (top) versus FIFO and SJF (bottom) when scheduling equal length tasks.
Unfortunately, Round Robin has some weaknesses. Figure 7.3 illustrates what happens for
FIFO, SJF, and Round Robin when several tasks start at roughly same time and are of the
same length. Round Robin will rotate through the tasks, doing a bit of each, finishing them all
at roughly the same time. This is nearly the worst possible scheduling policy for this
workload! FIFO does much better, picking a task and sticking with it until it finishes. Not only
does FIFO reduce average response time for this workload relative to Round Robin, no task
is worse off under FIFO — e very task finishes at least as early as it would have under Round
```

#### Chunk 2

- Chunk ID: `2fc14e50cc4fa27a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `n/a `

```text
What happens to the response time curve for other scheduling policies? It depends on the
burstiness and predictability of the workload.
If the distribution of arrivals or service times is less bursty than an exponential (e.g., evenly
spaced or Gaussian), FIFO will deliver nearly optimal response times, while Round Robin
will perform worse than FIFO.
If task service times are exponentially distributed but individual task times are unpredictable,
the average response time is the exactly the same for Round Robin as for FIFO. With a
memoryless distribution, every queued task has the same expected remaining service time, so
switching among tasks has no impact other than to increase overhead.
On the other hand, if task lengths can be predicted and there is variability of service times,
```

#### Chunk 3

- Chunk ID: `2613fc9ed2ff1eed`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `n/a `

```text
are optimal for some workloads and pessimal for others, just different ones in each case.
Round Robin and streaming video
Round Robin is sometimes the best policy even when all tasks are roughly the same size. An example is managing the server
bandwidth for streaming video. When streaming, response time is much less of a concern than achieving a predictable, stable
rate of progress. For this, Round Robin is nearly ideal: all streams progress at the same rate. As long as Round Robin serves
the data as fast or faster than the viewer consumes the video stream, the time to completely download the stream is
unimportant.
```

#### Chunk 4

- Chunk ID: `80f1dedd7f143dbf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `n/a `

```text
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
One possible answer is to say that whatever Round Robin does is fair — a fter all, each
process gets an equal chance at the processor. As we saw above , however, Round Robin can
result in I/O-bound processes running at a much slower rate than they would if they had the
processor to themselves, while compute-bound processes are barely affected at all. That
hardly seems fair!
While there are many possible definitions of fairness, a particularly useful one is called max-
min fairness. Max-min fairness iteratively maximizes the minimum allocation given to a
particular process (user, application or thread) until all resources are assigned.
```

#### Chunk 5

- Chunk ID: `46cbf12b34eb135f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `n/a `

```text
is worse off under FIFO — e very task finishes at least as early as it would have under Round
Robin. Time slicing added ove rhead without any benefit. Finally, consider what SJF does on
this workload. SJF schedules tasks in exactly the same order as FIFO. The first task that
arrives will be assigned the processor, and as soon as it executes a single instruction, it will
have less time remaining than all of the other tasks, and so it will run to completion. Since we
know SJF is optimal for average response time, this means that both FIFO and Round Robin
are optimal for some workloads and pessimal for others, just different ones in each case.
Round Robin and streaming video
```

### Method C

- Retrieval latency: 0.394s
- Generation latency: 11.173s

**Answer:**

Round Robin *feels* fair because every job gets a turn, but “equal turns” is not always the same as “best” or even “fair” in outcome.

Key reasons:

1. **It can make all jobs finish later**
   If several equal-length jobs arrive at the same time, Round Robin gives each a small slice repeatedly.  
   That means none of them finish until near the end.

   With FIFO, one job runs to completion, then the next, etc. Some jobs finish much earlier, and in that workload no job finishes later than it would under Round Robin.

2. **Context switching adds overhead**
   Every time the CPU switches from one job to another, there is a cost.  
   If switching does not improve response time or fairness, Round Robin is just adding extra overhead.

3. **Equal CPU slices do not mean equal usefulness**
   An I/O-bound process may only need a little CPU before waiting for input/output again.  
   A CPU-bound process can use every slice fully.

   So Round Robin may give both “equal turns,” but the I/O-bound process can still make much slower progress than it ideally could.

4. **“Best” depends on the goal**
   Different scheduling policies optimize different things:

   - **Round Robin**: good for responsiveness and steady progress
   - **FIFO**: can be better when jobs are similar and arrive together
   - **SJF/STCF**: often better for minimizing average response time if job lengths are known or predictable
   - **Fair-share/max-min fairness**: better if the goal is fair allocation among users or processes

So Round Robin is fair in a simple sense: everyone gets a chance.  
But it is not always fair in terms of progress, waiting time, completion time, or resource efficiency.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `faa15ae2cae026ad`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `0.775179 vector_distance`

```text
Figure 7.3: Completion times with Round Robin (top) versus FIFO and SJF (bottom) when scheduling equal length tasks.
Unfortunately, Round Robin has some weaknesses. Figure 7.3 illustrates what happens for
FIFO, SJF, and Round Robin when several tasks start at roughly same time and are of the
same length. Round Robin will rotate through the tasks, doing a bit of each, finishing them all
at roughly the same time. This is nearly the worst possible scheduling policy for this
workload! FIFO does much better, picking a task and sticking with it until it finishes. Not only
does FIFO reduce average response time for this workload relative to Round Robin, no task
is worse off under FIFO — e very task finishes at least as early as it would have under Round
```

#### Chunk 2

- Chunk ID: `2fc14e50cc4fa27a`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `0.808093 vector_distance`

```text
What happens to the response time curve for other scheduling policies? It depends on the
burstiness and predictability of the workload.
If the distribution of arrivals or service times is less bursty than an exponential (e.g., evenly
spaced or Gaussian), FIFO will deliver nearly optimal response times, while Round Robin
will perform worse than FIFO.
If task service times are exponentially distributed but individual task times are unpredictable,
the average response time is the exactly the same for Round Robin as for FIFO. With a
memoryless distribution, every queued task has the same expected remaining service time, so
switching among tasks has no impact other than to increase overhead.
On the other hand, if task lengths can be predicted and there is variability of service times,
```

#### Chunk 3

- Chunk ID: `2613fc9ed2ff1eed`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `0.827246 vector_distance`

```text
are optimal for some workloads and pessimal for others, just different ones in each case.
Round Robin and streaming video
Round Robin is sometimes the best policy even when all tasks are roughly the same size. An example is managing the server
bandwidth for streaming video. When streaming, response time is much less of a concern than achieving a predictable, stable
rate of progress. For this, Round Robin is nearly ideal: all streams progress at the same rate. As long as Round Robin serves
the data as fast or faster than the viewer consumes the video stream, the time to completely download the stream is
unimportant.
```

#### Chunk 4

- Chunk ID: `46cbf12b34eb135f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `214`
- Score: `0.856449 vector_distance`

```text
is worse off under FIFO — e very task finishes at least as early as it would have under Round
Robin. Time slicing added ove rhead without any benefit. Finally, consider what SJF does on
this workload. SJF schedules tasks in exactly the same order as FIFO. The first task that
arrives will be assigned the processor, and as soon as it executes a single instruction, it will
have less time remaining than all of the other tasks, and so it will run to completion. Since we
know SJF is optimal for average response time, this means that both FIFO and Round Robin
are optimal for some workloads and pessimal for others, just different ones in each case.
Round Robin and streaming video
```

#### Chunk 5

- Chunk ID: `80f1dedd7f143dbf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `0.860744 vector_distance`

```text
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
One possible answer is to say that whatever Round Robin does is fair — a fter all, each
process gets an equal chance at the processor. As we saw above , however, Round Robin can
result in I/O-bound processes running at a much slower rate than they would if they had the
processor to themselves, while compute-bound processes are barely affected at all. That
hardly seems fair!
While there are many possible definitions of fairness, a particularly useful one is called max-
min fairness. Max-min fairness iteratively maximizes the minimum allocation given to a
particular process (user, application or thread) until all resources are assigned.
```

## q21

**Question:** Why can shortest-job-first reduce average waiting time even though it seems unfair to long jobs?

### Method A

- Retrieval latency: 0.715s
- Generation latency: 6.435s

**Answer:**

Shortest-job-first (SJF) can reduce **average waiting time** because short jobs get completed quickly instead of sitting behind long jobs.

The key idea is:

> If a short job waits behind a long job, its waiting time increases a lot relative to how little CPU time it needs.  
> If a long job waits behind a short job, its waiting time only increases a little.

Example:

- Job A: 10 seconds
- Job B: 1 second
- Job C: 1 second

If we run the long job first:

```text
A → B → C
```

Waiting times:

- A waits 0
- B waits 10
- C waits 11

Average waiting time:

```text
(0 + 10 + 11) / 3 = 7
```

If we run shortest jobs first:

```text
B → C → A
```

Waiting times:

- B waits 0
- C waits 1
- A waits 2

Average waiting time:

```text
(0 + 1 + 2) / 3 = 1
```

So SJF improves the average because many short jobs finish quickly, and the long job is delayed only by a small amount.

But you are right that it can be **unfair to long jobs**. If short jobs keep arriving, a long job may keep getting postponed. This is called **starvation**. So SJF is good for minimizing average waiting/response time, but not necessarily good for fairness.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `8aeb4c452c6d9365`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `n/a `

```text
the scheduler will preempt the current task, and start the shorter one. The remaining short
tasks will be processed in order of arrival, followed by finishing the long task.
What counts as “shortest” is the remaining time left on the task, not its original length. If we
are one nanosecond away from finishing an hour-long task, we will minimize average
response time by staying with that task, rather than preempting it for a minute long task that
just arrived on the ready list. Of course, if they both arrive at about the same time, doing the
minute long task first will dramatically improve average response time.
Starvation and sample bias
Systems that might suffer from starvation require extra care when being measured. Suppose you want to compare FIFO and
```

#### Chunk 2

- Chunk ID: `7857ba59b08750ee`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `n/a `

```text
On the other hand, if task lengths can be predicted and there is variability of service times,
Shortest Job First can improve average response time, particularly if arrivals are bursty.
Many real-world systems exhibit more bursty arrivals or service times than an exponential
distribution. A bursty distribution is sometimes called heavy-tailed because it has more very
long tasks; since the mean rate is the same, this also implies that the distribution has even
more very short tasks. For example, web page size is heavy-tailed; so is the processing time
per web page. Process execution times on desktop computers are also heavy-tailed. For these
types of systems, burstiness results in worse average response time than would be predicted
```

#### Chunk 3

- Chunk ID: `cf2f869922d29f34`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `n/a `

```text
7.1.2 Shortest Job First (SJF)
If FIFO can be a poor  choice for average response time, is there an optimal policy for
minimizing average response time? The answer is yes: schedule the shortest job first (SJF).
Suppos e we could know how much time each task needed at the processor. (In general, we
will not know, so this is not meant as a practical policy! Rather, we use it as a thought
experiment; later on, we will see how to approximate SJF in practice.) If we always schedule
the task that has the least remaining work to do, t hat will minimize average response time.
(For this reason, some call SJF shortest-remaining-time-first or SRTF.)
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
```

#### Chunk 4

- Chunk ID: `00d08acc6b00c102`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `n/a `

```text
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
we think might be optimal. Because the alternative is not SJF, at some point it will choose to
run a task that is longer than something else in the queue. If we now switch the order of tasks,
keeping everything the same, but doing the shorter task first, we will reduce the average
response time. Thus, any alternative to SJF cannot be optimal.
Figure 7.1 illustrates SJF on the same example we used for FIFO. If a long task is the first to
arrive, it will be scheduled (if we are work-conserving). When a short task arrives a bit later,
the scheduler will preempt the current task, and start the shorter one. The remaining short
```

#### Chunk 5

- Chunk ID: `64ce91e1670a166e`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `209`
- Score: `n/a `

```text
Figure 7.1: Completion times with FIFO (top) and SJF (bottom) scheduling when several short tasks (2-5) arrive
immediately after a long task (1).
Unfortunately, FIFO has a weakness. If a task with very little work to do h appens to land in
line behind a task that takes a very long time, then the system will seem very inefficient.
Figure  7.1 illustrates a particularly bad workload for FIFO; it also shows SJF, which we
will discuss in a bit. If the first task in the queue takes one second, and the next four arrive an
instant later, but each only needs a millisecond of the processor, then they will all need to
wait until the first one finishes. The average response time will be over a second, bu t the
optimal average response time is much less than that. In fact, if we ignore switching
```

### Method B

- Retrieval latency: 0.450s
- Generation latency: 6.307s

**Answer:**

Shortest-job-first (SJF) reduces **average waiting time** because it gives priority to jobs that can finish quickly, so many jobs spend very little time waiting.

The key idea is:

> Making one long job wait a little longer may reduce the waiting time of many short jobs by a lot.

Example:

Suppose three jobs arrive together:

- Job A: 10 seconds
- Job B: 1 second
- Job C: 1 second

If we run the long job first:

```text
A → B → C
```

Waiting times:

- A waits 0
- B waits 10
- C waits 11

Average waiting time:

```text
(0 + 10 + 11) / 3 = 7
```

If we use shortest-job-first:

```text
B → C → A
```

Waiting times:

- B waits 0
- C waits 1
- A waits 2

Average waiting time:

```text
(0 + 1 + 2) / 3 = 1
```

So the average is much lower.

The unfairness is that long jobs may keep getting delayed if new short jobs keep arriving. That is called **starvation**. So SJF is good for minimizing average waiting/response time, but it can be bad for fairness.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `9682e0f93ed3d65d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `211`
- Score: `5.11528 rerank_score`

```text
fundamental tradeoff between reducing average response time and reducing the variance in
average response time.
Worse, SJF can suffer from starvation and frequent context switches. If enough short tasks
arrive, long tasks may never complete. Whenever a new task on the ready list is shorter than
the remaining time left on the currently scheduled task, the scheduler will switch to the new
task. If this keeps happening indefinitely, a long task may never finish.
Suppos e a supermarket manager reads a portion of this textbook  and decides to implement
shortest job first to reduce average waiting times. The manager tells herself: who cares about
variance! A benefit is that there would no longer be any need for express lanes — if someone
```

#### Chunk 2

- Chunk ID: `cf2f869922d29f34`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `3.16787 rerank_score`

```text
7.1.2 Shortest Job First (SJF)
If FIFO can be a poor  choice for average response time, is there an optimal policy for
minimizing average response time? The answer is yes: schedule the shortest job first (SJF).
Suppos e we could know how much time each task needed at the processor. (In general, we
will not know, so this is not meant as a practical policy! Rather, we use it as a thought
experiment; later on, we will see how to approximate SJF in practice.) If we always schedule
the task that has the least remaining work to do, t hat will minimize average response time.
(For this reason, some call SJF shortest-remaining-time-first or SRTF.)
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
```

#### Chunk 3

- Chunk ID: `7857ba59b08750ee`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `2.66868 rerank_score`

```text
On the other hand, if task lengths can be predicted and there is variability of service times,
Shortest Job First can improve average response time, particularly if arrivals are bursty.
Many real-world systems exhibit more bursty arrivals or service times than an exponential
distribution. A bursty distribution is sometimes called heavy-tailed because it has more very
long tasks; since the mean rate is the same, this also implies that the distribution has even
more very short tasks. For example, web page size is heavy-tailed; so is the processing time
per web page. Process execution times on desktop computers are also heavy-tailed. For these
types of systems, burstiness results in worse average response time than would be predicted
```

#### Chunk 4

- Chunk ID: `8aeb4c452c6d9365`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `0.381566 rerank_score`

```text
the scheduler will preempt the current task, and start the shorter one. The remaining short
tasks will be processed in order of arrival, followed by finishing the long task.
What counts as “shortest” is the remaining time left on the task, not its original length. If we
are one nanosecond away from finishing an hour-long task, we will minimize average
response time by staying with that task, rather than preempting it for a minute long task that
just arrived on the ready list. Of course, if they both arrive at about the same time, doing the
minute long task first will dramatically improve average response time.
Starvation and sample bias
Systems that might suffer from starvation require extra care when being measured. Suppose you want to compare FIFO and
```

#### Chunk 5

- Chunk ID: `00d08acc6b00c102`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `-0.134787 rerank_score`

```text
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
we think might be optimal. Because the alternative is not SJF, at some point it will choose to
run a task that is longer than something else in the queue. If we now switch the order of tasks,
keeping everything the same, but doing the shorter task first, we will reduce the average
response time. Thus, any alternative to SJF cannot be optimal.
Figure 7.1 illustrates SJF on the same example we used for FIFO. If a long task is the first to
arrive, it will be scheduled (if we are work-conserving). When a short task arrives a bit later,
the scheduler will preempt the current task, and start the shorter one. The remaining short
```

### Method C

- Retrieval latency: 0.390s
- Generation latency: 6.700s

**Answer:**

Shortest-job-first (SJF) can reduce **average waiting time** because it finishes many short jobs quickly instead of making them wait behind a long job.

The key idea is:

> If one long job and one short job are both waiting, doing the short job first usually reduces the total waiting time more than doing the long job first.

Example:

- Job A takes 10 minutes
- Job B takes 1 minute

If we run **A then B**:

- A waits 0
- B waits 10  
- Average waiting time = `(0 + 10) / 2 = 5`

If we run **B then A**:

- B waits 0
- A waits 1  
- Average waiting time = `(0 + 1) / 2 = 0.5`

So even though the long job waits a little longer, the short job’s waiting time drops a lot. Across many jobs, this lowers the average.

But you are right that it can be unfair: long jobs may be delayed again and again if short jobs keep arriving. This is called **starvation**. So SJF is good for minimizing average waiting/response time, but it can increase unfairness and variance in waiting time.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `cf2f869922d29f34`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `0.66019 vector_distance`

```text
7.1.2 Shortest Job First (SJF)
If FIFO can be a poor  choice for average response time, is there an optimal policy for
minimizing average response time? The answer is yes: schedule the shortest job first (SJF).
Suppos e we could know how much time each task needed at the processor. (In general, we
will not know, so this is not meant as a practical policy! Rather, we use it as a thought
experiment; later on, we will see how to approximate SJF in practice.) If we always schedule
the task that has the least remaining work to do, t hat will minimize average response time.
(For this reason, some call SJF shortest-remaining-time-first or SRTF.)
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
```

#### Chunk 2

- Chunk ID: `9682e0f93ed3d65d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `211`
- Score: `0.690052 vector_distance`

```text
fundamental tradeoff between reducing average response time and reducing the variance in
average response time.
Worse, SJF can suffer from starvation and frequent context switches. If enough short tasks
arrive, long tasks may never complete. Whenever a new task on the ready list is shorter than
the remaining time left on the currently scheduled task, the scheduler will switch to the new
task. If this keeps happening indefinitely, a long task may never finish.
Suppos e a supermarket manager reads a portion of this textbook  and decides to implement
shortest job first to reduce average waiting times. The manager tells herself: who cares about
variance! A benefit is that there would no longer be any need for express lanes — if someone
```

#### Chunk 3

- Chunk ID: `8aeb4c452c6d9365`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `0.698109 vector_distance`

```text
the scheduler will preempt the current task, and start the shorter one. The remaining short
tasks will be processed in order of arrival, followed by finishing the long task.
What counts as “shortest” is the remaining time left on the task, not its original length. If we
are one nanosecond away from finishing an hour-long task, we will minimize average
response time by staying with that task, rather than preempting it for a minute long task that
just arrived on the ready list. Of course, if they both arrive at about the same time, doing the
minute long task first will dramatically improve average response time.
Starvation and sample bias
Systems that might suffer from starvation require extra care when being measured. Suppose you want to compare FIFO and
```

#### Chunk 4

- Chunk ID: `00d08acc6b00c102`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `210`
- Score: `0.741994 vector_distance`

```text
To see that SJF is optimal, consider a hypothetical alternative policy that is not SJF, but that
we think might be optimal. Because the alternative is not SJF, at some point it will choose to
run a task that is longer than something else in the queue. If we now switch the order of tasks,
keeping everything the same, but doing the shorter task first, we will reduce the average
response time. Thus, any alternative to SJF cannot be optimal.
Figure 7.1 illustrates SJF on the same example we used for FIFO. If a long task is the first to
arrive, it will be scheduled (if we are work-conserving). When a short task arrives a bit later,
the scheduler will preempt the current task, and start the shorter one. The remaining short
```

#### Chunk 5

- Chunk ID: `7857ba59b08750ee`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `249`
- Score: `0.770548 vector_distance`

```text
On the other hand, if task lengths can be predicted and there is variability of service times,
Shortest Job First can improve average response time, particularly if arrivals are bursty.
Many real-world systems exhibit more bursty arrivals or service times than an exponential
distribution. A bursty distribution is sometimes called heavy-tailed because it has more very
long tasks; since the mean rate is the same, this also implies that the distribution has even
more very short tasks. For example, web page size is heavy-tailed; so is the processing time
per web page. Process execution times on desktop computers are also heavy-tailed. For these
types of systems, burstiness results in worse average response time than would be predicted
```

## q22

**Question:** If a machine has multiple CPUs, why can’t the operating system just keep every thread on whichever CPU is free at the moment?

### Method A

- Retrieval latency: 0.904s
- Generation latency: 7.107s

**Answer:**

It *can* move threads to any free CPU, but doing that all the time is often inefficient.

The main reason is **processor/cache affinity**:

- When a thread runs on a CPU, that CPU’s caches fill with the thread’s code and data.
- If the OS later runs the same thread on the **same CPU**, much of that cached data may still be useful.
- If the OS moves the thread to a **different CPU**, the new CPU may not have that data cached, so the thread suffers more cache misses and runs slower.

So modern OSes often prefer:

> “If a thread ran on CPU 2 before, try to run it on CPU 2 again.”

This is called **affinity scheduling**.

There is also a scheduling overhead issue. On multiprocessor systems, OSes often keep **per-CPU run queues** instead of one global queue. That reduces contention between CPUs, because each CPU mostly manages its own work.

The tradeoff is:

- Keeping threads on the same CPU improves cache reuse.
- Moving threads around improves load balancing.

So the OS usually does **both**:

- Prefer the same CPU when possible.
- Migrate threads only when imbalance is persistent enough to justify the cache cost.

In short: the OS does not simply use “whichever CPU is free” because moving threads freely can waste cache locality and add scheduling overhead.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b0186d060a32586b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `222`
- Score: `n/a `

```text
For these reasons, commercial operating systems such as Linux use a per-processor data
structure: a separate copy of the multi-level feedback queue for each processor. Figure 7.6
illustrates this approach.
Each processor uses affinity scheduling: once a thread is scheduled on a processor, it is
returned to the same processor when it is re-scheduled, maximizing cache reuse. Each
processor looks at its own copy of the queue for new work to do;  this can mean that some
processors can idle while others have work waiting to be done. Rebalancing occurs only if
the queue lengths are persistent enough to compensate for the time to reload the cache for the
migrated threads. Because rebalancing is possible, the per-processor data structures must
```

#### Chunk 2

- Chunk ID: `c7518e3198b2fab0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `n/a `

```text
limited number of processors (and pot entially only one!). The operating system’s job is to
provide the illusion of a nearly infinite number of virtual processors even while the physical
hardware is more limited. It sustains this illusion by transparently suspending and resuming
threads so that at any given time only a subset of the threads are actively running.
```

#### Chunk 3

- Chunk ID: `a3cdad82174f7d5d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `n/a `

```text
Parallel programs need to be able to map work onto multiple processors to get the
performance benefits of multicore architectures.
Data management systems need concurrency to mask the latency of disk and network
operations.
From the programmer’s perspective, it is much easier to think sequentially than to keep track
of many simultaneous activities. For example, when reading or writing the code for a
procedure, you can identify an initial state and a set of pre-conditions, think through how each
successive statement changes the state, and from that determine the post-conditions. How can
you write a correct program with dozens of events happening at once?
Figure 4.1: The operating system provides the illusion that programmers can create as many threads as they need, and each
```

#### Chunk 4

- Chunk ID: `0ba2e7971db0b21d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `158`
- Score: `n/a `

```text
number of processors. Each thread uses the hash table based on the processor where it is
currently running. Each hash table still needs its own lock in case a thread is context switched
in the middle of an operation, but in the common case, only threads running on the same
processor contend for the same lock.
```

#### Chunk 5

- Chunk ID: `6d38c99a40688be5`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `47`
- Score: `n/a `

```text
running thread.
Regardless, the thread system must save the current processor state, so that when the current
thread resumes execution, it appears to the thread as if the event never occurred except for
some time having elapsed. This provides the abstraction of thread execution on a virtual
processor with unpredictable and variable speed.
To keep things simple, we do n ot want to do a n involuntary context switch while we are in
the middle of a voluntary one. When switching between two threads, we need to temporarily
defer interrupts until the switch is complete, to avoid confusion. Processors contain
privileged instructions to defer and re-enable interrupts; we make use of these in our
implementation below.
Why is it necessary to turn off interrupts during thread switch?
```

### Method B

- Retrieval latency: 0.726s
- Generation latency: 10.462s

**Answer:**

It mostly *does* try to do that — but there are limits and tradeoffs.

A machine may have multiple CPUs, but usually there are **many more threads than CPUs**. So the OS can only run as many threads at once as there are available CPU cores/hardware threads. The rest must wait.

Also, moving threads freely between CPUs is not always ideal:

1. **A CPU may not actually be free**
   - If 8 threads are runnable but the machine has 4 CPUs, only 4 can run at once.
   - The OS must choose which ones get CPU time.

2. **Threads are not always ready to run**
   - Some are blocked waiting for disk, network, keyboard input, locks, etc.
   - A “free CPU” can only run a thread that is currently runnable.

3. **Moving a thread between CPUs has cost**
   - CPUs have caches.
   - If a thread was running on CPU 1, its data may be in CPU 1’s cache.
   - Moving it to CPU 2 may make it slower because CPU 2 has to reload that data.

4. **Threads share data**
   - If threads interact through locks or shared memory, running them on different CPUs can create synchronization overhead.
   - The OS must still reason about races, locking, and timing.

5. **Fairness and priorities matter**
   - The OS may not simply run “whoever fits.”
   - Some threads have higher priority, some need responsiveness, and some should not starve others.

So the short answer is:

> The OS does try to assign runnable threads to available CPUs, but because there are often more threads than CPUs, because threads block and wake unpredictably, and because moving threads has overhead, scheduling is more complicated than just “put each thread on any free CPU.”

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `deb1b9004b45d8e1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `28`
- Score: `1.68318 rerank_score`

```text
the processor, starving other threads and making the system’s user interface sluggish or non-responsive. Additionally, modern
multiprocessor machines run multiple threads at a time, so one would still have to reason about the possible interactions
between threads even if cooperative multi-threading were used. Thus, although cooperative multi-threading was used in some
significant systems in the past, including early versions of Apple’s MacOS operating system, it is less often used today.
The alternative we describe in this book is sometimes called preemptive multi-threading since running threads can be
switched at any time. Whenever the book uses the term “multi-threading,” it means preemptive multi-threading unless we
explicitly state otherwise.
4.2.2 Why “U npredictable Speed”?
```

#### Chunk 2

- Chunk ID: `61d751465e15c923`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `1.01048 rerank_score`

```text
Figure 4.1: The operating system provides the illusion that programmers can create as many threads as they need, and each
thread runs on its own dedicated virtual processor. In reality, of course, a machine only has a finite number of processors, and
it is the operating system’s job to transparently multiplex threads onto the actual processors.
The key idea is to write a concurrent program — on e with many simultaneous activities — a s
a set of sequential streams of execution, or threads, that interact and share results in very
precise ways. Threads let us define a set of tasks that run concurrently while the code for
each task is sequential. Each thread behaves as if it has its own dedicated processor, as
```

#### Chunk 3

- Chunk ID: `a53784ec06dd87df`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `22`
- Score: `0.640667 rerank_score`

```text
system must somehow keep all of these activities separate, yet allow each the full capacity of
the machine if the others are not running. At a minimum, when one program stops running, the
operating system should let me run another. Better still, the operating system should let
multiple applications run at the same time, so I can read email while I dow nload a security
patch to the system software.
```

#### Chunk 4

- Chunk ID: `eb37e3e0a7a29b81`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `26`
- Score: `-0.306096 rerank_score`

```text
Many kernel threads. To manage complexity, shift work to the background, exploit parallelism, and hide I/O latency,
the operating system kernel itself can benefit from using multiple threads. In this case, each kernel thread runs with
the privileges of the kernel: it can execute privileged instructions, access system memory, and issue commands directly
to I/O devices. The operating system kernel itself implements the thread abstraction for its own use.
Because of the usefulness of threads, almost all modern operating systems support both multiple threads per process and
multiple kernel threads.
4.2 Thread Abstraction
Thus far, we have described what a thread is and why it is useful. Before we go farther, we
must define the thread abstraction and its properties more precisely.
```

#### Chunk 5

- Chunk ID: `c9a24201072d05d8`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `26`
- Score: `-0.67526 rerank_score`

```text
it preempts one of the running threads so the kernel can run the interrupt handler; when the handler finishes, the kernel
resumes that thread.
Many single-threaded processes. As recently as twenty years ago, many operating systems supported multiple
processes but only one thread per process. To the kernel, however, each process looks like a thread: a separate
sequence of instructions, executing sometimes in the kernel and sometimes at user level. For example, on a
multiprocessor, if multiple processes perform system calls at the same time, the kernel, in effect, has multiple threads
executing concurrently in kernel mode.
Many kernel threads. To manage complexity, shift work to the background, exploit parallelism, and hide I/O latency,
```

### Method C

- Retrieval latency: 0.203s
- Generation latency: 6.919s

**Answer:**

It *can* do that, but doing it all the time is usually inefficient.

The main reason is **cache affinity**.

When a thread runs on a CPU, that CPU’s caches may contain data the thread was recently using. If the OS later runs the same thread on the **same CPU**, the thread may reuse that cached data and continue faster.

If the OS moves the thread to a different CPU:

- the new CPU may not have the thread’s data in cache,
- the thread may suffer more cache misses,
- data may need to be reloaded or transferred,
- the old CPU’s cached data becomes less useful.

So operating systems often prefer **affinity scheduling**: once a thread has run on one CPU, try to schedule it there again.

But the OS also cares about load balancing. If one CPU is overloaded and another is idle, the OS may migrate threads. It just avoids doing that too aggressively because migration has a cost.

So the idea is:

> Use a free CPU when needed, but prefer keeping a thread on the same CPU if that gives better cache reuse.

That is why systems like Linux often use **per-processor run queues** with occasional rebalancing instead of constantly assigning every thread to any free CPU.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `61d751465e15c923`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `0.739827 vector_distance`

```text
Figure 4.1: The operating system provides the illusion that programmers can create as many threads as they need, and each
thread runs on its own dedicated virtual processor. In reality, of course, a machine only has a finite number of processors, and
it is the operating system’s job to transparently multiplex threads onto the actual processors.
The key idea is to write a concurrent program — on e with many simultaneous activities — a s
a set of sequential streams of execution, or threads, that interact and share results in very
precise ways. Threads let us define a set of tasks that run concurrently while the code for
each task is sequential. Each thread behaves as if it has its own dedicated processor, as
```

#### Chunk 2

- Chunk ID: `ce01248ab14e5f75`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `25`
- Score: `0.746602 vector_distance`

```text
returns immediately to the application. In the background, the operating system kernel
runs a separate thread to flush the modified data out to disk. Another example is on file
reads: the kernel can have a thread which attempts to anticipate which blocks are likely
to be read next (e.g., if the application is reading a large file from beginning to end), and
to bring those blocks from disk before the application asks for them.
Performance: exploiting multiple processors. Programs can use threads on a
multiprocessor to do w ork in parallel; they can do the same work in less time or more
work in the same elapsed time. Today, a server might have more than a dozen
processors; a desktop or laptop may include eight processor cores; even most
```

#### Chunk 3

- Chunk ID: `b0186d060a32586b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `222`
- Score: `0.754112 vector_distance`

```text
For these reasons, commercial operating systems such as Linux use a per-processor data
structure: a separate copy of the multi-level feedback queue for each processor. Figure 7.6
illustrates this approach.
Each processor uses affinity scheduling: once a thread is scheduled on a processor, it is
returned to the same processor when it is re-scheduled, maximizing cache reuse. Each
processor looks at its own copy of the queue for new work to do;  this can mean that some
processors can idle while others have work waiting to be done. Rebalancing occurs only if
the queue lengths are persistent enough to compensate for the time to reload the cache for the
migrated threads. Because rebalancing is possible, the per-processor data structures must
```

#### Chunk 4

- Chunk ID: `c7518e3198b2fab0`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `0.75973 vector_distance`

```text
limited number of processors (and pot entially only one!). The operating system’s job is to
provide the illusion of a nearly infinite number of virtual processors even while the physical
hardware is more limited. It sustains this illusion by transparently suspending and resuming
threads so that at any given time only a subset of the threads are actively running.
```

#### Chunk 5

- Chunk ID: `a3cdad82174f7d5d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `20`
- Score: `0.789057 vector_distance`

```text
Parallel programs need to be able to map work onto multiple processors to get the
performance benefits of multicore architectures.
Data management systems need concurrency to mask the latency of disk and network
operations.
From the programmer’s perspective, it is much easier to think sequentially than to keep track
of many simultaneous activities. For example, when reading or writing the code for a
procedure, you can identify an initial state and a set of pre-conditions, think through how each
successive statement changes the state, and from that determine the post-conditions. How can
you write a correct program with dozens of events happening at once?
Figure 4.1: The operating system provides the illusion that programmers can create as many threads as they need, and each
```

## q23

**Question:** Why does processor affinity matter if all CPUs are supposed to be equivalent?

### Method A

- Retrieval latency: 0.327s
- Generation latency: 7.555s

**Answer:**

CPUs are “equivalent” in the sense that any CPU can execute the same thread correctly.

Processor affinity matters because they are **not equivalent in current state**.

If a thread recently ran on CPU 2, then CPU 2 may still have useful data for that thread in its:

- L1/L2/L3 cache
- TLB entries
- branch predictor state
- possibly nearby NUMA memory locality

So if the OS schedules that same thread again on CPU 2, it can often continue faster because the processor cache is “warm.”

If the OS moves the thread to CPU 5, it still runs correctly, but CPU 5 may need to reload much of that data from memory or other caches. That costs time and energy.

So the key idea is:

> CPUs are functionally equivalent, but not performance-equivalent at a given moment.

That is why operating systems often use **affinity scheduling**: try to run a thread again on the same processor to maximize cache reuse.

There is still a tradeoff, though. If CPU 2 is busy and CPU 5 is idle, the OS may migrate the thread anyway to improve load balancing. So affinity is useful, but not absolute.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b0186d060a32586b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `222`
- Score: `-0.297419 rerank_score`

```text
For these reasons, commercial operating systems such as Linux use a per-processor data
structure: a separate copy of the multi-level feedback queue for each processor. Figure 7.6
illustrates this approach.
Each processor uses affinity scheduling: once a thread is scheduled on a processor, it is
returned to the same processor when it is re-scheduled, maximizing cache reuse. Each
processor looks at its own copy of the queue for new work to do;  this can mean that some
processors can idle while others have work waiting to be done. Rebalancing occurs only if
the queue lengths are persistent enough to compensate for the time to reload the cache for the
migrated threads. Because rebalancing is possible, the per-processor data structures must
```

#### Chunk 2

- Chunk ID: `71af296602ca08f4`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `255`
- Score: `-0.510874 rerank_score`

```text
resource sharing among multiple parallel applications, commercial systems are only just
now starting to deploy these ideas. It will be interesting to see how the theory works out
in practice.
Cache affinity. Over the past twenty years, processor architects have radically
increased both the size and number of levels of on-chip caches. There is little reason to
believe that this trend will reverse. Although processor clock rates are improving
slowly, transistor density is still increasing at a rapid rate. This will make it both
possible and desirable to have even larger, multi-level on-chip caches to achieve good
performance. Thus, it is likely that scheduling for cache affinity will be an even larger
factor in the future than it is today. Balancing when to respect affinity and when to
```

#### Chunk 3

- Chunk ID: `74c7aad4726a2321`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `230`
- Score: `-1.74461 rerank_score`

```text
interface hardware to be turned off more quickly once the application finishes. Because
context switching consumes both time and energy to reload processor caches, affinity
scheduling improves both performance and energy efficiency.
In most cases, however, there is a tradeoff: how should the operating system balance between
competing demands for timeliness and energy efficiency? If the user has requested maximum
responsiveness or maximum battery life, the choice is easy, but often the user wants a
reasonable tradeoff between the two.
```

#### Chunk 4

- Chunk ID: `337086551cfc3ddb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `152`
- Score: `-4.49009 rerank_score`

```text
processors because of the difficulty of improving single CPU performance. The design
of shared obj ects can have a large impact on multiprocessor performance. For example,
a lock protecting a frequently accessed shared obj ect can become a bottleneck, since
only one thread can hold the lock at a time.
Correctness. Performance considerations often cause designers to re-engineer their data
structures for increased concurrency. Splitting a single shared obj ect into a set of related
objects each with their own lock can improve performance. However, it also raises
issues of correctness. For programs with multiple shared obj ects, we face a problem
similar to the one faced when reasoning about atomic loads and stores: even if each
```

#### Chunk 5

- Chunk ID: `80f1dedd7f143dbf`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `-4.95792 rerank_score`

```text
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
One possible answer is to say that whatever Round Robin does is fair — a fter all, each
process gets an equal chance at the processor. As we saw above , however, Round Robin can
result in I/O-bound processes running at a much slower rate than they would if they had the
processor to themselves, while compute-bound processes are barely affected at all. That
hardly seems fair!
While there are many possible definitions of fairness, a particularly useful one is called max-
min fairness. Max-min fairness iteratively maximizes the minimum allocation given to a
particular process (user, application or thread) until all resources are assigned.
```

### Method B

- Retrieval latency: 0.852s
- Generation latency: 7.343s

**Answer:**

CPUs are “equivalent” in the sense that any CPU can run the same thread correctly.

But they are not equivalent in terms of **performance at a given moment**.

If a thread has recently run on CPU 2, then CPU 2 may still have useful state for that thread, such as:

- cached memory data
- cached instructions
- TLB entries / address-translation state
- nearby per-CPU scheduler data

So if the OS schedules that thread again on CPU 2, it may resume faster because much of what it needs is already “warm” in that processor’s cache.

If the OS moves the thread to CPU 5, correctness is still fine, but CPU 5 may have to reload that data from memory or other caches, causing cache misses and extra communication.

So processor affinity matters because:

> CPUs are functionally interchangeable, but their caches and recent execution history are not.

The tradeoff is that strict affinity can cause imbalance: one CPU may have many runnable threads while another is idle. So operating systems often prefer affinity, but may rebalance work when the imbalance is large enough to justify the cache cost.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b0186d060a32586b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `222`
- Score: `n/a `

```text
For these reasons, commercial operating systems such as Linux use a per-processor data
structure: a separate copy of the multi-level feedback queue for each processor. Figure 7.6
illustrates this approach.
Each processor uses affinity scheduling: once a thread is scheduled on a processor, it is
returned to the same processor when it is re-scheduled, maximizing cache reuse. Each
processor looks at its own copy of the queue for new work to do;  this can mean that some
processors can idle while others have work waiting to be done. Rebalancing occurs only if
the queue lengths are persistent enough to compensate for the time to reload the cache for the
migrated threads. Because rebalancing is possible, the per-processor data structures must
```

#### Chunk 2

- Chunk ID: `a20dfd11deee60b1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `159`
- Score: `n/a `

```text
Often, this is combined with a per-processor ready list, ensuring that each thread
preferentially runs on the same processor each time it is context switched, further improving
execution speed.
An advantage of this approach is better hardware cache behavior; as we saw in the previous
section, shared data that must be communicated between processors can slow dow n the
execution of critical sections. Of course, the disadvantage is that the hash tables are now
partitioned, so that a web page may be cached in one processor’s hash table, and needed in
another. Whether this is a performance benefit depends on the relative impact of reducing
communication of shared data versus the decreased effectiveness of the cache.
```

#### Chunk 3

- Chunk ID: `fd48fd852a20fb7d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `n/a `

```text
Even if we could ignore the issue of scheduling — e .g., if there are more processors than
threads so that each thread is assigned its own physical processor — the physical reality is
that the relative execution speed of different threads can be significantly affected by factors
outside their control. An extreme example is that the programmer may be debugging one
thread by single-stepping it, while other threads run at full speed on other processors. If the
programmer is to have any hope of understanding concurrent program behavior, the program’s
correctness cannot depend on which threads are being observed.
Variability in execution speed occurs during normal operation as well. Accessing memory
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
```

#### Chunk 4

- Chunk ID: `04628e54632b4590`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `n/a `

```text
particular user, users sharing a physical machine. For example, we could be concerned with
making sure that every thread within a process makes progress. For simplicity, however, our
discussion will assume we are interested in providing fairness among processes — the same
principles apply if the unit receiving resources is the user, application, or thread.
Fairness is easy if all processes are compute-bound: Round Robin will give each process an
equal portion of the processor. In practice, however, different processes consume resources
at different rates. An I/O-bound process may need only a small portion of the processor,
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
```

#### Chunk 5

- Chunk ID: `337086551cfc3ddb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `152`
- Score: `n/a `

```text
processors because of the difficulty of improving single CPU performance. The design
of shared obj ects can have a large impact on multiprocessor performance. For example,
a lock protecting a frequently accessed shared obj ect can become a bottleneck, since
only one thread can hold the lock at a time.
Correctness. Performance considerations often cause designers to re-engineer their data
structures for increased concurrency. Splitting a single shared obj ect into a set of related
objects each with their own lock can improve performance. However, it also raises
issues of correctness. For programs with multiple shared obj ects, we face a problem
similar to the one faced when reasoning about atomic loads and stores: even if each
```

### Method C

- Retrieval latency: 0.319s
- Generation latency: 7.581s

**Answer:**

CPUs are “equivalent” in the sense that they can run the same instructions and execute the same threads correctly.

But they are **not equivalent in current state**.

If a thread has recently run on CPU 2, then CPU 2 may already have useful state for that thread, such as:

- data in its hardware cache
- instruction cache contents
- TLB entries / address translation state
- branch predictor history
- nearby per-processor scheduler data

So if the OS schedules that thread again on CPU 2, it may run faster because much of what it needs is already “warm” in that processor’s cache.

If the OS moves the thread to CPU 5, CPU 5 can still run it correctly, but it may suffer cache misses and need to reload data from memory. That can cost hundreds or thousands of cycles.

So processor affinity matters for **performance**, not correctness.

The tradeoff is:

- Strong affinity: better cache reuse, less migration cost
- Too much affinity: one CPU may be overloaded while another is idle

That is why systems often use per-processor ready queues and only rebalance when the imbalance is large or persistent enough to justify the cache-reloading cost.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b0186d060a32586b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `222`
- Score: `0.853665 vector_distance`

```text
For these reasons, commercial operating systems such as Linux use a per-processor data
structure: a separate copy of the multi-level feedback queue for each processor. Figure 7.6
illustrates this approach.
Each processor uses affinity scheduling: once a thread is scheduled on a processor, it is
returned to the same processor when it is re-scheduled, maximizing cache reuse. Each
processor looks at its own copy of the queue for new work to do;  this can mean that some
processors can idle while others have work waiting to be done. Rebalancing occurs only if
the queue lengths are persistent enough to compensate for the time to reload the cache for the
migrated threads. Because rebalancing is possible, the per-processor data structures must
```

#### Chunk 2

- Chunk ID: `a20dfd11deee60b1`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `159`
- Score: `0.871309 vector_distance`

```text
Often, this is combined with a per-processor ready list, ensuring that each thread
preferentially runs on the same processor each time it is context switched, further improving
execution speed.
An advantage of this approach is better hardware cache behavior; as we saw in the previous
section, shared data that must be communicated between processors can slow dow n the
execution of critical sections. Of course, the disadvantage is that the hash tables are now
partitioned, so that a web page may be cached in one processor’s hash table, and needed in
another. Whether this is a performance benefit depends on the relative impact of reducing
communication of shared data versus the decreased effectiveness of the cache.
```

#### Chunk 3

- Chunk ID: `fd48fd852a20fb7d`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `29`
- Score: `0.889507 vector_distance`

```text
Even if we could ignore the issue of scheduling — e .g., if there are more processors than
threads so that each thread is assigned its own physical processor — the physical reality is
that the relative execution speed of different threads can be significantly affected by factors
outside their control. An extreme example is that the programmer may be debugging one
thread by single-stepping it, while other threads run at full speed on other processors. If the
programmer is to have any hope of understanding concurrent program behavior, the program’s
correctness cannot depend on which threads are being observed.
Variability in execution speed occurs during normal operation as well. Accessing memory
can stall a processor for hundreds or thousands of cycles if a cache miss occurs. Other factors
```

#### Chunk 4

- Chunk ID: `04628e54632b4590`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `216`
- Score: `0.895238 vector_distance`

```text
particular user, users sharing a physical machine. For example, we could be concerned with
making sure that every thread within a process makes progress. For simplicity, however, our
discussion will assume we are interested in providing fairness among processes — the same
principles apply if the unit receiving resources is the user, application, or thread.
Fairness is easy if all processes are compute-bound: Round Robin will give each process an
equal portion of the processor. In practice, however, different processes consume resources
at different rates. An I/O-bound process may need only a small portion of the processor,
while a compute-bound process is willing to consume all available processor time. What is a
fair allocation when there is a diversity of needs?
```

#### Chunk 5

- Chunk ID: `337086551cfc3ddb`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `152`
- Score: `0.906695 vector_distance`

```text
processors because of the difficulty of improving single CPU performance. The design
of shared obj ects can have a large impact on multiprocessor performance. For example,
a lock protecting a frequently accessed shared obj ect can become a bottleneck, since
only one thread can hold the lock at a time.
Correctness. Performance considerations often cause designers to re-engineer their data
structures for increased concurrency. Splitting a single shared obj ect into a set of related
objects each with their own lock can improve performance. However, it also raises
issues of correctness. For programs with multiple shared obj ects, we face a problem
similar to the one faced when reasoning about atomic loads and stores: even if each
```

## q24

**Question:** If utilization close to 100% sounds efficient, why do systems often become much less responsive as utilization approaches 100%?

### Method A

- Retrieval latency: 0.418s
- Generation latency: 7.249s

**Answer:**

Because “100% utilized” means the server is almost never idle, so any randomness in arrivals or service times creates queues that are hard to drain.

In a simple queueing model:

\[
R = \frac{S}{1-U}
\]

where:

- \(R\) = average response time  
- \(S\) = service time  
- \(U\) = utilization  

As \(U\) approaches 1, the denominator \(1-U\) approaches 0, so response time grows very quickly.

Example:

- At \(U = 0.20\):

\[
R = \frac{S}{1-0.20} = 1.25S
\]

- At \(U = 0.90\):

\[
R = \frac{S}{1-0.90} = 10S
\]

- At \(U = 0.95\):

\[
R = \frac{S}{1-0.95} = 20S
\]

So going from 90% to 95% utilization can double the response time.

The key idea: high utilization leaves very little spare capacity to absorb bursts. If requests arrive slightly faster than expected, the system can enter overload, where requests arrive faster than they are completed, and queues grow without bound.

So near-100% utilization may look efficient, but it usually means poor responsiveness and high overload risk.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6e98b5b9aad1e139`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `1.31156 rerank_score`

```text
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
become unbearably long. In the next section, we discuss some of the steps system designers
can take in response to ove rload.
Variance in the response time increases even faster as the system approaches full utilization,
proportional to 1 / (1 - U)2. Even with 99%  utilization, 1% of the time there is no queue at
all; random chance means that while sometimes a large number of customers arrive at nearly
the same time, at other times the server will be able to work through all of the backlog. If you
are lucky enough to arrive at just that moment, you can receive service without waiting. If you
```

#### Chunk 2

- Chunk ID: `dc63c5a2b7393850`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `0.798404 rerank_score`

```text
R   =   S / (1 - U)
   =   S / (1 - 0.25)
   =   1.33 S
The 5% increase in load increases response time by about 8%.
Using the same equation, at 90%  utilization we have R = 10S and at 95%  we have R = 20S,
the 5% increase in load increases response time by a factor of two. □
The response time of a system becomes unbounded as the system approaches full utilization.
Although it might seem that full utilization is an achievable goal, if there is any randomness in
arrivals or any randomness in service times, full utilization cannot be achieved in steady state
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
```

#### Chunk 3

- Chunk ID: `cd8a840bb3eece8b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `241`
- Score: `0.737172 rerank_score`

```text
Operating a system at high utilization also increases the risk of overload. Suppos e you plan to
minimize costs by operating a web site at 95%  utilization, but your service turns out to be a
little more popu lar than you expected. You can quickly find yourself operating in the unstable
regime where requests are arriving faster than you can service them (λ > μ) and where your
queues and waiting times are growing without bound.
As a designer, you need to find an appropriate tradeoff between higher utilization and better
response time. Fifty years ago, computer designers made the tradeoff in favor of higher
utilization: when computers are wildly expensive, it is annoying but understandable to make
people wait for the computer. Now that computers are much cheaper, our lives are better! We
```

#### Chunk 4

- Chunk ID: `ca7a6fe9a766f620`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `247`
- Score: `-0.557581 rerank_score`

```text
Figure 7.21: Relationship between response time and utilization, assuming exponentially distributed arrivals and departures.
Average response time goes to infinity as the system approaches full utilization.
This equation is graphed in Figure 7.21. When utilization is low, there is little queueing delay
and response time is close to the service time. Furthermore, when utilization is low, small
increases in the arrival rate result in small increases in queueing delay and response time.
As utilization increases, queueing and response time also increase, and the relationship is
non-linear. At high utilizations, the queueing delay is high, and small increases in the arrival
rate can drastically increase queueing delay and response time.
```

#### Chunk 5

- Chunk ID: `e2b90f00cc60f113`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `247`
- Score: `-1.1772 rerank_score`

```text
rate can drastically increase queueing delay and response time.
EXAMPLE: Suppos e a queueing system with exponentially distributed arrivals and task
sizes is 20%  utilized and the load increases by 5%, by how much does the response time
increase? How does that increase compare to the case when utilization goes from 90%  to
95%?
ANSWER: At 20%  utilization, the response time is:
R   =   S / (1 - U)
   =   S / (1 - 0.2)
   =   1.25 S
At 25%  utilization, the response time is:
```

### Method B

- Retrieval latency: 0.195s
- Generation latency: 6.679s

**Answer:**

Because **high utilization leaves almost no spare capacity to absorb randomness**.

Even if the average arrival rate is just below the service rate, real systems do not receive work perfectly evenly. Requests arrive in bursts, and service times vary. When utilization is low or moderate, the system has idle gaps that let it catch up after a burst. But near 100% utilization, those gaps almost disappear.

So queues build up quickly:

- At **90% utilization**, average response time can be about  
  \[
  R = \frac{S}{1-U} = \frac{S}{1-0.9} = 10S
  \]
- At **95% utilization**,  
  \[
  R = \frac{S}{1-0.95} = 20S
  \]

So a small increase in utilization can cause a huge increase in waiting time.

The key point is: **utilization measures how busy the server is, not how long users wait**. Near 100%, the server may look “efficient,” but any burst of requests creates a queue that the system has almost no free time to drain. If arrivals exceed capacity even slightly, the system enters overload and queues can grow without bound.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `cd8a840bb3eece8b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `241`
- Score: `0.649526 vector_distance`

```text
Operating a system at high utilization also increases the risk of overload. Suppos e you plan to
minimize costs by operating a web site at 95%  utilization, but your service turns out to be a
little more popu lar than you expected. You can quickly find yourself operating in the unstable
regime where requests are arriving faster than you can service them (λ > μ) and where your
queues and waiting times are growing without bound.
As a designer, you need to find an appropriate tradeoff between higher utilization and better
response time. Fifty years ago, computer designers made the tradeoff in favor of higher
utilization: when computers are wildly expensive, it is annoying but understandable to make
people wait for the computer. Now that computers are much cheaper, our lives are better! We
```

#### Chunk 2

- Chunk ID: `dc63c5a2b7393850`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `0.779046 vector_distance`

```text
R   =   S / (1 - U)
   =   S / (1 - 0.25)
   =   1.33 S
The 5% increase in load increases response time by about 8%.
Using the same equation, at 90%  utilization we have R = 10S and at 95%  we have R = 20S,
the 5% increase in load increases response time by a factor of two. □
The response time of a system becomes unbounded as the system approaches full utilization.
Although it might seem that full utilization is an achievable goal, if there is any randomness in
arrivals or any randomness in service times, full utilization cannot be achieved in steady state
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
```

#### Chunk 3

- Chunk ID: `6e98b5b9aad1e139`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `0.79304 vector_distance`

```text
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
become unbearably long. In the next section, we discuss some of the steps system designers
can take in response to ove rload.
Variance in the response time increases even faster as the system approaches full utilization,
proportional to 1 / (1 - U)2. Even with 99%  utilization, 1% of the time there is no queue at
all; random chance means that while sometimes a large number of customers arrive at nearly
the same time, at other times the server will be able to work through all of the backlog. If you
are lucky enough to arrive at just that moment, you can receive service without waiting. If you
```

#### Chunk 4

- Chunk ID: `85994412caae7d56`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `253`
- Score: `0.840588 vector_distance`

```text
requests: as more requests are queued, more processing time is used maintaining the queue
and not getting useful work done. If amount of work per task increases as the load increases,
then response times will soar even faster with increased utilization, and throughput can
decrease as we add load. This makes overload management even more important.
Figure 7.22: Measured throughput (cars per hour) versus occupancy (percentage of the road covered with vehicles). Each
data point represents a separate observation. At low load, throughput increases linearly; once load passes a critical point,
adding vehicles decreases average throughput. As each vehicle moves more slowly, it takes more time on the highway to
```

#### Chunk 5

- Chunk ID: `548da36b62b9a80f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `252`
- Score: `0.842702 vector_distance`

```text
More sophisticated scheduling can help at low to moderate load, bu t if the load is more than
system can handle, response time will spike, even for short tasks.
The key idea in overload management is to design your system to do l ess work when
overloaded. This will seem strange! After all, you want your system to work a particular
way; how can you cripple the user’s experience just when your system becomes popu lar?
Under overload conditions, however, your system is incapable of serving all of the requests
in the normal way. The only question is: do y ou choose what to disable, or do y ou let events
choose for you?
An obvi ous step is to simply reject some requests in order to preserve reasonable response
```

### Method C

- Retrieval latency: 0.647s
- Generation latency: 6.825s

**Answer:**

Because near 100% utilization, the system has almost **no spare capacity** to absorb randomness.

Even if the *average* arrival rate is just below the service rate, requests do not arrive perfectly evenly. They arrive in bursts, and service times vary. When the server is already busy almost all the time, any burst creates a queue, and there is very little idle time later to catch up.

A common queueing result is:

\[
R = \frac{S}{1-U}
\]

where:

- \(R\) = average response time  
- \(S\) = service time  
- \(U\) = utilization  

So if utilization is:

- \(U = 0.90\), then \(R = 10S\)
- \(U = 0.95\), then \(R = 20S\)
- \(U = 0.99\), then \(R = 100S\)

So a small increase in utilization near 100% can cause a huge increase in response time.

If load exceeds capacity, meaning requests arrive faster than they can be served \((\lambda > \mu)\), the queue grows without bound and the system enters overload.

So high utilization sounds efficient, but near 100% the system becomes fragile: queues grow, waiting time explodes, and responsiveness collapses.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `cd8a840bb3eece8b`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `241`
- Score: `n/a `

```text
Operating a system at high utilization also increases the risk of overload. Suppos e you plan to
minimize costs by operating a web site at 95%  utilization, but your service turns out to be a
little more popu lar than you expected. You can quickly find yourself operating in the unstable
regime where requests are arriving faster than you can service them (λ > μ) and where your
queues and waiting times are growing without bound.
As a designer, you need to find an appropriate tradeoff between higher utilization and better
response time. Fifty years ago, computer designers made the tradeoff in favor of higher
utilization: when computers are wildly expensive, it is annoying but understandable to make
people wait for the computer. Now that computers are much cheaper, our lives are better! We
```

#### Chunk 2

- Chunk ID: `dc63c5a2b7393850`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `n/a `

```text
R   =   S / (1 - U)
   =   S / (1 - 0.25)
   =   1.33 S
The 5% increase in load increases response time by about 8%.
Using the same equation, at 90%  utilization we have R = 10S and at 95%  we have R = 20S,
the 5% increase in load increases response time by a factor of two. □
The response time of a system becomes unbounded as the system approaches full utilization.
Although it might seem that full utilization is an achievable goal, if there is any randomness in
arrivals or any randomness in service times, full utilization cannot be achieved in steady state
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
```

#### Chunk 3

- Chunk ID: `6e98b5b9aad1e139`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `248`
- Score: `n/a `

```text
without making some tasks wait unbounded amounts of time.
In most systems, well before a system reaches full utilization, average response time will
become unbearably long. In the next section, we discuss some of the steps system designers
can take in response to ove rload.
Variance in the response time increases even faster as the system approaches full utilization,
proportional to 1 / (1 - U)2. Even with 99%  utilization, 1% of the time there is no queue at
all; random chance means that while sometimes a large number of customers arrive at nearly
the same time, at other times the server will be able to work through all of the backlog. If you
are lucky enough to arrive at just that moment, you can receive service without waiting. If you
```

#### Chunk 4

- Chunk ID: `85994412caae7d56`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `253`
- Score: `n/a `

```text
requests: as more requests are queued, more processing time is used maintaining the queue
and not getting useful work done. If amount of work per task increases as the load increases,
then response times will soar even faster with increased utilization, and throughput can
decrease as we add load. This makes overload management even more important.
Figure 7.22: Measured throughput (cars per hour) versus occupancy (percentage of the road covered with vehicles). Each
data point represents a separate observation. At low load, throughput increases linearly; once load passes a critical point,
adding vehicles decreases average throughput. As each vehicle moves more slowly, it takes more time on the highway to
```

#### Chunk 5

- Chunk ID: `548da36b62b9a80f`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `252`
- Score: `n/a `

```text
More sophisticated scheduling can help at low to moderate load, bu t if the load is more than
system can handle, response time will spike, even for short tasks.
The key idea in overload management is to design your system to do l ess work when
overloaded. This will seem strange! After all, you want your system to work a particular
way; how can you cripple the user’s experience just when your system becomes popu lar?
Under overload conditions, however, your system is incapable of serving all of the requests
in the normal way. The only question is: do y ou choose what to disable, or do y ou let events
choose for you?
An obvi ous step is to simply reject some requests in order to preserve reasonable response
```

## q25

**Question:** If the operating system already protects processes from one another, why do we also need user mode and kernel mode?

### Method A

- Retrieval latency: 0.367s
- Generation latency: 7.120s

**Answer:**

Because the operating system can only protect processes if the hardware gives it a way to enforce those protections.

If every program ran with full CPU privileges, then a process could simply:

- access another process’s memory,
- overwrite kernel memory,
- issue disk or device commands directly,
- disable interrupts,
- bypass OS checks entirely.

So the OS needs two modes:

### User mode
Normal applications run here. They are restricted.

They cannot directly do dangerous things like access arbitrary memory, control hardware, or modify CPU protection settings.

### Kernel mode
The operating system kernel runs here. It has full privileges and can manage memory, devices, files, processes, etc.

When a user program needs something privileged, like reading a file, it must ask the kernel through a controlled mechanism such as a system call.

So the key idea is:

> The OS provides the protection policy, but user/kernel mode provides the hardware enforcement.

Without user mode and kernel mode, OS protection would just be software checks that a program could skip or overwrite. Kernel mode lets the OS be trusted; user mode keeps applications limited.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `5.28113 rerank_score`

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 2

- Chunk ID: `f45561d3f608262d`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `3.988 rerank_score`

```text
vice versa. These transitions are not rare events. A high-performance web server, for
example, might switch between user mode and kernel mode thousands of times per second.
Thus, the mechanism must be both fast and safe, leaving no room for malicious or buggy
programs to corrupt the kernel, either intentionally or inadvertently.
2.3.1 User to Kernel Mode
We first focus on transitions from user mode to kernel mode; as we will see, transitioning in
the other direction works by “undo"-ing the transition from the user process into the kernel.
There are three reasons for the kernel to take control from a user process: interrupts,
processor exceptions, and system calls. Interrupts occur asynchronously — that is, they are
```

#### Chunk 3

- Chunk ID: `e918b7c40a5834be`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `56`
- Score: `3.31773 rerank_score`

```text
Timer Interrupts. Regardless of what the process does, the kernel must have a way to
periodically regain control from the current process. (Section 2.2.3 )
In addition, the hardware must also provide a way to safely transfer control from user mode
to kernel mode and back. As the mechanisms to do t his are relatively involved, we defer the
discussion of that topic to Sections 2.3 and  2.4.
The processor status register and privilege levels
Conceptually, the kernel/user mode is a one-bit register. When set to 1, the processor is in kernel mode and can do anything.
When set to 0, the processor is in user mode and is restricted. On most processors, the kernel/user mode is stored in the
```

#### Chunk 4

- Chunk ID: `641bebaf9f977369`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `3.07439 rerank_score`

```text
other.
Safety. However, resource management and protection are the responsibility of the
operating system kernel. As Chapter 2 explained, protection checks cannot be
implemented in a user-level library because application code can skip any checks made
by the library.
Reliability. Improved reliability is another reason to keep the operating system kernel
minimal. Kernel code needs the pow er to set up hardware devices, such as the disk, and
to control protection boundaries between applications. However, kernel modules are
typically not protected from one another, and so a bug in kernel code (whether sensitive
or not) may corrupt user or kernel data. This has led some systems to use a philosophy
of “what can be at user level, should be.” An extreme version of approach is to isolate
```

#### Chunk 5

- Chunk ID: `eb4d2c65e835b357`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `3.04108 rerank_score`

```text
How does the operating system kernel prevent a process from harming other processes or the
operating system itself? After all, when multiple programs are loaded into memory at the
same time, what prevents a process from overwriting another process’s data structures, or
even overwriting the operating system image stored on disk?
If we step back from any consideration of performance, a very simple, safe, and entirely
hypothetical approach would be to have the operating system kernel simulate, step by step,
every instruction in every user process. Instead of the processor directly executing
instructions, a software interpreter would fetch, decode, and execute each user program
instruction in turn. Before executing each instruction, the interpreter could check if the
```

### Method B

- Retrieval latency: 1.176s
- Generation latency: 10.686s

**Answer:**

Because the OS can protect processes **only if the hardware gives it a way to enforce that protection**.

User mode and kernel mode provide that enforcement.

- **User mode**: normal applications run here. Dangerous operations are disabled, such as:
  - directly accessing hardware devices
  - changing memory protection settings
  - modifying kernel memory
  - disabling interrupts
  - executing privileged CPU instructions

- **Kernel mode**: the OS kernel runs here. It has full privileges and can:
  - manage memory
  - schedule processes
  - access devices
  - enforce file and security permissions

So the idea is:

> The OS protects processes from one another by making sure ordinary processes run in user mode, where they cannot directly do dangerous things.

If there were no user/kernel mode distinction, then any process could potentially run the same instructions as the OS kernel. A buggy or malicious program could overwrite another process’s memory, corrupt the kernel, or take control of hardware directly.

When a user program needs something privileged, like reading a file or allocating memory, it must make a **system call**. That transfers control to the kernel, which checks whether the operation is allowed.

So user mode and kernel mode are not separate from OS protection — they are one of the main mechanisms that make OS protection possible.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `n/a `

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 2

- Chunk ID: `eb4d2c65e835b357`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `n/a `

```text
How does the operating system kernel prevent a process from harming other processes or the
operating system itself? After all, when multiple programs are loaded into memory at the
same time, what prevents a process from overwriting another process’s data structures, or
even overwriting the operating system image stored on disk?
If we step back from any consideration of performance, a very simple, safe, and entirely
hypothetical approach would be to have the operating system kernel simulate, step by step,
every instruction in every user process. Instead of the processor directly executing
instructions, a software interpreter would fetch, decode, and execute each user program
instruction in turn. Before executing each instruction, the interpreter could check if the
```

#### Chunk 3

- Chunk ID: `39eaf62c46bd6a14`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `50`
- Score: `n/a `

```text
forth. In other words, the operating system kernel mediates and checks each process’s access
to hardware. This chapter explains the process concept and how the kernel implements
process isolation.
A key consideration is the need to provide protection while still running application code at
high speed. The operating system kernel runs directly on the processor with unlimited rights.
The kernel can perform any operation available on the hardware. What about applications?
They need to run on the processor with all potentially dangerous operations disabled. To
make this work, hardware needs to provide a bit of assistance, which we will describe
shortly. Throughout the book , there are similar examples of how small amounts of carefully
```

#### Chunk 4

- Chunk ID: `ee26915851171bd6`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `n/a `

```text
operating system executes with protection checks turned off.
The kernel vs. the rest of the operating system
The operating system kernel is a crucial piece of an operating system, but it is only a portion of the overall operating system.
In most modern operating systems, a portion of the operating system runs in user mode as a library linked into each
application. An example is library code that manages an application’s menu buttons. To encourage a common user interface
across applications, most operating systems provide a library of user interface widgets. Applications can write their own user
interface routines, but most developers choose to reuse the routines provided by the operating system. This code could run in
```

#### Chunk 5

- Chunk ID: `1efc98902f5dbba4`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `48`
- Score: `n/a `

```text
2. The Kernel Abstraction
Good f ences make good n eighbors. —17th century proverb
A central role of operating systems is protection — the isolation of potentially misbehaving
applications and users so that they do n ot corrupt other applications or the operating system
itself. Protection is essential to achieving several of the operating systems goals noted in the
previous chapter:
Reliability. Protection prevents bugs in one program from causing crashes in other
programs or in the operating system. To the user, a system crash appears to be the
operating system’s fault, even if the root cause of the problem is some unexpected
behavior by an application or user. Thus, for high system reliability, an operating system
```

### Method C

- Retrieval latency: 0.212s
- Generation latency: 7.674s

**Answer:**

Because **process protection depends on user mode and kernel mode to be enforceable**.

The OS wants to protect processes from each other, but if an application could run with full hardware privileges, it could simply bypass the OS and do dangerous things directly, such as:

- access another process’s memory,
- modify page tables,
- write directly to disk,
- disable interrupts,
- overwrite kernel data.

So the hardware provides two modes:

- **User mode**: normal applications run here. Dangerous instructions are disabled.
- **Kernel mode**: the OS kernel runs here. It can access hardware, memory-management structures, devices, etc.

When a process needs something privileged, like reading a file or allocating memory, it must make a **system call**. That transfers control to the kernel, which checks whether the request is allowed.

So the key idea is:

> The OS protects processes, but **user/kernel mode is the hardware mechanism that prevents applications from bypassing that protection**.

Without user mode and kernel mode, process isolation would mostly rely on applications behaving honestly, which is not safe.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `0.632041 vector_distance`

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 2

- Chunk ID: `641bebaf9f977369`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `0.652189 vector_distance`

```text
other.
Safety. However, resource management and protection are the responsibility of the
operating system kernel. As Chapter 2 explained, protection checks cannot be
implemented in a user-level library because application code can skip any checks made
by the library.
Reliability. Improved reliability is another reason to keep the operating system kernel
minimal. Kernel code needs the pow er to set up hardware devices, such as the disk, and
to control protection boundaries between applications. However, kernel modules are
typically not protected from one another, and so a bug in kernel code (whether sensitive
or not) may corrupt user or kernel data. This has led some systems to use a philosophy
of “what can be at user level, should be.” An extreme version of approach is to isolate
```

#### Chunk 3

- Chunk ID: `eb4d2c65e835b357`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `0.7061 vector_distance`

```text
How does the operating system kernel prevent a process from harming other processes or the
operating system itself? After all, when multiple programs are loaded into memory at the
same time, what prevents a process from overwriting another process’s data structures, or
even overwriting the operating system image stored on disk?
If we step back from any consideration of performance, a very simple, safe, and entirely
hypothetical approach would be to have the operating system kernel simulate, step by step,
every instruction in every user process. Instead of the processor directly executing
instructions, a software interpreter would fetch, decode, and execute each user program
instruction in turn. Before executing each instruction, the interpreter could check if the
```

#### Chunk 4

- Chunk ID: `ee26915851171bd6`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `0.726129 vector_distance`

```text
operating system executes with protection checks turned off.
The kernel vs. the rest of the operating system
The operating system kernel is a crucial piece of an operating system, but it is only a portion of the overall operating system.
In most modern operating systems, a portion of the operating system runs in user mode as a library linked into each
application. An example is library code that manages an application’s menu buttons. To encourage a common user interface
across applications, most operating systems provide a library of user interface widgets. Applications can write their own user
interface routines, but most developers choose to reuse the routines provided by the operating system. This code could run in
```

#### Chunk 5

- Chunk ID: `39eaf62c46bd6a14`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `50`
- Score: `0.750558 vector_distance`

```text
forth. In other words, the operating system kernel mediates and checks each process’s access
to hardware. This chapter explains the process concept and how the kernel implements
process isolation.
A key consideration is the need to provide protection while still running application code at
high speed. The operating system kernel runs directly on the processor with unlimited rights.
The kernel can perform any operation available on the hardware. What about applications?
They need to run on the processor with all potentially dangerous operations disabled. To
make this work, hardware needs to provide a bit of assistance, which we will describe
shortly. Throughout the book , there are similar examples of how small amounts of carefully
```

## q26

**Question:** Why can’t an ordinary user program just execute privileged instructions directly if it needs something done by the hardware?

### Method A

- Retrieval latency: 0.822s
- Generation latency: 6.003s

**Answer:**

Because that would break protection between programs and users.

An ordinary user program runs in **user mode**. In user mode, the CPU is designed to **reject privileged instructions**—instructions that could affect the whole machine, such as:

- changing memory protection settings,
- directly accessing hardware devices,
- disabling interrupts,
- modifying the processor’s privilege level,
- doing raw disk I/O.

If user programs could execute those directly, a buggy or malicious program could:

- read or overwrite another program’s memory,
- corrupt the disk,
- take control of hardware devices,
- bypass file permissions,
- crash the whole system.

So the CPU only allows those instructions in **kernel mode**, where the operating system kernel runs.

When a user program needs something privileged done, it must make a **system call**. That transfers control to the kernel at a controlled entry point. The kernel then checks whether the request is allowed, performs the operation if appropriate, and returns control to the user program.

So the key idea is:

> User programs can request privileged operations, but they cannot perform them directly.  
> Only the kernel can execute privileged instructions.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `n/a `

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 2

- Chunk ID: `74bef6ef72186e08`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `56`
- Score: `n/a `

```text
would run at user level; the virtual machine would run at some intermediate level; and the true kernel would run in kernel
mode. Of course, with only four levels, this does not work for a virtual machine running on a virtual machine running on a
virtual machine. For our discussion, we assume the simpler and more universal case of two levels of hardware protection.
2.2.1 Privileged Instructions
Process isolation is possible only if there is a way to limit programs running in user mode
from directly changing their privilege level. We discuss in Section 2.3 that processes can
indirectly change their privilege level by executing a special instruction, called a system call,
to transfer control into the kernel at a fixed location defined by the operating system. Other
```

#### Chunk 3

- Chunk ID: `08adb4b6b800d12f`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `n/a `

```text
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
Privileged Instructions. All potentially unsafe instructions are prohibited when
executing in user mode. (Section 2.2.1 )
Memory Protection. All memory accesses outside of a process’s valid memory region
are prohibited when executing in user mode. (Section 2.2.2 )
```

#### Chunk 4

- Chunk ID: `ab833bad31271f07`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `n/a `

```text
modify the processor in some way to allow safe instructions to execute directly on the
hardware?
To accomplish this, we implement the same checks as in our hypothetical interpreter, but in
hardware rather than software. This is called dual-mode operation, represented by a single
bit in the processor status register that signifies the current mode of the processor. In user
mode, the processor checks each instruction before executing it to verify that it is permitted to
be performed by that process. (We describe the specific checks next.) In kernel mode, the
operating system executes with protection checks turned off.
The kernel vs. the rest of the operating system
```

#### Chunk 5

- Chunk ID: `692a1e9047cd21c5`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `68`
- Score: `n/a `

```text
hardware must ensure that the entry point into the kernel is one set up by the kernel. User
programs cannot be allowed to jump to arbitrary locations in the kernel. For example,
the kernel code for handling the read file system call first checks whether the user
program has permission to do s o. If not, the kernel should return an error. Without
limited entry points into the kernel, a malicious program could jump immediately after
the code to perform the check, allowing the program to access to anyone’s file.
Atomic changes to processor state. In user mode, the program counter and stack point
to memory locations in the user process; memory protection prevents the user process
from accessing any memory outside of its region. In kernel mode, the program counter
```

### Method B

- Retrieval latency: 0.425s
- Generation latency: 6.420s

**Answer:**

Because an ordinary user program runs in **user mode**, where the CPU deliberately blocks **privileged instructions**.

Privileged instructions are operations that could affect the whole system, such as:

- changing memory protection settings
- disabling interrupts
- accessing hardware devices directly
- changing privilege levels
- controlling parts of the CPU or OS state

If any user program could execute those directly, a buggy or malicious program could effectively gain the power of the operating system kernel. It could corrupt other processes, damage files, bypass security, or prevent the OS from regaining control.

So the hardware enforces a separation:

- **User programs** run in **user mode** and can only execute safe, non-privileged instructions.
- The **operating system kernel** runs in **kernel mode** and can execute the full instruction set, including privileged instructions.

When a user program needs something privileged done, it does not execute the instruction directly. Instead, it makes a **system call**, which transfers control to the OS kernel. The kernel checks whether the request is allowed, performs the operation if appropriate, and then returns control to the user program.

So the short answer is:  
**user programs cannot execute privileged instructions directly because the CPU blocks them in user mode to protect the system.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `0171775121f108f4`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `63`
- Score: `4.64383 rerank_score`

```text
program, the process is free to execute any user-level (non-privileged) instructions it
chooses, call any function in the process’s memory region, load or store any value to its
memory, and so forth. To the user program, it appears to have complete control of the
hardware within the limits of its memory region.
However, this too is only an illusion. If the application enters an infinite loop, or  if the user
simply becomes impatient and wants the system to stop the application, then the operating
system must be able to regain control. Of course, the operating system needs to execute
instructions to decide if it should stop the application, but if the application controls the
processor, the operating system by definition is not running on that processor.
```

#### Chunk 2

- Chunk ID: `08adb4b6b800d12f`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `4.53224 rerank_score`

```text
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
Privileged Instructions. All potentially unsafe instructions are prohibited when
executing in user mode. (Section 2.2.1 )
Memory Protection. All memory accesses outside of a process’s valid memory region
are prohibited when executing in user mode. (Section 2.2.2 )
```

#### Chunk 3

- Chunk ID: `f6041dd4208b28d2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `57`
- Score: `3.89491 rerank_score`

```text
or the operating system. Further, applications cannot disable processor interrupts, as we will
explain in Section 2.2.3 .
Instructions available in kernel mode, but not in user mode, are called privileged
instructions. The operating system kernel must be able to execute these instructions to do i ts
work — it needs to change privilege levels, adjust memory access, and disable and enable
interrupts. If these instructions were available to applications, then a rogue application would
in effect have the pow er of the operating system kernel.
Thus, while application programs can use only a subset of the full instruction set, the
operating system executes in kernel mode with the full pow er of the hardware.
```

#### Chunk 4

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `3.44844 rerank_score`

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 5

- Chunk ID: `6dbe32baa210f8b8`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `66`
- Score: `2.94918 rerank_score`

```text
exception is raised, trapping into the operating system kernel. Instead of halting the process, the operating system can
emulate the missing instruction, and, on completion, return to the user process at the instruction immediately after the
one that caused the exception. In this way, the same program binary can run on different versions of the processor.
More generally, processor exceptions are used to transparently emulate a virtual machine. When a guest operating
system is running as a user-level process on top of an operating system, it will attempt to execute privileged
instructions as if it were running on physical hardware. These instructions will cause processor exceptions, trapping
```

### Method C

- Retrieval latency: 0.197s
- Generation latency: 8.537s

**Answer:**

Because an ordinary user program runs in **user mode**, where the CPU deliberately blocks dangerous operations.

Privileged instructions can do things like:

- change memory protection settings
- access hardware devices directly
- disable interrupts
- switch privilege levels
- modify CPU control registers

If any user program could execute those directly, it could effectively gain the power of the kernel. For example, a buggy or malicious program could overwrite another process’s memory, corrupt the disk, or prevent the OS from regaining control.

So the CPU enforces a rule:

> Privileged instructions may execute only in **kernel mode**.

If a user program tries to execute one directly, the hardware rejects it, usually by causing a trap/exception.

Instead, the program must ask the operating system through a **system call**. The system call transfers control to a fixed, trusted kernel entry point. The kernel then checks whether the request is allowed and, if so, performs the privileged operation on the program’s behalf.

So the short answer is:

> User programs cannot execute privileged instructions directly because that would break process isolation and system protection. They must request such actions from the kernel using system calls.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `08adb4b6b800d12f`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `0.647956 vector_distance`

```text
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
Privileged Instructions. All potentially unsafe instructions are prohibited when
executing in user mode. (Section 2.2.1 )
Memory Protection. All memory accesses outside of a process’s valid memory region
are prohibited when executing in user mode. (Section 2.2.2 )
```

#### Chunk 2

- Chunk ID: `f6041dd4208b28d2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `57`
- Score: `0.740508 vector_distance`

```text
or the operating system. Further, applications cannot disable processor interrupts, as we will
explain in Section 2.2.3 .
Instructions available in kernel mode, but not in user mode, are called privileged
instructions. The operating system kernel must be able to execute these instructions to do i ts
work — it needs to change privilege levels, adjust memory access, and disable and enable
interrupts. If these instructions were available to applications, then a rogue application would
in effect have the pow er of the operating system kernel.
Thus, while application programs can use only a subset of the full instruction set, the
operating system executes in kernel mode with the full pow er of the hardware.
```

#### Chunk 3

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `0.754468 vector_distance`

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 4

- Chunk ID: `74bef6ef72186e08`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `56`
- Score: `0.800413 vector_distance`

```text
would run at user level; the virtual machine would run at some intermediate level; and the true kernel would run in kernel
mode. Of course, with only four levels, this does not work for a virtual machine running on a virtual machine running on a
virtual machine. For our discussion, we assume the simpler and more universal case of two levels of hardware protection.
2.2.1 Privileged Instructions
Process isolation is possible only if there is a way to limit programs running in user mode
from directly changing their privilege level. We discuss in Section 2.3 that processes can
indirectly change their privilege level by executing a special instruction, called a system call,
to transfer control into the kernel at a fixed location defined by the operating system. Other
```

#### Chunk 5

- Chunk ID: `ab833bad31271f07`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `54`
- Score: `0.814626 vector_distance`

```text
modify the processor in some way to allow safe instructions to execute directly on the
hardware?
To accomplish this, we implement the same checks as in our hypothetical interpreter, but in
hardware rather than software. This is called dual-mode operation, represented by a single
bit in the processor status register that signifies the current mode of the processor. In user
mode, the processor checks each instruction before executing it to verify that it is permitted to
be performed by that process. (We describe the specific checks next.) In kernel mode, the
operating system executes with protection checks turned off.
The kernel vs. the rest of the operating system
```

## q27

**Question:** If system calls are just requests for the kernel to do work, why is the boundary between user mode and kernel mode such a big deal?

### Method A

- Retrieval latency: 0.819s
- Generation latency: 8.499s

**Answer:**

Because a system call is not just a normal function call — it crosses a **protection boundary**.

In user mode, a program is deliberately limited. It cannot directly do things like:

- access arbitrary physical memory
- modify page tables
- talk directly to hardware devices
- corrupt the file system
- disable interrupts
- interfere with other processes

Kernel mode can do those things. So the user/kernel boundary is a big deal because it controls **who is allowed to use dangerous privileges**.

A system call is the safe doorway through that boundary:

1. A user program requests something, e.g. “open this file” or “allocate memory.”
2. The CPU switches from user mode to kernel mode using a special trap/syscall mechanism.
3. The kernel checks the request: permissions, arguments, validity, resource limits, etc.
4. If allowed, the kernel performs the operation and returns to user mode.

So the boundary matters for three main reasons:

- **Security:** one program should not be able to read another user’s files or memory.
- **Reliability:** a buggy application should not be able to crash or corrupt the whole system.
- **Controlled sharing:** hardware and OS resources are shared through kernel-managed rules.

If system calls were just ordinary calls into kernel code without a privilege boundary, any program could misuse kernel-level power. The boundary is what lets user programs run directly on the CPU while still keeping the system protected.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `f254d98fdea5fbb2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `n/a `

```text
of “what can be at user level, should be.” An extreme version of approach is to isolate
privileged, bu t less critical, parts of the operating system such as the file system or the
window system, from the rest of the kernel. This is called a microkernel design. In a
microkernel, the kernel itself is kept small, and instead most of the functionality of a
traditional operating system kernel is put into a set of user-level processes, or servers,
accessed from user applications via interprocess communication.
Performance. Finally, transferring control into the kernel is more expensive than a
procedure call to a library, and transferring control to a user-level file system server via
the kernel is still even more costly. Hardware designers have attempted to reduce the
```

#### Chunk 2

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `n/a `

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 3

- Chunk ID: `d12ac4c54d6a5c31`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `n/a `

```text
data through the kernel.
Operating systems use the system call interface to provide services to applications and to aid
in the internal structuring of the operating system itself. Almost all general-purpose computer
systems today have a user-level shell and/or a window manager that can start and manage
applications on behalf of the user. Many systems also implement parts of the operating system
as user-level services accessed through kernel pipes.
As we noted, a trend is for applications to become mini-operating systems in their own right,
with multiple users, resource sharing and allocation, untrusted third-party code, processor
and memory management, and so forth. The system call interfaces for Windows and UNIX
```

#### Chunk 4

- Chunk ID: `5912bd2817ef4007`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `106`
- Score: `n/a `

```text
Interposing on system calls is straightforward. The kernel uses a table lookup to determine
which routine to call for each system call invoked by the application program. The kernel can
redirect a system call to a new enhanced routine by simply changing the table entry.
A more interesting case is the memory system. Address translation hardware provides an
efficient way for the operating system to monitor and gain control on every memory reference
to a specific region of memory, while allowing other memory references to continue
unaffected. (Equivalently, software-based fault isolation provides many of the same hooks,
with different tradeoffs between interposition and execution speed.) This makes address
```

#### Chunk 5

- Chunk ID: `af95d7ec6a43112b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `80`
- Score: `n/a `

```text
call procedures, each with its own arguments and return values, that can be called like any
other routine. The user program need not concern itself with how the kernel implements these
calls.
Implementing system calls requires the operating system to define a calling convention —
how to name system calls, pass arguments, and receive return values across the user/kernel
boundary. Typically, the operating system uses the same convention as the compiler uses for
normal procedures — s ome combination of passing arguments in registers and on the
execution stack.
Once the arguments are in the correct format, the user-level program can issue a system call
by executing the trap instruction to transfer control to the kernel. System calls, like interrupts
```

### Method B

- Retrieval latency: 0.452s
- Generation latency: 8.561s

**Answer:**

Because a system call is not just a normal function call — it crosses a **trust boundary**.

In **user mode**, a program is restricted. It cannot directly do dangerous things like:

- access arbitrary physical memory
- modify kernel data structures
- control devices directly
- change page tables
- disable interrupts
- interfere with other processes

In **kernel mode**, code has full hardware privileges. If buggy or malicious user code could freely run there, it could crash the OS, steal data, or take over the machine.

So the boundary matters because the kernel must say:

> “You may request this operation, but I will check whether it is valid and safe before doing it.”

For example, if a program calls `read(fd, buffer, size)`, the kernel must check things like:

- Is `fd` a valid file descriptor?
- Is `buffer` actually memory owned by this process?
- Is `size` reasonable?
- Does the process have permission to read this file?

The system call mechanism gives user programs a **controlled entry point** into the kernel. The CPU switches from user mode to kernel mode using a trap/syscall instruction, and the kernel handles the request carefully.

So the big deal is:

> System calls let user programs use privileged OS services without giving them privileged control.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ba0d1d0f47f636b8`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `80`
- Score: `3.55172 rerank_score`

```text
by executing the trap instruction to transfer control to the kernel. System calls, like interrupts
and processor exceptions, share the same mechanism for switching between user and kernel
mode. In fact, the x86 instruction to trap into the kernel on a system call is called int, for
“software interrupt.”
Inside the kernel, a procedure implements each system call. This procedure behaves exactly
as if the call was made from within the kernel but with one notable difference: the kernel must
implement its system calls in a way that protects itself from all errors and attacks that might
be launched by the misuse of the interface. Of course, most applications will use the interface
correctly! But errors in an application program must not crash the kernel, and a computer
```

#### Chunk 2

- Chunk ID: `f45561d3f608262d`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `3.02802 rerank_score`

```text
vice versa. These transitions are not rare events. A high-performance web server, for
example, might switch between user mode and kernel mode thousands of times per second.
Thus, the mechanism must be both fast and safe, leaving no room for malicious or buggy
programs to corrupt the kernel, either intentionally or inadvertently.
2.3.1 User to Kernel Mode
We first focus on transitions from user mode to kernel mode; as we will see, transitioning in
the other direction works by “undo"-ing the transition from the user process into the kernel.
There are three reasons for the kernel to take control from a user process: interrupts,
processor exceptions, and system calls. Interrupts occur asynchronously — that is, they are
```

#### Chunk 3

- Chunk ID: `5fabc528cec35be3`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `67`
- Score: `1.64089 rerank_score`

```text
handler fills in the data from disk before resuming the program. In this way, the operating system can execute
programs that require more memory than can fit on the machine at the same time.
System calls. User processes can also transition into the operating system kernel
voluntarily to request that the kernel perform an operation on the user’s behalf. A system
call is any procedure provided by the kernel that can be called from user level. Most
processors implement system calls with a special trap or syscall instruction.
However, a special instruction is not strictly required; on some systems, a process
triggers a system call by executing an instruction with a specific invalid opc ode.
As with an interrupt or a processor exception, the trap instruction changes the processor
```

#### Chunk 4

- Chunk ID: `af95d7ec6a43112b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `80`
- Score: `1.34826 rerank_score`

```text
call procedures, each with its own arguments and return values, that can be called like any
other routine. The user program need not concern itself with how the kernel implements these
calls.
Implementing system calls requires the operating system to define a calling convention —
how to name system calls, pass arguments, and receive return values across the user/kernel
boundary. Typically, the operating system uses the same convention as the compiler uses for
normal procedures — s ome combination of passing arguments in registers and on the
execution stack.
Once the arguments are in the correct format, the user-level program can issue a system call
by executing the trap instruction to transfer control to the kernel. System calls, like interrupts
```

#### Chunk 5

- Chunk ID: `566b9ff495ff59da`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `67`
- Score: `1.31264 rerank_score`

```text
user process. To the user program, these are called like normal procedures, with
parameters and return values. The caller needs to be concerned only with the interface;
it does not need to know that the routine is actually being implemented by the kernel. The
kernel handles the details of checking and copying arguments, performing the operation,
and copying return values back into the process’s memory. When the kernel completes
the system call, it resumes user-level execution at the instruction immediately after the
trap.
2.3.2 Kernel to User Mode
Just as there are several different types of transitions from user to kernel mode, there are
several types of transitions from kernel to user mode:
New process. To start a new process, the kernel copies the program into memory, sets
```

### Method C

- Retrieval latency: 0.279s
- Generation latency: 10.595s

**Answer:**

Because a system call is not just a normal function call — it crosses a **protection boundary**.

In user mode, a program is deliberately restricted. It cannot directly do things like:

- access arbitrary physical memory
- modify page tables
- talk directly to devices
- change CPU scheduling state
- corrupt the file system
- interfere with other processes

Those powers belong to the kernel because mistakes or malicious behavior there can affect the whole system.

So the user/kernel boundary matters for three main reasons:

1. **Protection**
   User programs should not be able to damage the OS or other programs. If a buggy application crashes, ideally only that application dies — not the whole machine.

2. **Controlled access**
   Programs still need services like file I/O, process creation, memory allocation, and networking. System calls provide a controlled doorway into the kernel. The kernel checks the request, validates arguments, enforces permissions, does the work, and returns a result.

3. **Privilege**
   Kernel mode can execute privileged instructions that user mode cannot. The mode switch gives the kernel temporary control to perform operations that ordinary code is not trusted to perform directly.

So although system calls may look like ordinary procedure calls from the program’s perspective, internally they involve a **trap into kernel mode**, where the CPU changes privilege level. That boundary is what lets user code run directly on the processor while still keeping the system secure and reliable.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `f254d98fdea5fbb2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `0.747006 vector_distance`

```text
of “what can be at user level, should be.” An extreme version of approach is to isolate
privileged, bu t less critical, parts of the operating system such as the file system or the
window system, from the rest of the kernel. This is called a microkernel design. In a
microkernel, the kernel itself is kept small, and instead most of the functionality of a
traditional operating system kernel is put into a set of user-level processes, or servers,
accessed from user applications via interprocess communication.
Performance. Finally, transferring control into the kernel is more expensive than a
procedure call to a library, and transferring control to a user-level file system server via
the kernel is still even more costly. Hardware designers have attempted to reduce the
```

#### Chunk 2

- Chunk ID: `5912bd2817ef4007`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `106`
- Score: `0.766962 vector_distance`

```text
Interposing on system calls is straightforward. The kernel uses a table lookup to determine
which routine to call for each system call invoked by the application program. The kernel can
redirect a system call to a new enhanced routine by simply changing the table entry.
A more interesting case is the memory system. Address translation hardware provides an
efficient way for the operating system to monitor and gain control on every memory reference
to a specific region of memory, while allowing other memory references to continue
unaffected. (Equivalently, software-based fault isolation provides many of the same hooks,
with different tradeoffs between interposition and execution speed.) This makes address
```

#### Chunk 3

- Chunk ID: `566b9ff495ff59da`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `67`
- Score: `0.778507 vector_distance`

```text
user process. To the user program, these are called like normal procedures, with
parameters and return values. The caller needs to be concerned only with the interface;
it does not need to know that the routine is actually being implemented by the kernel. The
kernel handles the details of checking and copying arguments, performing the operation,
and copying return values back into the process’s memory. When the kernel completes
the system call, it resumes user-level execution at the instruction immediately after the
trap.
2.3.2 Kernel to User Mode
Just as there are several different types of transitions from user to kernel mode, there are
several types of transitions from kernel to user mode:
New process. To start a new process, the kernel copies the program into memory, sets
```

#### Chunk 4

- Chunk ID: `38fd8d95935a2dc7`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `55`
- Score: `0.792877 vector_distance`

```text
even worse if it could corrupt the disk. This illustrates the principle of least privilege, that security and reliability are
enhanced if each part of the system has exactly the privileges it needs to do its job, and no more.
Figure 2.4: The operation of a CPU with kernel and user modes.
Figure 2.4 shows the operation of a dual-mode processor; the program counter and the mode
bit together control the processor’s operation. In turn, the mode bit is modified by some
instructions, just as the program counter is modified by some instructions.
What hardware is needed to let the operating system kernel protect applications and users
from one another, yet also let user code run directly on the processor? At a minimum, the
hardware must support three things:
```

#### Chunk 5

- Chunk ID: `d12ac4c54d6a5c31`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `0.799295 vector_distance`

```text
data through the kernel.
Operating systems use the system call interface to provide services to applications and to aid
in the internal structuring of the operating system itself. Almost all general-purpose computer
systems today have a user-level shell and/or a window manager that can start and manage
applications on behalf of the user. Many systems also implement parts of the operating system
as user-level services accessed through kernel pipes.
As we noted, a trend is for applications to become mini-operating systems in their own right,
with multiple users, resource sharing and allocation, untrusted third-party code, processor
and memory management, and so forth. The system call interfaces for Windows and UNIX
```

## q28

**Question:** Why does the operating system need timer interrupts at all? Why not just let each program run until it blocks or finishes?

### Method A

- Retrieval latency: 0.192s
- Generation latency: 6.158s

**Answer:**

Because if the OS simply let a program run until it blocks or finishes, one program could keep the CPU forever.

Timer interrupts let the kernel **periodically regain control**, even if the running program does not cooperate.

For example:

```c
while (1) {
    // infinite loop
}
```

This program never blocks and never finishes. Without timer interrupts, the OS might never get control back, so:

- other programs would not run,
- the system could appear frozen,
- the OS could not enforce fair CPU sharing,
- a malicious or buggy program could monopolize the processor.

A **hardware timer** is set by the kernel to interrupt after a short interval, e.g. every few milliseconds. When it fires:

1. the CPU switches from user mode to kernel mode,
2. the kernel’s timer interrupt handler runs,
3. the kernel decides whether to continue the same process or switch to another one.

So timer interrupts are what make **preemptive multitasking** possible.

Without them, the OS would rely on programs voluntarily giving up the CPU, which is unsafe and unreliable.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `905609ac17d0bf9a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `0.688724 vector_distance`

```text
Almost all computer systems include a device called a hardware timer, which can be set to
interrupt the processor after a specified delay (either in time or after some number of
instructions have been executed). Each timer interrupts only one processor, so a
multiprocessor will usually have a separate timer for each CPU. The operating system might
set each timer to expire every few milliseconds; human reaction time is a few hundred of
milliseconds. Resetting the timer is a privileged ope ration, accessible only within the kernel,
so that the user-level process cannot inadvertently or maliciously disable the timer.
When the timer interrupt occurs, the hardware transfers control from the user process to the
```

#### Chunk 2

- Chunk ID: `09b9aaaf6f20b4d8`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `0.74654 vector_distance`

```text
When the timer interrupt occurs, the hardware transfers control from the user process to the
kernel running in kernel mode. Other hardware interrupts, such as to signal the processor that
an I/O device has completed its work, likewise transfer control from the user process to the
kernel. A timer or other interrupt does not imply that the program has an error; in most cases,
after resetting the timer, the operating system resumes execution of the process, setting the
mode, program counter and registers back to the values they had immediately before the
interrupt occurred. We discuss the hardware and kernel mechanisms for implementing
interrupts in Section 2.4.
EXAMPLE: How does the kernel know if an application is in an infinite loop?
```

#### Chunk 3

- Chunk ID: `565c33044a95f75a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `65`
- Score: `0.771016 vector_distance`

```text
hardware saves the current execution state and starts executing at a specially designated
interrupt handler in the kernel. On a multiprocessor, an interrupt is taken on only one of
the processors; the others continue to execute as if nothing happened.
Each different type of interrupt requires its own handler. For timer interrupts, the handler
checks if the current process is being responsive to user input to detect if the process has
gone into an infinite loop. T he timer handler can also switch execution to a different
process to ensure that each process gets a turn. If no change is needed, the timer handler
resumes execution at the interrupted instruction, transparently to the user process.
Interrupts are also used to inform the kernel of the completion of I/O requests. For
```

#### Chunk 4

- Chunk ID: `dd6e0925cbe84941`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `71`
- Score: `0.786975 vector_distance`

```text
interrupt or system call handler. For example, a timer interrupt handler might decide to give
the processor to a different process. Likewise, a system call might need to wait for an I/O
operation to complete; in the meantime, some other process should run. With per-process
```

#### Chunk 5

- Chunk ID: `e918b7c40a5834be`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `56`
- Score: `0.789198 vector_distance`

```text
Timer Interrupts. Regardless of what the process does, the kernel must have a way to
periodically regain control from the current process. (Section 2.2.3 )
In addition, the hardware must also provide a way to safely transfer control from user mode
to kernel mode and back. As the mechanisms to do t his are relatively involved, we defer the
discussion of that topic to Sections 2.3 and  2.4.
The processor status register and privilege levels
Conceptually, the kernel/user mode is a one-bit register. When set to 1, the processor is in kernel mode and can do anything.
When set to 0, the processor is in user mode and is restricted. On most processors, the kernel/user mode is stored in the
```

### Method B

- Retrieval latency: 0.378s
- Generation latency: 8.454s

**Answer:**

The OS needs **timer interrupts** so it can regain control of the CPU even if the currently running program does not voluntarily give it up.

If the OS only let each program run until it **blocks** or **finishes**, then scheduling would be purely cooperative. That causes problems:

1. **A CPU-bound program might never block**
   ```c
   while (1) {
       // compute forever
   }
   ```
   If this program never performs I/O and never exits, it could monopolize the CPU forever.

2. **Other programs would become unresponsive**
   Your editor, browser, terminal, music player, etc. might not get CPU time if one process keeps running.

3. **The OS could not enforce fairness**
   Timer interrupts let the OS say: “This process has had enough time; now another process gets a turn.”

4. **The OS can preempt buggy or malicious programs**
   A program does not need to cooperate. The hardware timer interrupts it automatically after a short interval.

So the basic idea is:

1. The OS sets a hardware timer.
2. A user program runs.
3. When the timer expires, hardware interrupts the CPU.
4. Control transfers to the kernel.
5. The OS decides whether to resume the same process or switch to another one.

Without timer interrupts, a badly written or intentionally malicious program could take over the CPU indefinitely. Timer interrupts are what make **preemptive multitasking** possible.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `09b9aaaf6f20b4d8`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `4.03056 rerank_score`

```text
When the timer interrupt occurs, the hardware transfers control from the user process to the
kernel running in kernel mode. Other hardware interrupts, such as to signal the processor that
an I/O device has completed its work, likewise transfer control from the user process to the
kernel. A timer or other interrupt does not imply that the program has an error; in most cases,
after resetting the timer, the operating system resumes execution of the process, setting the
mode, program counter and registers back to the values they had immediately before the
interrupt occurred. We discuss the hardware and kernel mechanisms for implementing
interrupts in Section 2.4.
EXAMPLE: How does the kernel know if an application is in an infinite loop?
```

#### Chunk 2

- Chunk ID: `905609ac17d0bf9a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `3.85985 rerank_score`

```text
Almost all computer systems include a device called a hardware timer, which can be set to
interrupt the processor after a specified delay (either in time or after some number of
instructions have been executed). Each timer interrupts only one processor, so a
multiprocessor will usually have a separate timer for each CPU. The operating system might
set each timer to expire every few milliseconds; human reaction time is a few hundred of
milliseconds. Resetting the timer is a privileged ope ration, accessible only within the kernel,
so that the user-level process cannot inadvertently or maliciously disable the timer.
When the timer interrupt occurs, the hardware transfers control from the user process to the
```

#### Chunk 3

- Chunk ID: `7fe488991c560890`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `47`
- Score: `2.47952 rerank_score`

```text
Involuntary. An interrupt or processor exception could invoke an interrupt handler.
The interrupt hardware saves the state of the running thread and executes the handler’s
code. The handler can decide that some other thread should run, and then switch to it.
Alternatively, if the current thread should continue running, the handler restores the state
of the interrupted thread and resumes execution.
For example, many thread systems are designed to ensure that no thread can monopolize
the processor. To accomplish this, they set a hardware timer to interrupt the processor
periodically (e.g., every few milliseconds). The timer interrupt handler saves the state
of the running thread, chooses another thread to run, and runs that thread by restoring its
state to the processor.
```

#### Chunk 4

- Chunk ID: `dd6e0925cbe84941`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `71`
- Score: `2.12869 rerank_score`

```text
interrupt or system call handler. For example, a timer interrupt handler might decide to give
the processor to a different process. Likewise, a system call might need to wait for an I/O
operation to complete; in the meantime, some other process should run. With per-process
```

#### Chunk 5

- Chunk ID: `366a7a55bce59c1a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `86`
- Score: `2.09961 rerank_score`

```text
To allow applications to implement operating system-like functionality, we need something
more. For many of the reasons that kernels need interrupt-based event delivery, applications
can also benefit from being told when events occur that need their immediate attention.
Throughout this book , we will see this pattern repeatedly: the need to virtualize some part of
the kernel so that applications can behave more like operating systems. We call virtualized
interrupts and exceptions upcalls. In UNIX, they are called signals; in Windows, they are
asynchronous  events.
There are several uses for immediate event delivery with upcalls:
Preemptive user-level threads. Just as the operating system kernel runs multiple
```

### Method C

- Retrieval latency: 0.901s
- Generation latency: 7.981s

**Answer:**

Because if the OS only let a program run until it **blocks** or **finishes**, then the system would depend on programs being cooperative.

That causes problems:

1. **A program might never block or finish**
   ```c
   while (1) {
       // do work forever
   }
   ```
   Without timer interrupts, the OS might never regain control of the CPU. One buggy or malicious program could freeze the machine.

2. **Fairness**
   If one CPU-bound program keeps computing, other programs may not get a turn. Timer interrupts let the OS periodically stop the current program and schedule another one.

3. **Responsiveness**
   The OS needs to react to user input, redraw windows, handle networking, etc. If a program runs too long uninterrupted, the system feels stuck.

4. **Preemption**
   Timer interrupts allow **preemptive multitasking**: the OS can interrupt a running process even if that process did not voluntarily give up the CPU.

So the timer is basically the OS’s “alarm clock.” Every few milliseconds, hardware interrupts the CPU, control returns to the kernel, and the kernel can decide:

- resume the same program, or
- switch to another program.

Without timer interrupts, multitasking would be mostly **cooperative**, meaning programs would have to voluntarily yield the CPU. That is simpler, but much less safe and reliable.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `905609ac17d0bf9a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `n/a `

```text
Almost all computer systems include a device called a hardware timer, which can be set to
interrupt the processor after a specified delay (either in time or after some number of
instructions have been executed). Each timer interrupts only one processor, so a
multiprocessor will usually have a separate timer for each CPU. The operating system might
set each timer to expire every few milliseconds; human reaction time is a few hundred of
milliseconds. Resetting the timer is a privileged ope ration, accessible only within the kernel,
so that the user-level process cannot inadvertently or maliciously disable the timer.
When the timer interrupt occurs, the hardware transfers control from the user process to the
```

#### Chunk 2

- Chunk ID: `09b9aaaf6f20b4d8`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `64`
- Score: `n/a `

```text
When the timer interrupt occurs, the hardware transfers control from the user process to the
kernel running in kernel mode. Other hardware interrupts, such as to signal the processor that
an I/O device has completed its work, likewise transfer control from the user process to the
kernel. A timer or other interrupt does not imply that the program has an error; in most cases,
after resetting the timer, the operating system resumes execution of the process, setting the
mode, program counter and registers back to the values they had immediately before the
interrupt occurred. We discuss the hardware and kernel mechanisms for implementing
interrupts in Section 2.4.
EXAMPLE: How does the kernel know if an application is in an infinite loop?
```

#### Chunk 3

- Chunk ID: `565c33044a95f75a`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `65`
- Score: `n/a `

```text
hardware saves the current execution state and starts executing at a specially designated
interrupt handler in the kernel. On a multiprocessor, an interrupt is taken on only one of
the processors; the others continue to execute as if nothing happened.
Each different type of interrupt requires its own handler. For timer interrupts, the handler
checks if the current process is being responsive to user input to detect if the process has
gone into an infinite loop. T he timer handler can also switch execution to a different
process to ensure that each process gets a turn. If no change is needed, the timer handler
resumes execution at the interrupted instruction, transparently to the user process.
Interrupts are also used to inform the kernel of the completion of I/O requests. For
```

#### Chunk 4

- Chunk ID: `e5a31293091b6095`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `73`
- Score: `n/a `

```text
To simplify the kernel design, the hardware provides a privileged instruction to temporarily
defer delivery of an interrupt until it is safe to do s o. On the x86 and several other
processors, this instruction is called disable interrupts. However, this is a misnomer: the
interrupt is only deferred (masked), and not ignored. Once a corresponding enable interrupts
instruction is executed, any pending interrupts are delivered to the processor. The instructions
to mask and unmask interrupts must be privileged; otherwise, user code could inadvertently
or maliciously disable the hardware timer, allowing the machine to freeze.
If multiple interrupts arrive while interrupts are disabled, the hardware delivers them in turn
```

#### Chunk 5

- Chunk ID: `7fe488991c560890`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `47`
- Score: `n/a `

```text
Involuntary. An interrupt or processor exception could invoke an interrupt handler.
The interrupt hardware saves the state of the running thread and executes the handler’s
code. The handler can decide that some other thread should run, and then switch to it.
Alternatively, if the current thread should continue running, the handler restores the state
of the interrupted thread and resumes execution.
For example, many thread systems are designed to ensure that no thread can monopolize
the processor. To accomplish this, they set a hardware timer to interrupt the processor
periodically (e.g., every few milliseconds). The timer interrupt handler saves the state
of the running thread, chooses another thread to run, and runs that thread by restoring its
state to the processor.
```

## q29

**Question:** If a process is isolated from others, how can it still communicate with other processes at all?

### Method A

- Retrieval latency: 0.418s
- Generation latency: 7.130s

**Answer:**

A process is isolated **by default**, but the operating system can provide **controlled ways** for processes to communicate.

Isolation means a process cannot freely access another process’s memory or resources. It cannot just read or overwrite another process’s data directly. But the OS can allow communication through safe mechanisms, such as:

- **Pipes**: one process writes output, another reads it  
  Example: `ls | grep txt`
- **Files**: one process writes data to disk, another reads it later
- **Sockets**: processes communicate over a network or locally
- **Shared memory**: the OS maps the same memory region into multiple processes
- **Signals / events**: one process can notify another
- **Message queues** or other IPC mechanisms

The key idea is:

> Processes do not communicate by breaking isolation.  
> They communicate through OS-approved interfaces.

So isolation protects processes from accidental or malicious interference, while **interprocess communication (IPC)** allows sharing when it is explicitly requested and permitted.

A simple analogy: isolated processes are like people in separate rooms. They cannot enter each other’s rooms, but they can still communicate through a phone, a mailbox, or a shared whiteboard controlled by the building.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6e8f98c147e5f47b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `34`
- Score: `2.92832 rerank_score`

```text
process an attachment in an isolated execution environment with limited capabilities, then
even attachments containing viruses would do n o harm.
Complicating matters is that the operating system must not only prevent unwanted access to
shared data, it must also allow access in many cases. Users and programs must be able to
interact with each other, so that it is possible to cut and paste text between different
applications, and to share data written to disk or over the network. If each program were
completely standalone and never needed to interact with any other program, then fault
isolation by itself would be sufficient. However, we not only want to isolate programs from
one another, but to easily share data between programs and between users.
```

#### Chunk 2

- Chunk ID: `1460198edf710f43`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `98`
- Score: `0.415825 rerank_score`

```text
provide applications?
Process management. Can a program create an instance of another program? Wait for it
to complete? Stop or resume another running program? Send it an asynchronous event?
Input/output. How do pr ocesses communicate with devices attached to the computer
and through them to the physical world? Can processes communicate with each other?
Thread management. Can we create multiple activities or threads that share memory or
other resources within a process? Can we stop and start threads? How do w e
synchronize their use of shared data structures?
Memory management. Can a process ask for more (or less) memory space? Can it
share the same physical memory region with other processes?
File systems and storage. How does a process store the user’s data persistently so that
```

#### Chunk 3

- Chunk ID: `2ca581d91e5d2adb`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `93`
- Score: `0.218605 rerank_score`

```text
due to better hardware reliability and automated bug tracking, process isolation has been a
key technology in constructing more reliable system software.
Process isolation is also essential to building more secure computer systems. Without
isolation, computer users would be forced to trust every application loaded onto the
computer, not just the operating system code. In practice, however, complete process
isolation remains more an aspiration than a reality. Most operating systems are vulnerable to
```

#### Chunk 4

- Chunk ID: `91afdf895b707f9e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `115`
- Score: `-0.100672 rerank_score`

```text
For this to work, we need a way for processes to communicate with each other. Three widely
used forms of interprocess communication are:
Producer-consumer. In this model, programs are structured to accept as input the output
of other programs. Communication is one-way: the producer only writes, and the
consumer only reads. As we explained above , this allows chaining: a consumer can be,
in turn, a producer for a different process. Much of the success of UNIX was due to its
ability to easily compose many different programs together in this fashion.
```

#### Chunk 5

- Chunk ID: `073f3c8b40367405`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `18`
- Score: `-0.6176 rerank_score`

```text
Address translation is a simple concept, but it turns out to be incredibly pow erful. What can
an operating system do w ith address translation? This is only a partial list:
Process isolation. As we discussed in Chapter 2, pr otecting the operating system kernel
and other applications against buggy or malicious code requires the ability to limit
memory references by applications. Likewise, address translation can be used by
applications to construct safe execution sandbox es for third party extensions.
Interprocess communication. Often processes need to coordinate with each other, and
an efficient way to do t hat is to have the processes share a common memory region.
Shared code segments. Instances of the same program can share the program’s
```

### Method B

- Retrieval latency: 0.869s
- Generation latency: 6.631s

**Answer:**

Process isolation means a process **cannot directly access or modify another process’s private memory or resources**.

But processes can still communicate through **controlled mechanisms provided by the operating system**.

The OS acts like a mediator:

- A process cannot just read another process’s memory.
- But it can ask the OS to send data through an approved channel.

Common examples of interprocess communication include:

- **Pipes**: one process writes output, another reads it  
  Example: in UNIX/Linux:

  ```bash
  ls | grep ".txt"
  ```

  Here `ls` and `grep` are separate processes, but the OS connects the output of one to the input of the other.

- **Sockets**: processes communicate over a network or locally.
- **Shared memory**: the OS allows two processes to access a specific shared region, but only if permitted.
- **Files**: one process writes data to a file, another reads it.

So the key idea is:

> Isolation prevents uncontrolled access. Communication allows controlled sharing through OS-managed channels.

This way, processes can cooperate without being able to freely interfere with each other.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6e8f98c147e5f47b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `34`
- Score: `0.797921 vector_distance`

```text
process an attachment in an isolated execution environment with limited capabilities, then
even attachments containing viruses would do n o harm.
Complicating matters is that the operating system must not only prevent unwanted access to
shared data, it must also allow access in many cases. Users and programs must be able to
interact with each other, so that it is possible to cut and paste text between different
applications, and to share data written to disk or over the network. If each program were
completely standalone and never needed to interact with any other program, then fault
isolation by itself would be sufficient. However, we not only want to isolate programs from
one another, but to easily share data between programs and between users.
```

#### Chunk 2

- Chunk ID: `bddf5e45b943b100`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `115`
- Score: `0.864409 vector_distance`

```text
3.4 Case Study: Interprocess Communication
For many of the same reasons it makes sense to construct complex applications from simpler
modules, it often makes sense to create applications that can specialize on a specific task, and
then combine those applications into more complex structures. We gave an example above
with the C compiler, but many parts of the operating system are structured this way. For
example, instead of every program needing to know how to coordinate access to a printer,
UNIX has a printer server, a specialized program for managing the printer queue.
For this to work, we need a way for processes to communicate with each other. Three widely
used forms of interprocess communication are:
```

#### Chunk 3

- Chunk ID: `91afdf895b707f9e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `115`
- Score: `0.890077 vector_distance`

```text
For this to work, we need a way for processes to communicate with each other. Three widely
used forms of interprocess communication are:
Producer-consumer. In this model, programs are structured to accept as input the output
of other programs. Communication is one-way: the producer only writes, and the
consumer only reads. As we explained above , this allows chaining: a consumer can be,
in turn, a producer for a different process. Much of the success of UNIX was due to its
ability to easily compose many different programs together in this fashion.
```

#### Chunk 4

- Chunk ID: `edec91efe8186f80`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `24`
- Score: `0.937362 vector_distance`

```text
Fault isolation requires restricting the behavior of applications to less than the full
power of the underlying hardware. Otherwise, any application downloaded off the web,
or any script embedded in a web page, could completely control the machine. Any
application could install spyware into the operating system to log every keystroke you
type, or record the password to every web site you visit. Without fault isolation
provided by the operating system, any bug in any program might irretrievably corrupt the
disk. Error-prone or malignant applications could cause all sorts of havoc.
Communication. The flip side of isolation is the need for communication between
different applications and different users. For example, a web site may be implemented
```

#### Chunk 5

- Chunk ID: `2ca581d91e5d2adb`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `93`
- Score: `0.959442 vector_distance`

```text
due to better hardware reliability and automated bug tracking, process isolation has been a
key technology in constructing more reliable system software.
Process isolation is also essential to building more secure computer systems. Without
isolation, computer users would be forced to trust every application loaded onto the
computer, not just the operating system code. In practice, however, complete process
isolation remains more an aspiration than a reality. Most operating systems are vulnerable to
```

### Method C

- Retrieval latency: 0.780s
- Generation latency: 6.288s

**Answer:**

Process isolation does **not** mean processes can never interact. It means they cannot access each other’s memory or resources **directly and arbitrarily**.

Instead, the operating system provides **controlled communication mechanisms**.

For example, two isolated processes cannot normally do this:

```text
Process A directly reads/writes Process B's memory
```

because that would break fault isolation and security.

But they can communicate through OS-managed channels, such as:

- **pipes**
- **files**
- **sockets**
- **shared memory**
- **message queues**
- **signals**

The key idea is:

```text
Isolation prevents uncontrolled access.
Communication allows controlled access.
```

For instance, in a UNIX-style producer-consumer setup:

```text
process1 | process2
```

`process1` writes output to a pipe, and `process2` reads input from that pipe. They are still isolated processes, but the OS gives them a safe communication channel.

So the OS has two jobs that seem opposite but must work together:

1. **Protect processes from each other**
2. **Allow them to share data when permitted**

That is why isolation and interprocess communication are both core operating system features.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6e8f98c147e5f47b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `34`
- Score: `n/a `

```text
process an attachment in an isolated execution environment with limited capabilities, then
even attachments containing viruses would do n o harm.
Complicating matters is that the operating system must not only prevent unwanted access to
shared data, it must also allow access in many cases. Users and programs must be able to
interact with each other, so that it is possible to cut and paste text between different
applications, and to share data written to disk or over the network. If each program were
completely standalone and never needed to interact with any other program, then fault
isolation by itself would be sufficient. However, we not only want to isolate programs from
one another, but to easily share data between programs and between users.
```

#### Chunk 2

- Chunk ID: `91afdf895b707f9e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `115`
- Score: `n/a `

```text
For this to work, we need a way for processes to communicate with each other. Three widely
used forms of interprocess communication are:
Producer-consumer. In this model, programs are structured to accept as input the output
of other programs. Communication is one-way: the producer only writes, and the
consumer only reads. As we explained above , this allows chaining: a consumer can be,
in turn, a producer for a different process. Much of the success of UNIX was due to its
ability to easily compose many different programs together in this fashion.
```

#### Chunk 3

- Chunk ID: `edec91efe8186f80`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `24`
- Score: `n/a `

```text
Fault isolation requires restricting the behavior of applications to less than the full
power of the underlying hardware. Otherwise, any application downloaded off the web,
or any script embedded in a web page, could completely control the machine. Any
application could install spyware into the operating system to log every keystroke you
type, or record the password to every web site you visit. Without fault isolation
provided by the operating system, any bug in any program might irretrievably corrupt the
disk. Error-prone or malignant applications could cause all sorts of havoc.
Communication. The flip side of isolation is the need for communication between
different applications and different users. For example, a web site may be implemented
```

#### Chunk 4

- Chunk ID: `c11370933bb8b781`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `103`
- Score: `n/a `

```text
communication? (Section 3.2)
Case study: Implementing a shell. We will illustrate these interfaces by using them to
implement a user-level job control system called a shell. (Section 3.3)
Case study: Interprocess communication. How does the communication between a
client and server work? (Section 3.4)
Operating system structure. Can we use the process abstraction to simplify the
construction of the operating system itself and to make it more secure, more reliable, and
more flexible? (Section 3.5)
3.1 Process Management
On a modern computer, when a user clicks on a file or application icon, the application starts
up. How does this happen and who is called? Of course, we could implement everything that
```

#### Chunk 5

- Chunk ID: `01d4b1ca6d9511b5`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `23`
- Score: `n/a `

```text
the user could ask the operating system to force the looping program to exit.
Isolation. An error in one application should not disrupt other applications, or even the
operating system itself. This is called fault isolation. Anyone who has taken an
introductory computer science class knows the value of an operating system that can
protect itself and other applications from programmer bugs. Debugging would be vastly
harder if an error in one program could corrupt data structures in other applications.
Likewise, dow nloading and installing a screen saver or other application should not
crash unrelated programs, provide a way for a malicious attacker to surreptitiously
install a computer virus, or let one user access or change another’s data without
permission.
```

## q30

**Question:** Why is a process usually described as an abstraction rather than just “a program that is running”?

### Method A

- Retrieval latency: 0.345s
- Generation latency: 7.685s

**Answer:**

A process is often called an **abstraction** because it is more than just “a program that is running.”

A **program** is mainly the passive code and data stored in an executable file.

A **process** is the operating system’s model of an executing program instance. It includes things like:

- the program’s code and data in memory
- the current CPU state, such as registers and program counter
- its stack and heap
- open files and other resources
- permissions/privileges
- scheduling information stored by the OS, often in a **process control block (PCB)**

So “a running program” is a useful informal description, but it is incomplete.

Also, a process is not always literally running on the CPU. It may be:

- running
- ready to run
- blocked waiting for input/output
- suspended

Yet we still call it a process.

It is an **abstraction** because the OS creates the illusion that each program has its own private CPU, memory, and resources, even though the real hardware is shared among many processes. The source describes this as the OS providing a sandbox for executing untrusted user-level code.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d28085dcbd23f6e4`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `98`
- Score: `2.7933 rerank_score`

```text
3. The Programming Interface
From a programmer’s point of view, the user is a peripheral that types when you issue a read
request. —Peter Williams
The previous chapter concerned the mechanisms needed in the operating system kernel to
implement the process abstraction. A process is an instance of a program — the kernel
provides an efficient sandbox  for executing untrusted code at user-level, running user code
directly on the processor.
This chapter concerns how we choose to use the process abstraction: what functionality does
the operating system provide applications, and what should go where — w hat functionality
should be put in the operating system kernel, what should be put into user-level libraries, and
how should the operating system itself be organized?
```

#### Chunk 2

- Chunk ID: `bff39cd5beba52c2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `51`
- Score: `0.180365 rerank_score`

```text
including the operating system itself.
2.1 The Process Abstraction
In the model you are likely familiar with, illustrated in Figure 2.2, a programmer types code
in some high-level language. A compiler converts that code into a sequence of machine
instructions and stores those instructions in a file, called the program’s executable image.
The compiler also defines any static data the program needs, along with its initial values, and
includes them in the executable image.
```

#### Chunk 3

- Chunk ID: `c87c8591768a3e1b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `50`
- Score: `0.0609325 rerank_score`

```text
personality. When running the operating system kernel, the processor is like a warden in
charge of an insane asylum with complete access to everything. At other times, the processor
runs application code in a process — the processor becomes an inmate, wearing a
straightjacket locked in a padded cell by the warden, protected from harming anyone else. Of
course, it is the same processor in both cases, sometimes completely trustworthy and at other
times completely untrusted.
Chapter roadmap: Protection raises several important questions that we will answer in the
rest of the chapter:
The Process Abstraction. What is a process and how does it differ from a program?
(Section 2.1)
Dual-Mode Operation. What hardware enables the operating system to efficiently
```

#### Chunk 4

- Chunk ID: `6731441d4f6d6c4b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `52`
- Score: `-0.547653 rerank_score`

```text
now, we will keep things simple and assume the operating system makes a separate copy of
the entire program for each process.
Thus, a process is an instance of a program, in much the same way that an object is an
instance of a class in object-oriented programming. Each program can have zero, on e or more
processes executing it. For each instance of a program, there is a process with its own copy
of the program in memory.
The operating system keeps track of the various processes on the computer using a data
structure called the process control block, or PCB. The PCB stores all the information the
operating system needs about a particular process: where it is stored in memory, where its
executable image resides on disk, which user asked it to execute, what privileges the process
```

#### Chunk 5

- Chunk ID: `a6429c2f10f32953`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `35`
- Score: `-0.967972 rerank_score`

```text
All operating systems provide applications with an abstraction of the underlying computer
hardware; a portable abstraction is one that does not change as the hardware changes. A
program written for Microsoft’s Windows 8 should run correctly regardless of whether a
specific graphics card is being used, whether persistent storage is provided via flash memory
or rotating magnetic disk, or whether the network is Bluetooth, WiFi, or gigabit Ethernet.
Portability also applies to the operating system itself. As we have noted, operating systems
are among the most complex software systems ever invented, making it impractical to re-
write them from scratch every time new hardware is produced or a new application is
```

### Method B

- Retrieval latency: 0.206s
- Generation latency: 6.915s

**Answer:**

Because **“a program that is running” is only a rough description**. A **process** is better called an **abstraction** because the operating system creates a whole *model/interface* around running code.

A **program** is just the executable image: instructions + static data stored in a file.

A **process** is an OS-managed execution environment for that program. It includes things like:

- its own memory/address space
- program counter and CPU register state
- stack and heap
- open files and other resources
- permissions/owner information
- scheduling state
- a process control block (PCB) the OS uses to track it

So the OS gives the illusion that the program has its own private CPU and memory, even though many processes may be sharing the same physical machine.

That is why we say:

> A process is an **instance of a program**, managed by the OS.

Like in object-oriented terms:

> program : process ≈ class : object

So “a running program” is not wrong informally, but **“process abstraction”** emphasizes that the OS is providing a protected, managed environment in which that program executes.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bff39cd5beba52c2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `51`
- Score: `0.764395 vector_distance`

```text
including the operating system itself.
2.1 The Process Abstraction
In the model you are likely familiar with, illustrated in Figure 2.2, a programmer types code
in some high-level language. A compiler converts that code into a sequence of machine
instructions and stores those instructions in a file, called the program’s executable image.
The compiler also defines any static data the program needs, along with its initial values, and
includes them in the executable image.
```

#### Chunk 2

- Chunk ID: `d28085dcbd23f6e4`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `98`
- Score: `0.833922 vector_distance`

```text
3. The Programming Interface
From a programmer’s point of view, the user is a peripheral that types when you issue a read
request. —Peter Williams
The previous chapter concerned the mechanisms needed in the operating system kernel to
implement the process abstraction. A process is an instance of a program — the kernel
provides an efficient sandbox  for executing untrusted code at user-level, running user code
directly on the processor.
This chapter concerns how we choose to use the process abstraction: what functionality does
the operating system provide applications, and what should go where — w hat functionality
should be put in the operating system kernel, what should be put into user-level libraries, and
how should the operating system itself be organized?
```

#### Chunk 3

- Chunk ID: `6731441d4f6d6c4b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `52`
- Score: `0.908023 vector_distance`

```text
now, we will keep things simple and assume the operating system makes a separate copy of
the entire program for each process.
Thus, a process is an instance of a program, in much the same way that an object is an
instance of a class in object-oriented programming. Each program can have zero, on e or more
processes executing it. For each instance of a program, there is a process with its own copy
of the program in memory.
The operating system keeps track of the various processes on the computer using a data
structure called the process control block, or PCB. The PCB stores all the information the
operating system needs about a particular process: where it is stored in memory, where its
executable image resides on disk, which user asked it to execute, what privileges the process
```

#### Chunk 4

- Chunk ID: `242f8595299cbdf5`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `53`
- Score: `0.950683 vector_distance`

```text
Organizing the operating system as a cooperating set of processes proved immensely successful, and soon almost every new
operating system was built this way, including systems that also provided protection against malicious or buggy user
programs. At the time, almost all user programs were simple, single-threaded programs with only one program counter and
one stack, so there was no confusion. A process was needed to run a program, that is, a single sequential execution stream
with a protection boundary.
As parallel computers became more popular, though, we once again needed a word for a logical sequence of instructions. A
multiprocessor program can have multiple instruction sequences running in parallel, each with its own program counter, but all
```

#### Chunk 5

- Chunk ID: `b6997290100ab21d`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `53`
- Score: `0.955827 vector_distance`

```text
Processes, lightweight processes, and threads
The word “process", like many terms in computer science, has evolved over time. The evolution of words can sometimes trip
up the unwary — systems built at different times will use the same word in significantly different ways.
A “process" was originally coined to mean what is now called a “thread" — a logical sequence of instructions that executes
either operating system or application code. The concept of a process was developed as a way of simplifying the correct
construction of early operating systems that provided no protection between application programs.
Organizing the operating system as a cooperating set of processes proved immensely successful, and soon almost every new
```

### Method C

- Retrieval latency: 0.695s
- Generation latency: 8.011s

**Answer:**

A process is described as an **abstraction** because it is more than just the raw fact that “a program is running.”

A **program** is usually a passive thing: an executable file, code stored on disk.

A **process** is the operating system’s abstraction for an executing program instance. It gives the program the illusion that it has its own controlled environment, including things like:

- its own address space / memory view
- program counter and stack, for simple single-threaded processes
- permissions and privileges
- open files and other resources
- scheduling state
- protection from other processes

So “a program that is running” is a useful informal description, but it is incomplete.

For example, you can run the same program twice:

```text
firefox
firefox
```

That is one program, but two separate processes. Each process has its own memory, state, resources, and identity in the OS.

The textbook distinction is roughly:

> A process is an instance of a program executing with restricted rights.

So we call it an abstraction because the OS hides the messy hardware details and presents a cleaner model: “this running computation has its own protected execution environment.”

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `242f8595299cbdf5`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `53`
- Score: `n/a `

```text
Organizing the operating system as a cooperating set of processes proved immensely successful, and soon almost every new
operating system was built this way, including systems that also provided protection against malicious or buggy user
programs. At the time, almost all user programs were simple, single-threaded programs with only one program counter and
one stack, so there was no confusion. A process was needed to run a program, that is, a single sequential execution stream
with a protection boundary.
As parallel computers became more popular, though, we once again needed a word for a logical sequence of instructions. A
multiprocessor program can have multiple instruction sequences running in parallel, each with its own program counter, but all
```

#### Chunk 2

- Chunk ID: `b6997290100ab21d`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `53`
- Score: `n/a `

```text
Processes, lightweight processes, and threads
The word “process", like many terms in computer science, has evolved over time. The evolution of words can sometimes trip
up the unwary — systems built at different times will use the same word in significantly different ways.
A “process" was originally coined to mean what is now called a “thread" — a logical sequence of instructions that executes
either operating system or application code. The concept of a process was developed as a way of simplifying the correct
construction of early operating systems that provided no protection between application programs.
Organizing the operating system as a cooperating set of processes proved immensely successful, and soon almost every new
```

#### Chunk 3

- Chunk ID: `f32832dd0bac0984`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `52`
- Score: `n/a `

```text
executable image resides on disk, which user asked it to execute, what privileges the process
has, and so forth.
Earlier, we defined a process as an instance of a program executing with restricted rights.
Each of these roles — e xecution and protection — is important enough to merit several
chapters.
This chapter focuses on protection, and so we limit our discussion to simple processes, each
with one program counter, code, data, heap, and stack.
Some programs consist of multiple concurrent activities, or threads. A web browser, for
example, might need to receive user input at the same time it is drawing the screen or
receiving network input. Each of these separate activities has its own program counter and
```

#### Chunk 4

- Chunk ID: `34a9cfe6f686fbb9`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `21`
- Score: `n/a `

```text
Thread Abstraction. What is the thread abstraction as seen by a programmer?
(Section 4.2)
Simple Thread API. How can programmers use threads? (Section 4.3)
Thread Data Structures. What data structures does the operating system use to manage
threads? (Section 4.4)
Thread Life Cycle. What states does a thread go through between initialization and
completion? (Section 4.5)
Implementing Kernel Threads. How do we implement the thread abstraction inside the
operating system kernel? (Section 4.6)
Combining Kernel Threads and Single-Threaded User Processes. How do we extend
the implementation of kernel threads to support simple single-threaded processes?
(Section 4.7)
Implementing Multi-threaded Processes. How do we implement the thread abstraction
for multi-threaded applications? (Section 4.8)
```

#### Chunk 5

- Chunk ID: `c87c8591768a3e1b`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `50`
- Score: `n/a `

```text
personality. When running the operating system kernel, the processor is like a warden in
charge of an insane asylum with complete access to everything. At other times, the processor
runs application code in a process — the processor becomes an inmate, wearing a
straightjacket locked in a padded cell by the warden, protected from harming anyone else. Of
course, it is the same processor in both cases, sometimes completely trustworthy and at other
times completely untrusted.
Chapter roadmap: Protection raises several important questions that we will answer in the
rest of the chapter:
The Process Abstraction. What is a process and how does it differ from a program?
(Section 2.1)
Dual-Mode Operation. What hardware enables the operating system to efficiently
```

## q31

**Question:** If a child process is created from a parent process, why doesn’t every process creation require copying the parent’s entire memory immediately?

### Method A

- Retrieval latency: 0.366s
- Generation latency: 5.054s

**Answer:**

Because modern UNIX-like systems usually use **copy-on-write** when creating a child process with `fork()`.

Instead of immediately copying all of the parent’s physical memory, the OS initially lets the parent and child **share the same memory pages**. Those pages are marked **read-only** for both processes.

Then:

- If neither process modifies a shared page, no copy is needed.
- If the parent or child tries to write to a shared page, the CPU raises an exception/page fault.
- The OS then copies only that specific page, so the writing process gets its own private copy.

This is efficient because very often after `fork()`, the child quickly calls `exec()` to load a new program. In that case, copying the parent’s entire memory would be wasted, because the child’s memory is about to be replaced anyway.

So process creation does not require an immediate full memory copy because the OS delays copying until it is actually necessary. This technique is called **copy-on-write**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `349a1396637e4d07`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `4.49792 rerank_score`

```text
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
same memory as the parent. If the child changes some data, it should change only its copy, and not its parent’s data. On the
other hand, most of the time, the child process in UNIX fork simply calls UNIX exec; the shared data is there as a
programming convenience.
We can make this work efficiently by using an idea called copy-on-write. During the fork, all of the segments shared
between the parent and child process are marked “read-only” in both segment tables. If either side modifies data in a
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
```

#### Chunk 2

- Chunk ID: `a998281d9450f7e7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `3.75979 rerank_score`

```text
UNIX fork and copy-on-write
In Chapter 3, we described the UNIX fork system call. UNIX creates a new process by making a complete copy of the
parent process; the parent process and the child process are identical except for the return value from fork. The child
process can then set up its I/O and eventually use the UNIX exec system call to run a new program. We promised at the
time we would explain how this can be done efficiently.
With segments, this is now possible. To fork a process, we can simply make a copy of the parent’s segment table; we do not
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
```

#### Chunk 3

- Chunk ID: `687a301a73fddf23`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `106`
- Score: `1.26436 rerank_score`

```text
by closing some files, ope ning others, reducing its priority if it is to run in the background,
etc. Because the child runs exactly the same code as the parent, it can be trusted to set up the
context for the new program correctly.
Once the context is set, the child process calls UNIX exec. UNIX exec brings the new
executable image into memory and starts it running. It may seem wasteful to make a complete
copy of the parent process, just to ove rwrite that copy when we bring in the new executable
image into memory using exec. It turns out that fork and exec can be implemented efficiently,
using a set of techniques we will describe in Chapter 8.
With this design, UNIX fork takes no arguments and returns an integer. UNIX exec takes two
```

#### Chunk 4

- Chunk ID: `7365e0088296fc8e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `105`
- Score: `1.17796 rerank_score`

```text
boolean CreateProcess(char *prog, char *args); 
We call the process creator the parent and the process being created, the child.
What steps does CreateProcess take? As we explained in the previous chapter, the kernel
needs to:
Create and initialize the process control block (PCB) in the kernel.
Create and initialize a new address space.
Load the program prog into the address space.
Copy arguments args into memory in the address space.
Initialize the hardware context to start execution at “start”.
Inform the scheduler that the new process is ready to run.
Unfortunately, there are quite a few aspects of the process that the parent might like to control,
such as: its privileges, where it sends its input and output, what it should store its files, what
```

#### Chunk 5

- Chunk ID: `72b15d27ccd5e293`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `106`
- Score: `0.119378 rerank_score`

```text
UNIX takes a different approach to process management, one that is complex in theory and
simple in practice. UNIX splits CreateProcess in two steps, called fork and exec, illustrated
in Figure 3.4.
Figure 3.4: The operation of the UNIX fork and exec system calls. UNIX fork makes a copy of the parent process; UNIX
exec changes the child process to run the new program.
UNIX fork creates a complete copy of the parent process, with one key exception. (We need
some way to distinguish between which copy is the parent and which is the child.) The child
process sets up privileges, priorities, and I/O for the program that is about to be started, e.g.,
by closing some files, ope ning others, reducing its priority if it is to run in the background,
```

### Method B

- Retrieval latency: 0.732s
- Generation latency: 5.723s

**Answer:**

Because modern OSes usually use **copy-on-write (COW)**.

When a child process is created with something like `fork()`, the OS does **not immediately copy all of the parent’s physical memory**. Instead:

- The parent and child initially **share the same physical memory pages/segments**.
- Those shared regions are marked **read-only** in both processes.
- If either process tries to modify a shared page, the CPU raises a protection fault.
- Then the OS copies **only that page/segment**, so the modifying process gets its own private copy.

So logically, the child looks like a copy of the parent, but physically the memory is only copied **when necessary**.

This is efficient because in UNIX-like systems, a common pattern is:

```c
fork();
exec();
```

The child often calls `exec()` almost immediately, replacing its memory with a new program. If the OS had copied the parent’s entire memory first, most of that work would be wasted.

So the short answer is:

> Process creation does not require immediate full memory copying because the OS can share memory initially and copy only modified parts later using copy-on-write.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `349a1396637e4d07`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `n/a `

```text
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
same memory as the parent. If the child changes some data, it should change only its copy, and not its parent’s data. On the
other hand, most of the time, the child process in UNIX fork simply calls UNIX exec; the shared data is there as a
programming convenience.
We can make this work efficiently by using an idea called copy-on-write. During the fork, all of the segments shared
between the parent and child process are marked “read-only” in both segment tables. If either side modifies data in a
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
```

#### Chunk 2

- Chunk ID: `83dd36ba17864c38`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `n/a `

```text
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
process modifies only its stack before calling UNIX exec, and if so, only the stack needs to be physically copied.
We can also use segments for interprocess communication, if processes are given read and
write permission to the same segment. Multics, an operating system from the 1960’ s that
contained many of the ideas we now find in Microsoft’s Windows 7, Apple’s Mac OS X, and
Linux, made extensive use of segmented memory for interprocess sharing. In Multics, a
segment was allocated for every data structure, allowing fine-grained protection and sharing
between processes. Of course, this made the segment table pretty large! More modern
```

#### Chunk 3

- Chunk ID: `38803452a731c236`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `25`
- Score: `n/a `

```text
Figure 8.4: Two processes sharing a code segment, but with separate data and stack segments. In this case, each process
uses the same virtual addresses, but these virtual addresses map to either the same region of physical memory (if code) or
different regions of physical memory (if data).
Although simple to implement and manage, segmented memory is both remarkably pow erful
and widely used. For example, the x86 architecture is segmented (with some enhancements
that we will describe later). With segments, the operating system can allow processes to
share some regions of memory while keeping other regions protected. For example, two
processes can share a code segment by setting up an entry in their segment tables to poi nt to
```

#### Chunk 4

- Chunk ID: `4a5417ec6df0231f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `n/a `

```text
Memory sharing. We want to allow multiple processes to share selected regions of
memory. These shared regions can be large (e.g., if we are sharing a program’s code
segment among multiple processes executing the same program) or relatively small (e.g.,
if we are sharing a common library, a file, or a shared data structure).
Flexible memory placement. We want to allow the operating system the flexibility to
place a process (and each part of a process) anywhere in physical memory; this will
allow us to pack physical memory more efficiently. As we will see in the next chapter,
flexibility in assigning process data to physical memory locations will also enable us to
make more effective use of on-chip caches.
Sparse addresses. Many programs have multiple dynamic memory regions that can
```

#### Chunk 5

- Chunk ID: `5f2b173f0f6f35a1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `n/a `

```text
Copy-on-write. Copy-on-write allows multiple processes to have logically separate
copies of the same memory region, backed by a single physical copy in memory. Each
page in the region is mapped read-only in each process; the operating system makes a
physical copy only when (and if) a page is modified.
Memory-mapped files. Disk files can be made part of a process’s virtual address
space, allowing the process to access the data in the file using normal processor
instructions. When a page from a memory-mapped file is first accessed, a protection
fault traps to the operating system so that it can bring the page into memory from disk.
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
```

### Method C

- Retrieval latency: 0.184s
- Generation latency: 5.758s

**Answer:**

Because modern OSes usually use **copy-on-write (COW)**.

When a child process is created with something like UNIX `fork`, the OS does **not immediately copy all of the parent’s physical memory**. Instead:

- The child gets its own address space metadata, e.g. page table / segment table.
- The parent’s and child’s memory mappings initially point to the same physical memory.
- Those shared pages/segments are marked **read-only**.
- If either process tries to modify one, the CPU raises an exception/page fault.
- Then the OS copies only that page/segment, so the modifying process gets its own private copy.

So the memory is copied **only if it is actually written to**.

This is efficient because often after `fork`, the child quickly calls `exec`, which replaces its memory with a new program anyway. In that common case, copying the parent’s entire memory would be wasted work.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `349a1396637e4d07`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `0.639854 vector_distance`

```text
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
same memory as the parent. If the child changes some data, it should change only its copy, and not its parent’s data. On the
other hand, most of the time, the child process in UNIX fork simply calls UNIX exec; the shared data is there as a
programming convenience.
We can make this work efficiently by using an idea called copy-on-write. During the fork, all of the segments shared
between the parent and child process are marked “read-only” in both segment tables. If either side modifies data in a
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
```

#### Chunk 2

- Chunk ID: `7365e0088296fc8e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `105`
- Score: `0.80969 vector_distance`

```text
boolean CreateProcess(char *prog, char *args); 
We call the process creator the parent and the process being created, the child.
What steps does CreateProcess take? As we explained in the previous chapter, the kernel
needs to:
Create and initialize the process control block (PCB) in the kernel.
Create and initialize a new address space.
Load the program prog into the address space.
Copy arguments args into memory in the address space.
Initialize the hardware context to start execution at “start”.
Inform the scheduler that the new process is ready to run.
Unfortunately, there are quite a few aspects of the process that the parent might like to control,
such as: its privileges, where it sends its input and output, what it should store its files, what
```

#### Chunk 3

- Chunk ID: `a998281d9450f7e7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `0.830527 vector_distance`

```text
UNIX fork and copy-on-write
In Chapter 3, we described the UNIX fork system call. UNIX creates a new process by making a complete copy of the
parent process; the parent process and the child process are identical except for the return value from fork. The child
process can then set up its I/O and eventually use the UNIX exec system call to run a new program. We promised at the
time we would explain how this can be done efficiently.
With segments, this is now possible. To fork a process, we can simply make a copy of the parent’s segment table; we do not
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
```

#### Chunk 4

- Chunk ID: `83dd36ba17864c38`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `0.884644 vector_distance`

```text
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
process modifies only its stack before calling UNIX exec, and if so, only the stack needs to be physically copied.
We can also use segments for interprocess communication, if processes are given read and
write permission to the same segment. Multics, an operating system from the 1960’ s that
contained many of the ideas we now find in Microsoft’s Windows 7, Apple’s Mac OS X, and
Linux, made extensive use of segmented memory for interprocess sharing. In Multics, a
segment was allocated for every data structure, allowing fine-grained protection and sharing
between processes. Of course, this made the segment table pretty large! More modern
```

#### Chunk 5

- Chunk ID: `687a301a73fddf23`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `106`
- Score: `0.888066 vector_distance`

```text
by closing some files, ope ning others, reducing its priority if it is to run in the background,
etc. Because the child runs exactly the same code as the parent, it can be trusted to set up the
context for the new program correctly.
Once the context is set, the child process calls UNIX exec. UNIX exec brings the new
executable image into memory and starts it running. It may seem wasteful to make a complete
copy of the parent process, just to ove rwrite that copy when we bring in the new executable
image into memory using exec. It turns out that fork and exec can be implemented efficiently,
using a set of techniques we will describe in Chapter 8.
With this design, UNIX fork takes no arguments and returns an integer. UNIX exec takes two
```

## q32

**Question:** If a microkernel keeps fewer things in the kernel, does that automatically make it better than a monolithic kernel?

### Method A

- Retrieval latency: 0.171s
- Generation latency: 5.985s

**Answer:**

No — a microkernel is **not automatically better** than a monolithic kernel.

It depends on the tradeoff you care about.

A **microkernel** keeps the kernel small and moves services like file systems, drivers, or networking into user-level servers. This can make the OS:

- easier to modularize
- easier to debug
- potentially more reliable, because a failed service may not crash the whole kernel

But it can also be **slower**, because applications may need extra communication steps through the kernel to reach those user-level services. That means more boundary crossings and interprocess communication overhead.

A **monolithic kernel** keeps more functionality inside the kernel. This can improve:

- performance
- tight integration between OS components

But it may be:

- harder to modify
- harder to debug
- less flexible

So the better answer is:

> A microkernel improves modularity and potentially reliability, but it can hurt performance. A monolithic kernel can be faster but less flexible.

That is why many real operating systems use a **hybrid design**, putting some services in the kernel and others at user level depending on the performance and complexity tradeoff.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4bda4c17854153be`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `0.644788 vector_distance`

```text
items more quickly. Some systems have moved other parts of the operating system into user-
level servers: the network stack, the file system, device drivers, and so forth.
The difference between a monolithic and a microkernel design is often transparent to the
application programmer. The location of the service can be hidden in a user-level library —
calls go to the library, which casts the requests either as system calls or as reads and writes
to the server through a pipe. The location of the server can also be hidden inside the kernel
— the application calls the kernel as if the kernel implements the service, but instead the
kernel reformats the request into a pipe that the server can read.
A microkernel design offers considerable benefit to the operating system developer, as it
```

#### Chunk 2

- Chunk ID: `a96cf2b2d991d58e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `120`
- Score: `0.761625 vector_distance`

```text
located on a different machine.
This has led ope rating system designers to wrestle with a fundamental tradeoff: by
centralizing functionality in the kernel, performance is improved and it makes it easier to
arrange tight integration between kernel modules. However, the resulting systems are less
flexible, less easy to change, and less adaptive to user or application needs. We discuss these
tradeoffs by describing several options for the operating system architecture.
3.5.1 Monolithic Kernels
```

#### Chunk 3

- Chunk ID: `0d2bd5db44000006`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `0.774253 vector_distance`

```text
A microkernel design offers considerable benefit to the operating system developer, as it
easier to modularize and debug user-level services than kernel code. Aside from a potential
reliability improvement, however, microkernels offer little in the way of visible benefit to
end users and can slow dow n overall performance by inserting extra steps between the
application and the services it needs. Thus, in practice, most systems adopt a hybrid model
where some operating system services are run at user-level and some are in the kernel,
depending on the specific tradeoff between code complexity and performance.
3.6 Summary and Future Directions
In this chapter, we have seen how system calls can be used by applications to create and
```

#### Chunk 4

- Chunk ID: `e75d1fc32abac4cd`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `0.842279 vector_distance`

```text
the kernel is still even more costly. Hardware designers have attempted to reduce the
cost of these boundary crossings, but their performance remains a problem. Microsoft
Windows NT, a precursor to Windows 7, w as initially designed as a microkernel, but
over time, much of its functionality has been migrated back into the kernel for
performance reasons.
Application-level sandboxing and operating system functionality
Applications that support executing third-party code or scripts in a restricted sandbox must address many of these same
questions, with the sandbox playing the role of the operating system kernel. In terms of functionality: Can the scripting code
start a new instance of itself? Can it do input/output? Can it perform work in the background? Can it store data persistently,
```

#### Chunk 5

- Chunk ID: `f254d98fdea5fbb2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `0.872375 vector_distance`

```text
of “what can be at user level, should be.” An extreme version of approach is to isolate
privileged, bu t less critical, parts of the operating system such as the file system or the
window system, from the rest of the kernel. This is called a microkernel design. In a
microkernel, the kernel itself is kept small, and instead most of the functionality of a
traditional operating system kernel is put into a set of user-level processes, or servers,
accessed from user applications via interprocess communication.
Performance. Finally, transferring control into the kernel is more expensive than a
procedure call to a library, and transferring control to a user-level file system server via
the kernel is still even more costly. Hardware designers have attempted to reduce the
```

### Method B

- Retrieval latency: 0.971s
- Generation latency: 5.890s

**Answer:**

No — a microkernel is not automatically better than a monolithic kernel.

A microkernel keeps the kernel small and moves many OS services, like file systems or device-related services, into user-level processes. This can make the system:

- more modular
- easier to debug
- potentially more reliable, because a faulty service may not crash the whole kernel
- easier to change or extend

But there is a tradeoff.

Because services run outside the kernel, applications often need extra communication steps, usually through interprocess communication. That can make operations slower than in a monolithic kernel, where many services are directly inside the kernel.

So the difference is roughly:

| Design | Main advantage | Main disadvantage |
|---|---|---|
| Monolithic kernel | Faster, tightly integrated | Less flexible, harder to isolate faults |
| Microkernel | More modular, easier to isolate/debug | Can have performance overhead |

That is why many real operating systems use a hybrid approach: they put some services in the kernel for performance, and some at user level for modularity or reliability.

So the answer is: **microkernels are better for some design goals, but not universally better.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `a96cf2b2d991d58e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `120`
- Score: `n/a `

```text
located on a different machine.
This has led ope rating system designers to wrestle with a fundamental tradeoff: by
centralizing functionality in the kernel, performance is improved and it makes it easier to
arrange tight integration between kernel modules. However, the resulting systems are less
flexible, less easy to change, and less adaptive to user or application needs. We discuss these
tradeoffs by describing several options for the operating system architecture.
3.5.1 Monolithic Kernels
```

#### Chunk 2

- Chunk ID: `0d2bd5db44000006`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `n/a `

```text
A microkernel design offers considerable benefit to the operating system developer, as it
easier to modularize and debug user-level services than kernel code. Aside from a potential
reliability improvement, however, microkernels offer little in the way of visible benefit to
end users and can slow dow n overall performance by inserting extra steps between the
application and the services it needs. Thus, in practice, most systems adopt a hybrid model
where some operating system services are run at user-level and some are in the kernel,
depending on the specific tradeoff between code complexity and performance.
3.6 Summary and Future Directions
In this chapter, we have seen how system calls can be used by applications to create and
```

#### Chunk 3

- Chunk ID: `f254d98fdea5fbb2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `n/a `

```text
of “what can be at user level, should be.” An extreme version of approach is to isolate
privileged, bu t less critical, parts of the operating system such as the file system or the
window system, from the rest of the kernel. This is called a microkernel design. In a
microkernel, the kernel itself is kept small, and instead most of the functionality of a
traditional operating system kernel is put into a set of user-level processes, or servers,
accessed from user applications via interprocess communication.
Performance. Finally, transferring control into the kernel is more expensive than a
procedure call to a library, and transferring control to a user-level file system server via
the kernel is still even more costly. Hardware designers have attempted to reduce the
```

#### Chunk 4

- Chunk ID: `3b746b139dd587fc`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `153`
- Score: `n/a `

```text
MFT
See: master file table.
microkernel
An operating system design where the kernel itself is kept small, and instead most of the
functionality of a traditional operating system kernel is put into a set of user-level
processes, or servers, accessed from user applications via interprocess communication.
MIN cache replacement
See: optimal cache replacement.
minimum seek time
The time to move the disk arm to the next adjacent track.
MIPS
An early measure of processor performance: millions of instructions per second.
mirroring
A system for redundantly storing data on disk where each block of data is stored on two
disks and can be read from either. See also: RAID 1.
model
A simplification that tries to capture the most important aspects of a more complex
system’s behavior.
monolithic kernel
```

#### Chunk 5

- Chunk ID: `989e59a5a3601851`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `124`
- Score: `n/a `

```text
guest operating system and not other applications running on the underlying virtual
machine monitor.
Driver sandboxing. A further challenge for both user-level device drivers and virtual
machine drivers is performance. Some device drivers need frequent interaction with
hardware and the rest of the kernel. Some researchers have propos ed running device
drivers in their own restricted execution environment inside the kernel. This requires
lightweight sandbox ing techniques, a topic we will return to at the end of Chapter 8.
3.5.2 Microkernel
An alternative to the monolithic kernel approach is to run as much of the operating system as
possible in one or more user-level servers. The window manager on most operating systems
```

### Method C

- Retrieval latency: 0.758s
- Generation latency: 7.216s

**Answer:**

No — a microkernel is not automatically “better” than a monolithic kernel.

A microkernel keeps the kernel small and moves services like file systems, device drivers, or networking into user-level server processes. That has some real advantages:

- **Better modularity**: services are separated more cleanly.
- **Easier debugging/development**: user-level code is usually easier to test than kernel code.
- **Potential reliability benefits**: if a user-level service crashes, it may not crash the whole kernel.

But there is also a cost:

- **Performance overhead**: applications may need to communicate with user-level OS services through interprocess communication, often involving the kernel as a middle step.
- This can mean more context switches and extra data movement compared with calling a service directly inside a monolithic kernel.

So the tradeoff is roughly:

| Design | Main strength | Main weakness |
|---|---|---|
| **Microkernel** | Modularity, isolation, reliability | More communication overhead |
| **Monolithic kernel** | Performance, direct access to services | More complex kernel, bugs can be more dangerous |

That is why many real systems use a **hybrid approach**: some services run in the kernel for speed, while others run at user level for modularity and safety.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4bda4c17854153be`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `2.78363 rerank_score`

```text
items more quickly. Some systems have moved other parts of the operating system into user-
level servers: the network stack, the file system, device drivers, and so forth.
The difference between a monolithic and a microkernel design is often transparent to the
application programmer. The location of the service can be hidden in a user-level library —
calls go to the library, which casts the requests either as system calls or as reads and writes
to the server through a pipe. The location of the server can also be hidden inside the kernel
— the application calls the kernel as if the kernel implements the service, but instead the
kernel reformats the request into a pipe that the server can read.
A microkernel design offers considerable benefit to the operating system developer, as it
```

#### Chunk 2

- Chunk ID: `f254d98fdea5fbb2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `102`
- Score: `1.66465 rerank_score`

```text
of “what can be at user level, should be.” An extreme version of approach is to isolate
privileged, bu t less critical, parts of the operating system such as the file system or the
window system, from the rest of the kernel. This is called a microkernel design. In a
microkernel, the kernel itself is kept small, and instead most of the functionality of a
traditional operating system kernel is put into a set of user-level processes, or servers,
accessed from user applications via interprocess communication.
Performance. Finally, transferring control into the kernel is more expensive than a
procedure call to a library, and transferring control to a user-level file system server via
the kernel is still even more costly. Hardware designers have attempted to reduce the
```

#### Chunk 3

- Chunk ID: `0d2bd5db44000006`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `125`
- Score: `1.00084 rerank_score`

```text
A microkernel design offers considerable benefit to the operating system developer, as it
easier to modularize and debug user-level services than kernel code. Aside from a potential
reliability improvement, however, microkernels offer little in the way of visible benefit to
end users and can slow dow n overall performance by inserting extra steps between the
application and the services it needs. Thus, in practice, most systems adopt a hybrid model
where some operating system services are run at user-level and some are in the kernel,
depending on the specific tradeoff between code complexity and performance.
3.6 Summary and Future Directions
In this chapter, we have seen how system calls can be used by applications to create and
```

#### Chunk 4

- Chunk ID: `9491be32708cb184`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `152`
- Score: `0.472531 rerank_score`

```text
MFT
See: master file table.
microkernel
An operating system design where the kernel itself is kept small, and instead most of the
functionality of a traditional operating system kernel is put into a set of user-level
processes, or servers, accessed from user applications via interprocess communication.
MIN cache replacement
See: optimal cache replacement.
minimum seek time
The time to move the disk arm to the next adjacent track.
MIPS
An early measure of processor performance: millions of instructions per second.
mirroring
A system for redundantly storing data on disk where each block of data is stored on two
disks and can be read from either. See also: RAID 1.
model
A simplification that tries to capture the most important aspects of a more complex
system’s behavior.
monolithic kernel
```

#### Chunk 5

- Chunk ID: `1629dc0449af4780`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `285`
- Score: `0.472531 rerank_score`

```text
MFT
See: master file table.
microkernel
An operating system design where the kernel itself is kept small, and instead most of the
functionality of a traditional operating system kernel is put into a set of user-level
processes, or servers, accessed from user applications via interprocess communication.
MIN cache replacement
See: optimal cache replacement.
minimum seek time
The time to move the disk arm to the next adjacent track.
MIPS
An early measure of processor performance: millions of instructions per second.
mirroring
A system for redundantly storing data on disk where each block of data is stored on two
disks and can be read from either. See also: RAID 1.
model
A simplification that tries to capture the most important aspects of a more complex
system’s behavior.
monolithic kernel
```

## q33

**Question:** If a TLB is only a cache of address translations, why can TLB misses have such a noticeable effect on performance?

### Method A

- Retrieval latency: 0.361s
- Generation latency: 7.630s

**Answer:**

Because address translation happens on **almost every memory reference**, even a “small” extra cost can be paid very often.

A TLB hit is fast: the CPU quickly gets the physical page number and continues.

A TLB miss is expensive because the processor must do the **full address translation** instead of using the cached result. That may involve:

- walking the page table, often with **multiple memory accesses**
- possibly causing cache misses during that page-table walk
- stalling the instruction that needs the address
- in a software-loaded TLB, trapping into the OS kernel, which is even more expensive

So the average cost is roughly:

\[
\text{translation cost}
=
\text{TLB lookup cost}
+
\text{full translation cost} \times (1 - P(\text{hit}))
\]

Even if the miss rate is low, programs generate huge numbers of memory references: instruction fetches, loads, stores, stack accesses, etc. So a small percentage of misses can still create many stalls.

In short: **a TLB miss is noticeable because it turns a normally tiny per-access translation cost into a much larger operation, and memory accesses happen constantly.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1713643eca83672d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `41`
- Score: `5.1005 rerank_score`

```text
A TLB miss occurs if none of the entries in the TLB match. In this case, the hardware does the
full address translation in the way we described above . When the address translation
completes, the physical page is used to form the physical address, and the translation is
installed in an entry in the TLB, replacing one of the existing entries. Typically, the replaced
entry will be one that has not been used recently.
The TLB lookup is illustrated in Figure 8.10, and Figure 8.11 shows how a TLB fits into the
overall address translation system.
Although the hardware cost of a TLB might seem large, it is modest compared to the potential
gain in processor performance. To be useful, the TLB lookup needs to be much more rapid
```

#### Chunk 2

- Chunk ID: `ae9a64ea67e92604`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `4.92215 rerank_score`

```text
rare event. Even so, TLB misses are a significant cost for many applications.
Software-loaded TLB
If the TLB is effective at amortizing the cost of doing a full address translation across many memory references, we can ask
a radical question: do we need hardware multi-level page table lookup on a TLB miss? This is the concept behind a software-
loaded TLB. A TLB hit works as before, as a fast path. On a TLB miss, instead of doing hardware address translation, the
processor traps to the operating system kernel. In the trap handler, the kernel is responsible for doing the address lookup,
loading the TLB with the new translation, and restarting the application.
This approach dramatically simplifies the design of the operating system, because it no longer needs to keep two sets of page
```

#### Chunk 3

- Chunk ID: `4003a131de5380a6`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `4.69068 rerank_score`

```text
engineering reasons into one for instruction lookups and a separate one for data lookups). If
the first level TLB does not contain the translation, a larger second level TLB is consulted,
and the full translation is only invoked if the translation misses both levels. For simplicity,
our discussion will assume a single-level TLB.
A TLB also requires an address comparator for each entry to check in parallel if there is a
match. To reduce this cost, some TLBs are set associative. Compared to fully associative
TLBs, set associative ones need fewer comparators, but they may have a higher miss rate. We
will discuss set associativity, and its implications for operating system design, in the next
chapter.
What is the cost of address translation with a TLB? There are two factors. We pay the cost of
```

#### Chunk 4

- Chunk ID: `be5979749d88257e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `4.22748 rerank_score`

```text
chapter.
What is the cost of address translation with a TLB? There are two factors. We pay the cost of
the TLB lookup regardless of whether the address is in the TLB or not; in the case of an
unsuccessful TLB lookup, we also pay the cost of the full translation. If P(hit) is the
likelihood t hat the TLB has the entry cached:
Cost (address translation)   =   Cost (TLB lookup)
     + Cost (full translation) × (1 - P(hit))
In other words, the processor designer needs to include a sufficiently large TLB that most
addresses generated by a program will hit in the TLB, so that doing the full translation is the
rare event. Even so, TLB misses are a significant cost for many applications.
Software-loaded TLB
```

#### Chunk 5

- Chunk ID: `df6e6e058412caf5`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `3.48605 rerank_score`

```text
This approach dramatically simplifies the design of the operating system, because it no longer needs to keep two sets of page
tables, one for the hardware and one for itself. On a TLB miss, the operating system can consult its own portable data
structures to determine what data should be loaded into the TLB.
Although convenient for the operating system, a software-loaded TLB is somewhat slower for executing applications, as the
cost of trapping to the kernel is significantly more than the cost of doing hardware address translation. As we will see in the
next chapter, the contents of page table entries can be stored in on-chip hardware caches; this means that even on a TLB
```

### Method B

- Retrieval latency: 0.204s
- Generation latency: 7.683s

**Answer:**

Because a TLB is on the critical path of **every memory access**.

On a TLB hit, address translation is very fast: the virtual page number is matched in the TLB, and the physical page number is obtained immediately.

On a TLB miss, the processor cannot complete the memory access until it finds the translation elsewhere. That may require:

- doing a full page table walk,
- reading multiple page table entries from memory,
- possibly missing in the CPU caches while doing that,
- or, on systems with a software-managed TLB, trapping into the OS kernel to load the translation.

So even though the TLB is “only a cache,” a miss is expensive because it delays the actual memory reference.

A useful way to think about it:

> A cache miss in a normal data cache delays one memory load/store.  
> A TLB miss delays the translation needed before the load/store can even happen.

Also, programs perform huge numbers of memory references. Even a small TLB miss rate can therefore add up to a noticeable performance cost, especially for programs with poor locality or large working sets.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1713643eca83672d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `41`
- Score: `0.442856 vector_distance`

```text
A TLB miss occurs if none of the entries in the TLB match. In this case, the hardware does the
full address translation in the way we described above . When the address translation
completes, the physical page is used to form the physical address, and the translation is
installed in an entry in the TLB, replacing one of the existing entries. Typically, the replaced
entry will be one that has not been used recently.
The TLB lookup is illustrated in Figure 8.10, and Figure 8.11 shows how a TLB fits into the
overall address translation system.
Although the hardware cost of a TLB might seem large, it is modest compared to the potential
gain in processor performance. To be useful, the TLB lookup needs to be much more rapid
```

#### Chunk 2

- Chunk ID: `ae9a64ea67e92604`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `0.4575 vector_distance`

```text
rare event. Even so, TLB misses are a significant cost for many applications.
Software-loaded TLB
If the TLB is effective at amortizing the cost of doing a full address translation across many memory references, we can ask
a radical question: do we need hardware multi-level page table lookup on a TLB miss? This is the concept behind a software-
loaded TLB. A TLB hit works as before, as a fast path. On a TLB miss, instead of doing hardware address translation, the
processor traps to the operating system kernel. In the trap handler, the kernel is responsible for doing the address lookup,
loading the TLB with the new translation, and restarting the application.
This approach dramatically simplifies the design of the operating system, because it no longer needs to keep two sets of page
```

#### Chunk 3

- Chunk ID: `fd261878e24d742b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `41`
- Score: `0.538981 vector_distance`

```text
gain in processor performance. To be useful, the TLB lookup needs to be much more rapid
than doing a full address translation; thus, the TLB table entries are implemented in very fast,
on-chip static memory, situated near the processor. In fact, to keep lookups rapid, many
systems now include multiple levels of TLB. In general, the smaller the memory, the faster the
lookup. So, the first level TLB is small and close to the processor (and often split for
```

#### Chunk 4

- Chunk ID: `7ced947632c50916`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `96`
- Score: `0.569443 vector_distance`

```text
cached translations in the TLB.
Many systems use a hybrid approach. In addition to active pages where the hardware collects the use bit, the operating
system maintains a pool of unused, clean page frames that are unmapped in any virtual address space, but still contain their
old data. When a new page frame is needed, pages in this pool can be used without any further work. However, if the old
data is referenced before the page frame is reused, the page can be pulled out of the pool and mapped back into the virtual
address space.
Systems with a software-managed TLB have an even simpler time. Each time there is a TLB miss with a software-managed
TLB, there is a trap to the kernel to look up the translation. During the trap, the kernel can update its list of frequently used
pages.
```

#### Chunk 5

- Chunk ID: `4003a131de5380a6`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `0.573441 vector_distance`

```text
engineering reasons into one for instruction lookups and a separate one for data lookups). If
the first level TLB does not contain the translation, a larger second level TLB is consulted,
and the full translation is only invoked if the translation misses both levels. For simplicity,
our discussion will assume a single-level TLB.
A TLB also requires an address comparator for each entry to check in parallel if there is a
match. To reduce this cost, some TLBs are set associative. Compared to fully associative
TLBs, set associative ones need fewer comparators, but they may have a higher miss rate. We
will discuss set associativity, and its implications for operating system design, in the next
chapter.
What is the cost of address translation with a TLB? There are two factors. We pay the cost of
```

### Method C

- Retrieval latency: 0.915s
- Generation latency: 7.884s

**Answer:**

Because address translation happens **on nearly every memory access**, and a TLB miss turns a normally fast operation into a much slower one.

A TLB hit is cheap:

- CPU generates a virtual address
- TLB quickly gives the physical page number
- memory/cache access can continue

But on a TLB miss:

- the translation is not cached
- the system must do the **full address translation**, usually by walking the page table
- this may require extra memory accesses
- on software-managed TLB systems, it may even trap into the kernel

So the cost is roughly:

\[
\text{translation cost} =
\text{TLB lookup cost}
+
\text{full translation cost} \times (1 - P(\text{hit}))
\]

Even if misses are rare, they can be expensive enough to matter because programs perform huge numbers of memory accesses. A small miss rate multiplied by millions or billions of accesses can noticeably slow execution.

So the key idea is:

> The TLB is “only a cache,” but it caches something needed constantly. When it misses, the processor may have to pause and perform a much slower translation path.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1713643eca83672d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `41`
- Score: `n/a `

```text
A TLB miss occurs if none of the entries in the TLB match. In this case, the hardware does the
full address translation in the way we described above . When the address translation
completes, the physical page is used to form the physical address, and the translation is
installed in an entry in the TLB, replacing one of the existing entries. Typically, the replaced
entry will be one that has not been used recently.
The TLB lookup is illustrated in Figure 8.10, and Figure 8.11 shows how a TLB fits into the
overall address translation system.
Although the hardware cost of a TLB might seem large, it is modest compared to the potential
gain in processor performance. To be useful, the TLB lookup needs to be much more rapid
```

#### Chunk 2

- Chunk ID: `7ced947632c50916`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `96`
- Score: `n/a `

```text
cached translations in the TLB.
Many systems use a hybrid approach. In addition to active pages where the hardware collects the use bit, the operating
system maintains a pool of unused, clean page frames that are unmapped in any virtual address space, but still contain their
old data. When a new page frame is needed, pages in this pool can be used without any further work. However, if the old
data is referenced before the page frame is reused, the page can be pulled out of the pool and mapped back into the virtual
address space.
Systems with a software-managed TLB have an even simpler time. Each time there is a TLB miss with a software-managed
TLB, there is a trap to the kernel to look up the translation. During the trap, the kernel can update its list of frequently used
pages.
```

#### Chunk 3

- Chunk ID: `4003a131de5380a6`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `n/a `

```text
engineering reasons into one for instruction lookups and a separate one for data lookups). If
the first level TLB does not contain the translation, a larger second level TLB is consulted,
and the full translation is only invoked if the translation misses both levels. For simplicity,
our discussion will assume a single-level TLB.
A TLB also requires an address comparator for each entry to check in parallel if there is a
match. To reduce this cost, some TLBs are set associative. Compared to fully associative
TLBs, set associative ones need fewer comparators, but they may have a higher miss rate. We
will discuss set associativity, and its implications for operating system design, in the next
chapter.
What is the cost of address translation with a TLB? There are two factors. We pay the cost of
```

#### Chunk 4

- Chunk ID: `be5979749d88257e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `42`
- Score: `n/a `

```text
chapter.
What is the cost of address translation with a TLB? There are two factors. We pay the cost of
the TLB lookup regardless of whether the address is in the TLB or not; in the case of an
unsuccessful TLB lookup, we also pay the cost of the full translation. If P(hit) is the
likelihood t hat the TLB has the entry cached:
Cost (address translation)   =   Cost (TLB lookup)
     + Cost (full translation) × (1 - P(hit))
In other words, the processor designer needs to include a sufficiently large TLB that most
addresses generated by a program will hit in the TLB, so that doing the full translation is the
rare event. Even so, TLB misses are a significant cost for many applications.
Software-loaded TLB
```

#### Chunk 5

- Chunk ID: `fd261878e24d742b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `41`
- Score: `n/a `

```text
gain in processor performance. To be useful, the TLB lookup needs to be much more rapid
than doing a full address translation; thus, the TLB table entries are implemented in very fast,
on-chip static memory, situated near the processor. In fact, to keep lookups rapid, many
systems now include multiple levels of TLB. In general, the smaller the memory, the faster the
lookup. So, the first level TLB is small and close to the processor (and often split for
```

## q34

**Question:** If paging avoids external fragmentation, does that mean fragmentation is no longer a problem?

### Method A

- Retrieval latency: 0.194s
- Generation latency: 5.845s

**Answer:**

Not completely.

Paging **solves external fragmentation** because physical memory is split into fixed-size frames, so a process’s pages can be placed anywhere in memory. The free frames do **not** need to be contiguous.

But fragmentation can still exist as **internal fragmentation**:

- Each page/frame has a fixed size, e.g. 4 KB.
- If a process needs only part of its last page, the unused part is wasted.
- Example: if a process needs 10 KB and pages are 4 KB, it gets 3 pages = 12 KB, so 2 KB are unused.

So:

| Memory system | Main fragmentation problem |
|---|---|
| Segmentation / variable-sized allocation | External fragmentation |
| Paging | Internal fragmentation |

Also, paging introduces another overhead: **page tables** can become large, especially with large virtual address spaces.

So the short answer is:

**Paging removes external fragmentation, but it does not eliminate memory waste entirely; it mainly trades external fragmentation for internal fragmentation and page-table overhead.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `0.922966 vector_distance`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `bc42460b2c8c0361`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `0.92981 vector_distance`

```text
even faster devices are likely in the future. Similarly, the move towards data center
computing has added a new option to memory management: using DRAM on other nodes
in the data center as a low-latency, very high capacity backing store for local memory.
Both of these trends reduce the cost of paging, making it relatively more attractive.
Variable page sizes. Many systems use a standard 4 KB page size, but there is nothing
fundamental about that choice — it is a tradeoff chosen to balance internal
fragmentation, page table overhead, disk latency, the overhead of collecting dirty and
usage bits, and application spatial locality. On modern disks, it only takes twice as long
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
```

#### Chunk 3

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `0.943114 vector_distance`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

#### Chunk 4

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `0.997984 vector_distance`

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 5

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.999196 vector_distance`

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

### Method B

- Retrieval latency: 0.363s
- Generation latency: 6.600s

**Answer:**

No. Paging removes **external fragmentation** in physical memory, but fragmentation/space waste can still exist.

With paging:

- Physical memory is split into fixed-size **page frames**.
- A process’s pages can be placed in any free frames.
- So the OS does **not** need one large contiguous free block.
- Therefore, paging avoids **external fragmentation**.

But paging can still cause **internal fragmentation**:

- Each page frame has a fixed size.
- If a process does not use the whole last page, the unused part is wasted.
- Example: if pages are 4 KB and a process needs 10 KB, it gets 3 pages = 12 KB, so 2 KB are unused.

So the idea is:

| Memory scheme | Main fragmentation problem |
|---|---|
| Segmentation / variable-size allocation | External fragmentation |
| Paging / fixed-size allocation | Internal fragmentation |

So fragmentation is **reduced and easier to manage**, but it is **not gone completely**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `04415980a4e02669`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `60`
- Score: `1.14071 rerank_score`

```text
and Application Domains. As these technologies become more widely used, it seems
likely we may direct hardware support for application-level protection — to allow each
application to set up its own protected execution environment, but enforced in hardware.
If so, we may come to think of many applications as having their own embedded
operating system, and the underlying operating system kernel as mediating between these
operating systems.
Exercises
1. True or false. A virtual memory system that uses paging is vulnerable to external
fragmentation. Why or why not?
2. For systems that use paged segmentation, what translation state does the kernel need to
change on a process context switch?
```

#### Chunk 2

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `0.788184 rerank_score`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 3

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `-1.36757 rerank_score`

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 4

- Chunk ID: `7415eb4425f232f5`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `90`
- Score: `-4.10722 rerank_score`

```text
long term benefits, however: fragmentation is reduced, the block will tend to have a long
run of free space at its end, subsequent writes are more likely to be sequential.
The intuition is that a given block group will usually have a handful of holes scattered
through blocks near the start of the group and a long run of free space at the end of the
group. Then, if a new, small file is created, its blocks will likely go to a few of the small
holes, which is not ideal, but which is acceptable for a small file. Conversely, if a large
file is created and written from beginning to end, it will tend to have the first few blocks
scattered through the holes in the early part of the block, but then have the bulk of its data
written sequentially at the end of the block group.
```

#### Chunk 5

- Chunk ID: `53bbd3d6ec8d5627`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `-4.52671 rerank_score`

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

### Method C

- Retrieval latency: 0.831s
- Generation latency: 5.517s

**Answer:**

No. Paging avoids **external fragmentation**, but fragmentation is not completely gone.

With paging:

- **External fragmentation is avoided** because physical memory is split into equal-size page frames. Any free frame can be used for any page, so memory does not need to be contiguous.

- But **internal fragmentation can still happen**. If a process does not fully use its last page, the unused space inside that allocated page frame is wasted.

Example:

If page size is 4 KB and a process needs 10 KB:

- It needs 3 pages = 12 KB allocated
- Actual use = 10 KB
- Wasted space = 2 KB

That wasted 2 KB is **internal fragmentation**.

So the tradeoff is:

- Paging removes the problem of scattered free holes in memory.
- But it can waste space inside pages, especially if pages are large.

Also, very small pages reduce internal fragmentation, but then the page table becomes larger. So fragmentation is reduced and managed differently, not eliminated entirely.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `n/a `

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `bc42460b2c8c0361`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `n/a `

```text
even faster devices are likely in the future. Similarly, the move towards data center
computing has added a new option to memory management: using DRAM on other nodes
in the data center as a low-latency, very high capacity backing store for local memory.
Both of these trends reduce the cost of paging, making it relatively more attractive.
Variable page sizes. Many systems use a standard 4 KB page size, but there is nothing
fundamental about that choice — it is a tradeoff chosen to balance internal
fragmentation, page table overhead, disk latency, the overhead of collecting dirty and
usage bits, and application spatial locality. On modern disks, it only takes twice as long
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
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

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `n/a `

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 5

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `n/a `

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

## q35

**Question:** What is the difference between internal fragmentation and external fragmentation, and why does paging help with one but not necessarily the other?

### Method A

- Retrieval latency: 0.197s
- Generation latency: 11.578s

**Answer:**

**Internal fragmentation** and **external fragmentation** are both wasted memory, but in different places.

### Internal fragmentation
This happens **inside an allocated block**.

Example:  
If memory is allocated in fixed-size pages of 4 KB, and a process only needs 3.5 KB, the remaining 0.5 KB inside that page is wasted.

So:

> **Internal fragmentation = wasted space inside allocated memory units.**

Paging can cause this because pages/page frames have fixed sizes.

---

### External fragmentation
This happens **between allocated blocks**.

Example:  
Memory has enough total free space for a new allocation, but the free space is split into many small non-contiguous holes:

```text
[used][free][used][free][used][free]
```

There may be enough free memory overall, but not one large continuous region.

So:

> **External fragmentation = wasted free space scattered between allocations.**

This is common with variable-sized allocation, such as segmentation.

---

### Why paging helps with external fragmentation

Paging divides physical memory into fixed-size **page frames**. A process’s virtual pages do **not** need to be placed contiguously in physical memory.

So a process can use frames scattered anywhere:

```text
Process page 0 → frame 8
Process page 1 → frame 2
Process page 2 → frame 15
```

Because every frame is the same size, any free frame can be used. This largely removes **external fragmentation**.

---

### Why paging does not necessarily help with internal fragmentation

Paging still allocates memory in fixed-size chunks. If a process does not fully use its last page, the unused part of that page is wasted.

For example, with 4 KB pages:

```text
Process needs 10 KB
Must allocate 3 pages = 12 KB
Unused = 2 KB
```

That unused 2 KB is **internal fragmentation**.

---

In short:

| Type | Where waste happens | Paging effect |
|---|---|---|
| Internal fragmentation | Inside allocated blocks/pages | Paging can cause it |
| External fragmentation | Between allocated blocks | Paging mostly avoids it |

Paging helps because it removes the need for contiguous physical allocation, but it still uses fixed-size pages, so some space inside pages may be wasted.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `0.886749 vector_distance`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `c58d2b67bf00091b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `31`
- Score: `0.933007 vector_distance`

```text
Almost all multi-level address translation systems use paging as the lowest level of the tree.
The main differences between systems are in how they reach the page table at the leaf of the
tree — w hether using segments plus paging, or multiple levels of paging, or segments plus
multiple levels of paging. There are several reasons for this:
Efficient memory allocation. By allocating physical memory in fixed-size page frames,
management of free space can use a simple bitmap.
Efficient disk transfers. Hardware disks are partitioned into fixed-sized regions called
sectors; disk sectors must be read or written in their entirety. By making the page size a
multiple of the disk sector, we simplify transfers to and from memory, for loading
```

#### Chunk 3

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `0.940416 vector_distance`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

#### Chunk 4

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `0.964132 vector_distance`

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 5

- Chunk ID: `bc42460b2c8c0361`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `0.97677 vector_distance`

```text
even faster devices are likely in the future. Similarly, the move towards data center
computing has added a new option to memory management: using DRAM on other nodes
in the data center as a low-latency, very high capacity backing store for local memory.
Both of these trends reduce the cost of paging, making it relatively more attractive.
Variable page sizes. Many systems use a standard 4 KB page size, but there is nothing
fundamental about that choice — it is a tradeoff chosen to balance internal
fragmentation, page table overhead, disk latency, the overhead of collecting dirty and
usage bits, and application spatial locality. On modern disks, it only takes twice as long
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
```

### Method B

- Retrieval latency: 0.903s
- Generation latency: 10.257s

**Answer:**

**Internal fragmentation** and **external fragmentation** are both forms of wasted memory, but they happen for different reasons.

### Internal fragmentation
This happens when memory is allocated in fixed-size chunks, but the process does not use the whole chunk.

Example:  
If pages are **4 KB** and a process needs **6 KB**, it gets 2 pages = **8 KB** total.  
The unused **2 KB inside the allocated pages** is internal fragmentation.

So the waste is **inside allocated memory blocks**.

---

### External fragmentation
This happens when free memory exists, but it is split into many small non-contiguous pieces.

Example:  
There may be 100 MB free in total, but scattered as small holes across memory.  
If a process needs one contiguous 50 MB block, allocation may fail even though enough total memory exists.

So the waste is **between allocated memory blocks**.

---

### Why paging helps with external fragmentation
Paging divides physical memory into fixed-size **page frames**. A process’s virtual pages do **not** need to be placed contiguously in physical memory.

So instead of needing one large continuous block, the OS can place pages into any free frames.

That means paging mostly eliminates **external fragmentation**.

---

### Why paging does not necessarily solve internal fragmentation
Paging still uses fixed-size chunks. If a process does not fully use its last page, the unused space inside that page is wasted.

So paging can still cause **internal fragmentation**.

In short:

| Type | Where waste occurs | Paging effect |
|---|---|---|
| Internal fragmentation | Inside allocated blocks/pages | Can still happen |
| External fragmentation | Between allocated blocks | Mostly avoided by paging |

Paging trades external fragmentation for possible internal fragmentation.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `n/a `

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `c58d2b67bf00091b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `31`
- Score: `n/a `

```text
Almost all multi-level address translation systems use paging as the lowest level of the tree.
The main differences between systems are in how they reach the page table at the leaf of the
tree — w hether using segments plus paging, or multiple levels of paging, or segments plus
multiple levels of paging. There are several reasons for this:
Efficient memory allocation. By allocating physical memory in fixed-size page frames,
management of free space can use a simple bitmap.
Efficient disk transfers. Hardware disks are partitioned into fixed-sized regions called
sectors; disk sectors must be read or written in their entirety. By making the page size a
multiple of the disk sector, we simplify transfers to and from memory, for loading
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

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `n/a `

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 5

- Chunk ID: `bc42460b2c8c0361`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `n/a `

```text
even faster devices are likely in the future. Similarly, the move towards data center
computing has added a new option to memory management: using DRAM on other nodes
in the data center as a low-latency, very high capacity backing store for local memory.
Both of these trends reduce the cost of paging, making it relatively more attractive.
Variable page sizes. Many systems use a standard 4 KB page size, but there is nothing
fundamental about that choice — it is a tradeoff chosen to balance internal
fragmentation, page table overhead, disk latency, the overhead of collecting dirty and
usage bits, and application spatial locality. On modern disks, it only takes twice as long
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
```

### Method C

- Retrieval latency: 0.641s
- Generation latency: 9.601s

**Answer:**

**Internal fragmentation** = wasted space *inside* an allocated block.

- Example: page size is 4 KB, but a process needs only 6 KB.
- It gets 2 pages = 8 KB total.
- 2 KB is unused inside the allocated pages.
- That unused space is **internal fragmentation**.

**External fragmentation** = wasted free space *between* allocated blocks.

- There may be enough free memory total, but it is split into many small non-contiguous pieces.
- Example: you need 100 KB contiguous memory, and the system has 120 KB free, but scattered in small chunks.
- The allocation may fail because the free memory is not contiguous.

### Why paging helps with external fragmentation

Paging divides physical memory into fixed-size **frames** and virtual memory into fixed-size **pages**.

A process’s pages do **not** need to be placed contiguously in physical memory. Any free frame can hold any page.

So paging largely avoids **external fragmentation**, because the OS does not need to find one large contiguous physical block.

### Why paging does not eliminate internal fragmentation

Paging uses fixed-size pages. If a process does not completely fill its last page, the unused part of that page is wasted.

So paging can still cause **internal fragmentation**.

In short:

| Type | Meaning | Paging effect |
|---|---|---|
| Internal fragmentation | Waste inside allocated blocks | Still possible |
| External fragmentation | Free space split between allocations | Mostly eliminated |

So paging trades the external-fragmentation problem for possible internal fragmentation and page table overhead.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `2.43112 rerank_score`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `04415980a4e02669`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `60`
- Score: `1.05076 rerank_score`

```text
and Application Domains. As these technologies become more widely used, it seems
likely we may direct hardware support for application-level protection — to allow each
application to set up its own protected execution environment, but enforced in hardware.
If so, we may come to think of many applications as having their own embedded
operating system, and the underlying operating system kernel as mediating between these
operating systems.
Exercises
1. True or false. A virtual memory system that uses paging is vulnerable to external
fragmentation. Why or why not?
2. For systems that use paged segmentation, what translation state does the kernel need to
change on a process context switch?
```

#### Chunk 3

- Chunk ID: `5989685cb5c2f6fe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `27`
- Score: `0.569039 rerank_score`

```text
operating system may reach a point where there is enough free space for a new segment, but
the free space is not contiguous. This is called external fragmentation. The operating system
is free to compact memory to make room without affecting applications, because virtual
addresses are unchanged when we relocate a segment in physical memory. Even so,
compaction can be costly in terms of processor overhead: a typical server configuration
would take roughly a second to compact its memory.
All this becomes even more complex when memory segments can grow. How much memory
should we set aside for a program’s heap? If we put the heap segment in a part of physical
memory with lots of room, then we will have wasted memory if that program turns out to need
```

#### Chunk 4

- Chunk ID: `bc42460b2c8c0361`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `-2.26262 rerank_score`

```text
even faster devices are likely in the future. Similarly, the move towards data center
computing has added a new option to memory management: using DRAM on other nodes
in the data center as a low-latency, very high capacity backing store for local memory.
Both of these trends reduce the cost of paging, making it relatively more attractive.
Variable page sizes. Many systems use a standard 4 KB page size, but there is nothing
fundamental about that choice — it is a tradeoff chosen to balance internal
fragmentation, page table overhead, disk latency, the overhead of collecting dirty and
usage bits, and application spatial locality. On modern disks, it only takes twice as long
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
```

#### Chunk 5

- Chunk ID: `8e13aa84a1dc04b3`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `63`
- Score: `-2.7176 rerank_score`

```text
wasted by internal fragmentation for a process that has 64K  of memory starting at
address 0?
c. How much memory is consumed by the first and second level page tables and
wasted by internal fragmentation for a process that has a code segment of 48K
starting at address 0x1000000, a  data segment of 600K  starting at address
0x80000000 a nd a stack segment of 64K  starting at address 0xf0000000 a nd
growing upward (towards higher addresses)?
14. Write pseudo-code to convert a 32-bit virtual address to a 32-bit physical address for a
two-level address translation scheme using segmentation at the first level of translation
and paging at the second level. Explicitly define whatever constants and data structures
you need (e.g., the format of the page table entry, the page size, and so forth).
```

## q36

**Question:** If a page table tells the system where pages are, why do we need multi-level page tables instead of one big table?

### Method A

- Retrieval latency: 0.825s
- Generation latency: 9.048s

**Answer:**

Because a single big page table can be **huge**, even if most of a process’s virtual address space is unused.

A page table needs one entry for every virtual page. For a large virtual address space, that means:

- many entries for pages that do not exist yet,
- lots of wasted memory,
- and a table that may be too large to conveniently store contiguously.

A **multi-level page table** avoids this by treating the page table like a tree.

Example idea:

```text
Virtual address
= top-level index | second-level index | page offset
```

The top-level table points to lower-level page tables. But the lower-level tables are created **only for parts of the virtual address space that are actually used**.

So instead of storing one massive table like:

```text
[entry for page 0][entry for page 1][entry for page 2]...[entry for every possible page]
```

the OS stores something more like:

```text
top-level table
   |
   +--> second-level table for used region
   |
   +--> nothing for unused region
   |
   +--> second-level table for another used region
```

So the main reason is:

> Multi-level page tables save memory by not allocating page table entries for unused regions of virtual address space.

There is a tradeoff, though: address translation may require looking through several levels. In practice, this is made fast using the **TLB**, which caches recent translations.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d11bda8313c1622b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `33`
- Score: `n/a `

```text
For example, with 32-bit virtual addresses and 4 K B pages, we might set aside the upper ten
bits for the segment number, the next ten bits for the page number, and twelve bits for the page
offset. In this case, if each page table entry is four bytes, the page table for each segment
would exactly fit into one physical page frame.
Multi-Level Paging
Figure 8.8: Address translation with three levels of page tables. The virtual address has four components: an index into
each level of the page table and an offset within the physical page frame.
A nearly equivalent approach to paged segmentation is to use multiple levels of page tables.
On the Sun Microsystems SPARC processor for example, there are three levels of page table.
```

#### Chunk 2

- Chunk ID: `32d8920459496302`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `33`
- Score: `n/a `

```text
On the Sun Microsystems SPARC processor for example, there are three levels of page table.
As shown in Figure 8.8, the top-level page table contains entries, each of which points to a
second-level page table whose entries are pointers to page tables. On the SPARC, as with
most other systems that use multiple levels of page tables, each level of page table is
designed to fit in a physical page frame. Only the top-level page table must be filled in; the
lower levels of the tree are allocated only if those portions of the virtual address space are in
use by a particular process. Access permissions can be specified at each level, and so
sharing between processes is possible at each level.
```

#### Chunk 3

- Chunk ID: `c58d2b67bf00091b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `31`
- Score: `n/a `

```text
Almost all multi-level address translation systems use paging as the lowest level of the tree.
The main differences between systems are in how they reach the page table at the leaf of the
tree — w hether using segments plus paging, or multiple levels of paging, or segments plus
multiple levels of paging. There are several reasons for this:
Efficient memory allocation. By allocating physical memory in fixed-size page frames,
management of free space can use a simple bitmap.
Efficient disk transfers. Hardware disks are partitioned into fixed-sized regions called
sectors; disk sectors must be read or written in their entirety. By making the page size a
multiple of the disk sector, we simplify transfers to and from memory, for loading
```

#### Chunk 4

- Chunk ID: `404b1d5ce04523ca`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `34`
- Score: `n/a `

```text
page. Each page table entry takes four bytes and the page size is 4 KB, so the top-level page
table and each second-level page table fits in a single physical page. The number of second-
level page tables needed depends on the length of the segment; they are not needed to map
empty regions of virtual address space. Both the top-level and second-level page table
entries have permissions, so fine-grained protection and sharing is possible within a segment.
Today, the amount of memory per computer is often well beyond what can 32 bi ts can
address; for example, a high-end server could have two terabytes of physical memory. For the
```

#### Chunk 5

- Chunk ID: `a713d060d4390589`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `35`
- Score: `n/a `

```text
operating system places data such that the entire 2 MB covered by the fourth level page table
is allocated contiguously in physical memory, then the page table entry one layer up can be
marked to poi nt directly to this region instead of to a page table. Likewise, a page of third
level page table can be omitted if the operating system allocates the process a 1 GB chunk of
physical memory. In addition to saving space needed for page table mappings, this improves
translation buffer efficiency, a point we will discuss in more detail in the next section.
8.2.4 Portability
The diversity of different translation mechanisms poses a challenge to the operating system
designer. To be widely used, we want our operating system to be easily portable to a wide
```

### Method B

- Retrieval latency: 0.202s
- Generation latency: 7.216s

**Answer:**

Because one big page table can waste a lot of memory.

A page table needs one entry for every virtual page in a process’s address space. But most processes do **not** use their entire virtual address space. Large parts may be empty.

With a **single-level page table**, the OS may still need a huge table covering all possible virtual pages, even unused ones.

With **multi-level page tables**, the table is split into smaller page-sized pieces:

- the top-level table is always present
- lower-level tables are created only for parts of virtual memory that are actually used
- empty regions of the address space need no lower-level page tables

So multi-level page tables save memory.

Example idea:

```text
Virtual address space:
[ used code ][ empty ][ empty ][ used heap ][ empty ][ used stack ]
```

A one-level page table needs entries for everything.

A multi-level page table only creates lower-level tables for:

```text
used code
used heap
used stack
```

and skips the empty parts.

So the main reason is:

> Multi-level page tables make page tables efficient for large, sparse virtual address spaces.

They still tell the system where pages are, just through multiple lookup steps instead of one giant table.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d11bda8313c1622b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `33`
- Score: `0.618809 vector_distance`

```text
For example, with 32-bit virtual addresses and 4 K B pages, we might set aside the upper ten
bits for the segment number, the next ten bits for the page number, and twelve bits for the page
offset. In this case, if each page table entry is four bytes, the page table for each segment
would exactly fit into one physical page frame.
Multi-Level Paging
Figure 8.8: Address translation with three levels of page tables. The virtual address has four components: an index into
each level of the page table and an offset within the physical page frame.
A nearly equivalent approach to paged segmentation is to use multiple levels of page tables.
On the Sun Microsystems SPARC processor for example, there are three levels of page table.
```

#### Chunk 2

- Chunk ID: `32d8920459496302`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `33`
- Score: `0.623109 vector_distance`

```text
On the Sun Microsystems SPARC processor for example, there are three levels of page table.
As shown in Figure 8.8, the top-level page table contains entries, each of which points to a
second-level page table whose entries are pointers to page tables. On the SPARC, as with
most other systems that use multiple levels of page tables, each level of page table is
designed to fit in a physical page frame. Only the top-level page table must be filled in; the
lower levels of the tree are allocated only if those portions of the virtual address space are in
use by a particular process. Access permissions can be specified at each level, and so
sharing between processes is possible at each level.
```

#### Chunk 3

- Chunk ID: `c58d2b67bf00091b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `31`
- Score: `0.652791 vector_distance`

```text
Almost all multi-level address translation systems use paging as the lowest level of the tree.
The main differences between systems are in how they reach the page table at the leaf of the
tree — w hether using segments plus paging, or multiple levels of paging, or segments plus
multiple levels of paging. There are several reasons for this:
Efficient memory allocation. By allocating physical memory in fixed-size page frames,
management of free space can use a simple bitmap.
Efficient disk transfers. Hardware disks are partitioned into fixed-sized regions called
sectors; disk sectors must be read or written in their entirety. By making the page size a
multiple of the disk sector, we simplify transfers to and from memory, for loading
```

#### Chunk 4

- Chunk ID: `404b1d5ce04523ca`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `34`
- Score: `0.675695 vector_distance`

```text
page. Each page table entry takes four bytes and the page size is 4 KB, so the top-level page
table and each second-level page table fits in a single physical page. The number of second-
level page tables needed depends on the length of the segment; they are not needed to map
empty regions of virtual address space. Both the top-level and second-level page table
entries have permissions, so fine-grained protection and sharing is possible within a segment.
Today, the amount of memory per computer is often well beyond what can 32 bi ts can
address; for example, a high-end server could have two terabytes of physical memory. For the
```

#### Chunk 5

- Chunk ID: `a713d060d4390589`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `35`
- Score: `0.695336 vector_distance`

```text
operating system places data such that the entire 2 MB covered by the fourth level page table
is allocated contiguously in physical memory, then the page table entry one layer up can be
marked to poi nt directly to this region instead of to a page table. Likewise, a page of third
level page table can be omitted if the operating system allocates the process a 1 GB chunk of
physical memory. In addition to saving space needed for page table mappings, this improves
translation buffer efficiency, a point we will discuss in more detail in the next section.
8.2.4 Portability
The diversity of different translation mechanisms poses a challenge to the operating system
designer. To be widely used, we want our operating system to be easily portable to a wide
```

### Method C

- Retrieval latency: 0.393s
- Generation latency: 7.751s

**Answer:**

A single big page table *would* work in principle, but it wastes a lot of memory.

A page table needs one entry for every possible virtual page. Modern virtual address spaces are huge, but most processes use only a small part of them.

Example idea:

```text
Virtual address space:
[ code ][ heap ] ........ lots unused ........ [ stack ]
```

With one big page table, the OS would need entries for all those unused virtual pages too.

A multi-level page table avoids that waste.

Instead of one huge flat array, it is like a tree:

```text
top-level page table
   ├── second-level table for used region
   ├── nothing for unused region
   └── second-level table for another used region
```

Only the parts of the page table that correspond to actually used regions of virtual memory need to be allocated. As the source says, lower levels are allocated only if those portions of the virtual address space are in use.

So the main reason is:

> Multi-level page tables save memory by not storing mappings for large unused parts of the virtual address space.

The tradeoff is that address translation may require multiple table lookups, but CPUs use the TLB — a translation cache — to make this efficient most of the time.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `66f2284d7c60a9e7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `4.65299 rerank_score`

```text
With a portability layer, the software page table is the ground truth, while the hardware page
table is a hint. The hardware page table can be safely used, provided that the translations and
permissions are a subset of the translations in the software page table.
Is an inverted page table enough?
The concept of an inverted page table raises an intriguing question: do we need to have a multi-level page table in hardware?
Suppose, in hardware, we hash the virtual address. But instead of using the hash value to look up in a table where to find the
physical page frame, suppose we just use the hash value as the physical page. For this to work, we need the hash table size
to have exactly as many entries as physical memory page frames, so that there is a one-to-one correspondence between the
```

#### Chunk 2

- Chunk ID: `a713d060d4390589`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `35`
- Score: `3.54486 rerank_score`

```text
operating system places data such that the entire 2 MB covered by the fourth level page table
is allocated contiguously in physical memory, then the page table entry one layer up can be
marked to poi nt directly to this region instead of to a page table. Likewise, a page of third
level page table can be omitted if the operating system allocates the process a 1 GB chunk of
physical memory. In addition to saving space needed for page table mappings, this improves
translation buffer efficiency, a point we will discuss in more detail in the next section.
8.2.4 Portability
The diversity of different translation mechanisms poses a challenge to the operating system
designer. To be widely used, we want our operating system to be easily portable to a wide
```

#### Chunk 3

- Chunk ID: `eb5a81474b867b77`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `3.30549 rerank_score`

```text
page number is just the position of that virtual page in the table.
The drawback to this approach? Handling hash collisions becomes much harder. If two pages hash to the same table entry,
only one can be stored in the physical page frame. The other has to be elsewhere — either in a secondary hash table entry
or possibly stored on disk. Copying in the new page can take time, and if the program is unlucky enough to need to
simultaneously access two virtual pages that both hash to the same physical page, the system will slow down even further.
As a result, on modern systems, inverted page tables are typically used in software to improve portability, rather than in
hardware, to eliminate the need for multi-level page tables.
8.3 Towards Efficient Address Translation
```

#### Chunk 4

- Chunk ID: `5bf34a6ee82f0acc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `60`
- Score: `3.15209 rerank_score`

```text
at today’s computers and wonder how we could have gotten by with as little as a
gigabyte of DRAM! These massive memories will require ever deeper multi-level page
tables. Fortunately, the same trends that make it possible to build gigantic memories also
make it possible to design very large TLBs to hide the increasing depth of the lookup
trees.
Multiprocessors. On the other hand, multiprocessors will mean that maintaining TLB
consistency will become increasingly expensive. A key assumption for using page table
protection hardware for implementing copy-on-write and fill-on-demand is that the cost
of modifying page table entries is modest. One possibility is that hardware will be
added to systems to make TLB shootdown a much cheaper operation, e.g., by making
```

#### Chunk 5

- Chunk ID: `32d8920459496302`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `33`
- Score: `2.7453 rerank_score`

```text
On the Sun Microsystems SPARC processor for example, there are three levels of page table.
As shown in Figure 8.8, the top-level page table contains entries, each of which points to a
second-level page table whose entries are pointers to page tables. On the SPARC, as with
most other systems that use multiple levels of page tables, each level of page table is
designed to fit in a physical page frame. Only the top-level page table must be filled in; the
lower levels of the tree are allocated only if those portions of the virtual address space are in
use by a particular process. Access permissions can be specified at each level, and so
sharing between processes is possible at each level.
```

## q37

**Question:** Why can a sparse virtual address space be useful even when a process is using only a small fraction of its possible addresses?

### Method A

- Retrieval latency: 0.200s
- Generation latency: 7.437s

**Answer:**

A sparse virtual address space is useful because the process can have a large, convenient address layout without needing physical memory for all of it.

For example:

- The stack can start near the top of the virtual address space and grow downward.
- The heap can start lower and grow upward.
- Large unused gaps can exist between them.
- Shared libraries, memory-mapped files, or dynamically allocated regions can be placed far apart without needing to be packed tightly.

The key idea is:

> Virtual addresses do not have to correspond to physical memory until the process actually uses them.

So a process might have a huge possible address range, but only the pages it touches need physical page frames. This gives the operating system flexibility while making the program’s memory layout simpler and safer.

For example, the process may see:

```text
code     heap        unused gap            stack
|----|   |----->     ...........        <----|
```

Even if the gap is enormous, it costs little or no physical memory because no physical pages are allocated for unused virtual addresses.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4a5417ec6df0231f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `0.738605 vector_distance`

```text
Memory sharing. We want to allow multiple processes to share selected regions of
memory. These shared regions can be large (e.g., if we are sharing a program’s code
segment among multiple processes executing the same program) or relatively small (e.g.,
if we are sharing a common library, a file, or a shared data structure).
Flexible memory placement. We want to allow the operating system the flexibility to
place a process (and each part of a process) anywhere in physical memory; this will
allow us to pack physical memory more efficiently. As we will see in the next chapter,
flexibility in assigning process data to physical memory locations will also enable us to
make more effective use of on-chip caches.
Sparse addresses. Many programs have multiple dynamic memory regions that can
```

#### Chunk 2

- Chunk ID: `57d9d2e10aeb5e8c`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `61`
- Score: `0.777546 vector_distance`

```text
many systems with virtual addresses allocate physical memory in fixed-sized, rather than
variable-sized, chunks to reduce fragmentation.
Virtual addresses can also let the heap and the stack start at separate ends of the virtual
address space so they can grow according to program need (Figure 2.6). If either the stack or
heap grows beyond its initially allocated region, the operating system can move it to a
different larger region in physical memory but leave it at the same virtual address. The
expansion is completely transparent to the user process. We discuss virtual addresses in more
depth in Chapter 8.
Figure 2.6: Virtual addresses allow the stack and heap regions of a process to grow independently. To grow the heap, the
```

#### Chunk 3

- Chunk ID: `e1e88d38b9413270`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `0.786727 vector_distance`

```text
In practice, modern systems use much more complex algorithms to translate between virtual
and physical addresses. The layer of indirection provided by virtual addresses gives
operating systems enormous flexibility to efficiently manage physical memory. For example,
```

#### Chunk 4

- Chunk ID: `1527b92e83a269c2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.792964 vector_distance`

```text
using virtual addresses; its virtual addresses are still linear. However, the instruction located
at the end of a page will be located in a completely different region of physical memory from
the next instruction at the start of the next page. Data structures will appear to be contiguous
using virtual addresses, but a large matrix may be scattered across many physical page
frames.
An apt analogy is what happens when you shuffle several decks of cards together. A single
process in its virtual address space sees the cards of a single deck in order. A different
process sees a completely different deck, but it will also be in order. In physical memory,
however, the decks of all the processes currently running will be shuffled together, apparently
```

#### Chunk 5

- Chunk ID: `b2714ae534beedcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.797017 vector_distance`

```text
The advantage of virtual memory is flexibility. The system can continue to function even
though the user has started more processes than can fit in main memory at the same time. The
operating system simply makes room for the new processes by paging the memory of idle
applications to disk. Without virtual memory, the user has to do m emory management by hand,
closing some applications to make room for others.
All of the mechanisms we have described for memory-mapped files apply when we
generalize to virtual memory, with one additional twist. We need to balance the allocation of
physical page frames between processes. Unfortunately, this balancing is quite tricky. If we
add a few extra page faults to a system, no one will notice. However, a modern disk can
```

### Method B

- Retrieval latency: 0.817s
- Generation latency: 10.257s

**Answer:**

A sparse virtual address space is useful because the process can have a **large, convenient address layout** without needing physical memory for all of it.

For example:

- The **heap and stack** can start far apart and grow independently without immediately colliding.
- The OS can place **shared libraries, memory-mapped files, and shared memory regions** at convenient virtual addresses.
- Large data structures can appear **contiguous in virtual memory**, even if their physical pages are scattered in RAM.
- Unused virtual address ranges usually consume **no physical memory**; physical pages are allocated only when the process actually uses those addresses.
- Empty gaps can act as protection regions, helping catch bugs like stack overflows or invalid pointer accesses.

So even if a process uses only a small fraction of its possible virtual addresses, the large sparse space gives the OS and program flexibility while avoiding actual physical memory waste.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `4a5417ec6df0231f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `n/a `

```text
Memory sharing. We want to allow multiple processes to share selected regions of
memory. These shared regions can be large (e.g., if we are sharing a program’s code
segment among multiple processes executing the same program) or relatively small (e.g.,
if we are sharing a common library, a file, or a shared data structure).
Flexible memory placement. We want to allow the operating system the flexibility to
place a process (and each part of a process) anywhere in physical memory; this will
allow us to pack physical memory more efficiently. As we will see in the next chapter,
flexibility in assigning process data to physical memory locations will also enable us to
make more effective use of on-chip caches.
Sparse addresses. Many programs have multiple dynamic memory regions that can
```

#### Chunk 2

- Chunk ID: `57d9d2e10aeb5e8c`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `61`
- Score: `n/a `

```text
many systems with virtual addresses allocate physical memory in fixed-sized, rather than
variable-sized, chunks to reduce fragmentation.
Virtual addresses can also let the heap and the stack start at separate ends of the virtual
address space so they can grow according to program need (Figure 2.6). If either the stack or
heap grows beyond its initially allocated region, the operating system can move it to a
different larger region in physical memory but leave it at the same virtual address. The
expansion is completely transparent to the user process. We discuss virtual addresses in more
depth in Chapter 8.
Figure 2.6: Virtual addresses allow the stack and heap regions of a process to grow independently. To grow the heap, the
```

#### Chunk 3

- Chunk ID: `1527b92e83a269c2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `n/a `

```text
using virtual addresses; its virtual addresses are still linear. However, the instruction located
at the end of a page will be located in a completely different region of physical memory from
the next instruction at the start of the next page. Data structures will appear to be contiguous
using virtual addresses, but a large matrix may be scattered across many physical page
frames.
An apt analogy is what happens when you shuffle several decks of cards together. A single
process in its virtual address space sees the cards of a single deck in order. A different
process sees a completely different deck, but it will also be in order. In physical memory,
however, the decks of all the processes currently running will be shuffled together, apparently
```

#### Chunk 4

- Chunk ID: `b2714ae534beedcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `n/a `

```text
The advantage of virtual memory is flexibility. The system can continue to function even
though the user has started more processes than can fit in main memory at the same time. The
operating system simply makes room for the new processes by paging the memory of idle
applications to disk. Without virtual memory, the user has to do m emory management by hand,
closing some applications to make room for others.
All of the mechanisms we have described for memory-mapped files apply when we
generalize to virtual memory, with one additional twist. We need to balance the allocation of
physical page frames between processes. Unfortunately, this balancing is quite tricky. If we
add a few extra page faults to a system, no one will notice. However, a modern disk can
```

#### Chunk 5

- Chunk ID: `e3804c71ee21ccaf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `115`
- Score: `n/a `

```text
Figure 10.5: When a host kernel runs multiple virtual machines, it can save space by storing a delta to an existing page
(page A) and by using the same physical page frame for multiple copies of the same page (page B).
There are two cases to consider, shown in Figure 10.5:
Multiple copies of the same page. Two different virtual machines will often have
pages with the same contents. An obvious case is zeroed pages: each kernel keeps a
pool of pages that have been zeroed, ready to be allocated to a new process. If each
guest operating system were running on its own machine, there would be little cost to
keeping this pool at the ready; no one else but the kernel can use that memory. However,
when the physical machine is shared between virtual machines, having each guest keep
```

### Method C

- Retrieval latency: 0.474s
- Generation latency: 7.614s

**Answer:**

A sparse virtual address space is useful because it lets the OS give different memory regions lots of “empty” room to grow without needing them to be physically contiguous.

For example, a process may have:

- a heap that grows upward,
- a stack that grows downward,
- separate stacks for multiple threads,
- memory-mapped files or libraries in different regions.

Even if most virtual addresses are unused, those unused gaps are valuable because they prevent regions from immediately colliding with each other as they grow.

The key idea is:

> Virtual addresses can be spread out, while physical memory is only allocated for the parts actually used.

So a process can see a large, clean, linear address space, even though its actual pages may be scattered in physical memory.

This is especially useful on 64-bit systems, where the address space is huge. The downside is that a very sparse address space can make page tables larger or more complex, because the system still needs some way to represent which virtual addresses are valid and where they map.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `fc1e9016434cd3e1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `3.99916 rerank_score`

```text
multiple threads per process, we need multiple thread stacks, each with room to grow.
This becomes even more of an issue with 64-bit virtual address spaces. The size of the page
table is proportional to the size of the virtual address space, not to the size of physical
memory. The more sparse the virtual address space, the more overhead is needed for the page
table. Most of the entries will be invalid, representing parts of the virtual address space that
are not in use, but physical memory is still needed for all of those page table entries.
We can reduce the space taken up by the page table by choosing a larger page frame. How big
should a page frame be? A larger page frame can waste space if a process does not use all of
```

#### Chunk 2

- Chunk ID: `53bbd3d6ec8d5627`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `2.96099 rerank_score`

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

#### Chunk 3

- Chunk ID: `57d9d2e10aeb5e8c`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `61`
- Score: `2.11767 rerank_score`

```text
many systems with virtual addresses allocate physical memory in fixed-sized, rather than
variable-sized, chunks to reduce fragmentation.
Virtual addresses can also let the heap and the stack start at separate ends of the virtual
address space so they can grow according to program need (Figure 2.6). If either the stack or
heap grows beyond its initially allocated region, the operating system can move it to a
different larger region in physical memory but leave it at the same virtual address. The
expansion is completely transparent to the user process. We discuss virtual addresses in more
depth in Chapter 8.
Figure 2.6: Virtual addresses allow the stack and heap regions of a process to grow independently. To grow the heap, the
```

#### Chunk 4

- Chunk ID: `1527b92e83a269c2`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.792078 rerank_score`

```text
using virtual addresses; its virtual addresses are still linear. However, the instruction located
at the end of a page will be located in a completely different region of physical memory from
the next instruction at the start of the next page. Data structures will appear to be contiguous
using virtual addresses, but a large matrix may be scattered across many physical page
frames.
An apt analogy is what happens when you shuffle several decks of cards together. A single
process in its virtual address space sees the cards of a single deck in order. A different
process sees a completely different deck, but it will also be in order. In physical memory,
however, the decks of all the processes currently running will be shuffled together, apparently
```

#### Chunk 5

- Chunk ID: `9078584b68d2f01a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `21`
- Score: `-0.0341039 rerank_score`

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

## q38

**Question:** If virtual memory lets the OS move pages between RAM and disk, why doesn’t that mean programs can effectively use unlimited memory with little downside?

### Method A

- Retrieval latency: 0.541s
- Generation latency: 8.301s

**Answer:**

Because virtual memory only makes memory **look larger and more flexible**; it does not make disk behave like RAM.

The key limitation is performance.

Virtual memory works by keeping some pages in RAM and moving less-used pages to disk. If a program accesses a page that is not currently in RAM, a **page fault** occurs:

1. CPU tries to access a virtual page.
2. Page table says it is not in physical memory.
3. OS traps into the kernel.
4. OS loads the page from disk into RAM.
5. Program resumes.

That is much slower than a normal memory access.

So virtual memory works well when a program’s **working set** — the pages it actively uses — fits in RAM. Then only occasional page faults happen.

But if the program actively uses more memory than RAM can hold, the OS keeps swapping pages in and out. This is called **thrashing**. The system spends most of its time moving pages between RAM and disk instead of running the program.

So the downside is:

- RAM access: very fast
- Disk/SSD access: much slower
- Too many page faults: severe slowdown
- Disk space is still finite
- Virtual address space is also finite

In short:

> Virtual memory lets programs exceed physical RAM, but only efficiently if most active pages still fit in RAM. It trades memory capacity for potentially huge performance cost.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b2714ae534beedcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `1.11788 rerank_score`

```text
The advantage of virtual memory is flexibility. The system can continue to function even
though the user has started more processes than can fit in main memory at the same time. The
operating system simply makes room for the new processes by paging the memory of idle
applications to disk. Without virtual memory, the user has to do m emory management by hand,
closing some applications to make room for others.
All of the mechanisms we have described for memory-mapped files apply when we
generalize to virtual memory, with one additional twist. We need to balance the allocation of
physical page frames between processes. Unfortunately, this balancing is quite tricky. If we
add a few extra page faults to a system, no one will notice. However, a modern disk can
```

#### Chunk 2

- Chunk ID: `2c9f46365db80529`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `-0.214849 rerank_score`

```text
caching; if the system runs out of memory, less frequently used code may be converted
each time it is needed.
Virtual memory. Operating systems can run programs that do n ot fit in physical memory
by using main memory as a cache for disk. Application pages that fit in memory have
their page table entries set to valid; these pages can be accessed directly by the
processor. Those pages that do n ot fit have their permissions set to invalid, triggering a
trap to the operating system kernel. The kernel will then fetch the required page from
disk and resume the application at the instruction that caused the trap.
File systems. File systems also treat memory as a cache for disk. They store copies in
memory of frequently used directories and files, reducing the need for disk accesses.
```

#### Chunk 3

- Chunk ID: `fcb5ffd483154c01`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `-0.750035 rerank_score`

```text
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
Demand paged virtual memory. The operating system can run programs that use more
memory than is physically present on the computer, by catching references to pages that
are not physically present and filling them from disk or cluster memory.
In this chapter, we explore how to construct a number of other advanced ope rating system
services by catching and re-interpreting memory references and system calls.
Chapter roadmap:
Zero-Copy I/O. How do we improve the performance of transferring blocks of data
between user-level programs and hardware devices? (Section 10.1)
Virtual Machines. How do we execute an operating system on top of another operating
```

#### Chunk 4

- Chunk ID: `8f0ad649675f606f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `100`
- Score: `-0.967671 rerank_score`

```text
to transfer 256 contiguous pages as it does to transfer one, so internally, most operating
systems arrange disk transfers to include many blocks at a time. With new technologies
such as low latency solid state storage and cluster memory, this balance may shift back
towards smaller effective page sizes.
Memory aw are applications. The increasing depth and complexity of the memory
hierarchy is both a boon  and a curse. For many applications, the memory hierarchy
delivers reasonable performance without any special effort. However, the wide gulf in
performance between the first level cache and main memory, and between main memory
and disk, implies that there is a significant performance benefit to tuning applications to
```

#### Chunk 5

- Chunk ID: `f45b120e6d8ff3de`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `96`
- Score: `-1.10222 rerank_score`

```text
TLB, there is a trap to the kernel to look up the translation. During the trap, the kernel can update its list of frequently used
pages.
9.7 Case Study: Virtual Memory
We can generalize on the concept of memory-mapped files, by backing every memory segment
with a file on disk. This is called virtual memory. Program executables, individual libraries,
data, stack and heap segments can all be demand paged to disk. Unlike memory-mapped files,
though, process memory is ephemeral: when the process exits, there is no need to write
modified data back to disk, and we can reclaim the disk space.
```

### Method B

- Retrieval latency: 0.200s
- Generation latency: 9.066s

**Answer:**

Because virtual memory makes memory **larger in appearance**, not **equally fast or truly unlimited**.

The key idea is:

> RAM acts like a cache for pages stored on disk.

If a program accesses a page that is already in RAM, it runs normally.  
But if the page has been moved to disk, the CPU triggers a **page fault**, and the OS must load that page back into RAM before the program can continue.

That has big downsides:

1. **Disk/SSD is much slower than RAM**  
   Accessing RAM is extremely fast. Loading a page from disk is thousands to millions of times slower, depending on the device.

2. **Too many page faults destroy performance**  
   If a program’s active data set does not fit in RAM, the OS keeps moving pages back and forth between RAM and disk. This is called **thrashing**.

3. **Programs need a working set in RAM**  
   A program can tolerate some unused pages being on disk. But the pages it is actively using need to stay in RAM for good performance.

4. **Virtual memory is still limited**  
   It is limited by things like:
   - address space size
   - available disk/swap space
   - OS policies
   - performance constraints

So virtual memory lets the OS run programs whose total allocated memory is larger than physical RAM, but only efficiently when the actively used pages fit mostly in RAM.

A good summary:

> Virtual memory gives the illusion of more memory, but if the illusion is used too heavily, the system pays for it with page faults and severe slowdown.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b2714ae534beedcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.550557 vector_distance`

```text
The advantage of virtual memory is flexibility. The system can continue to function even
though the user has started more processes than can fit in main memory at the same time. The
operating system simply makes room for the new processes by paging the memory of idle
applications to disk. Without virtual memory, the user has to do m emory management by hand,
closing some applications to make room for others.
All of the mechanisms we have described for memory-mapped files apply when we
generalize to virtual memory, with one additional twist. We need to balance the allocation of
physical page frames between processes. Unfortunately, this balancing is quite tricky. If we
add a few extra page faults to a system, no one will notice. However, a modern disk can
```

#### Chunk 2

- Chunk ID: `aa35eaa9299f196a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `124`
- Score: `0.705681 vector_distance`

```text
physical memory. If the operating system evicts a page that the database expects to be in
memory, these algorithms will run much more slowly.
Virtual machines. A similar issue arises with virtual machines. The guest operating
system running inside of a virtual machine thinks it has a set of physical page frames,
which it can assign to the virtual pages of applications running in the virtual machine. In
reality, however, the page frames in the guest operating system are virtual and can be
paged to disk by the host operating system. If the host operating system could tell the
guest operating system when it needed to steal a page frame (or donate a page frame),
then the guest would know exactly how many page frames were available to be
allocated to its applications.
```

#### Chunk 3

- Chunk ID: `2c9f46365db80529`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `0.719338 vector_distance`

```text
caching; if the system runs out of memory, less frequently used code may be converted
each time it is needed.
Virtual memory. Operating systems can run programs that do n ot fit in physical memory
by using main memory as a cache for disk. Application pages that fit in memory have
their page table entries set to valid; these pages can be accessed directly by the
processor. Those pages that do n ot fit have their permissions set to invalid, triggering a
trap to the operating system kernel. The kernel will then fetch the required page from
disk and resume the application at the instruction that caused the trap.
File systems. File systems also treat memory as a cache for disk. They store copies in
memory of frequently used directories and files, reducing the need for disk accesses.
```

#### Chunk 4

- Chunk ID: `e1e88d38b9413270`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `60`
- Score: `0.721065 vector_distance`

```text
In practice, modern systems use much more complex algorithms to translate between virtual
and physical addresses. The layer of indirection provided by virtual addresses gives
operating systems enormous flexibility to efficiently manage physical memory. For example,
```

#### Chunk 5

- Chunk ID: `e1149008fcb25c62`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `25`
- Score: `0.734992 vector_distance`

```text
operating system provides applications the illusion of a nearly infinite amount of virtual
memory. Wireless networks drop or  corrupt packets; the operating system masks these
failures to provide the illusion of a reliable service. At a physical level, magnetic disk and
flash RAM support block reads and writes, where the size of the block depends on the
physical device characteristics, addressed by a device-specific block number. Most
programmers prefer to work with byte-addressable files organized by name into hierarchical
directories. Even the type of processor can be virtualized to allow the same, unmodified
application to run on a smartphone, tablet, and laptop computer.
Figure 1.4: A guest operating system running inside a virtual machine.
```

### Method C

- Retrieval latency: 1.620s
- Generation latency: 7.906s

**Answer:**

Because virtual memory gives the *illusion* of a large memory, not free memory.

The OS can move pages between RAM and disk, but the downside is that disk/SSD access is much slower than RAM.

When a program accesses a page that is not currently in RAM:

1. The CPU triggers a **page fault**.
2. The OS pauses the program.
3. The OS loads the needed page from disk into RAM.
4. If RAM is full, it may have to evict another page first.
5. The program resumes.

That is much slower than a normal memory access.

So virtual memory works well when most of the program’s actively used pages fit in RAM. This active set is often called the **working set**.

But if a program uses more memory actively than RAM can hold, the OS constantly swaps pages in and out. This is called **thrashing**.

In that situation, the system spends more time moving pages between RAM and disk than actually running the program.

So the key idea is:

> Virtual memory lets programs use more memory than physical RAM, but only efficiently if the currently active pages fit in RAM.

It is not unlimited because:

- disk space is finite,
- virtual address space is finite,
- page tables and bookkeeping take memory too,
- and disk/SSD is far slower than RAM.

So virtual memory improves flexibility, but excessive memory use can cause major slowdown.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `b2714ae534beedcf`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `n/a `

```text
The advantage of virtual memory is flexibility. The system can continue to function even
though the user has started more processes than can fit in main memory at the same time. The
operating system simply makes room for the new processes by paging the memory of idle
applications to disk. Without virtual memory, the user has to do m emory management by hand,
closing some applications to make room for others.
All of the mechanisms we have described for memory-mapped files apply when we
generalize to virtual memory, with one additional twist. We need to balance the allocation of
physical page frames between processes. Unfortunately, this balancing is quite tricky. If we
add a few extra page faults to a system, no one will notice. However, a modern disk can
```

#### Chunk 2

- Chunk ID: `2c9f46365db80529`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `n/a `

```text
caching; if the system runs out of memory, less frequently used code may be converted
each time it is needed.
Virtual memory. Operating systems can run programs that do n ot fit in physical memory
by using main memory as a cache for disk. Application pages that fit in memory have
their page table entries set to valid; these pages can be accessed directly by the
processor. Those pages that do n ot fit have their permissions set to invalid, triggering a
trap to the operating system kernel. The kernel will then fetch the required page from
disk and resume the application at the instruction that caused the trap.
File systems. File systems also treat memory as a cache for disk. They store copies in
memory of frequently used directories and files, reducing the need for disk accesses.
```

#### Chunk 3

- Chunk ID: `e1149008fcb25c62`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `25`
- Score: `n/a `

```text
operating system provides applications the illusion of a nearly infinite amount of virtual
memory. Wireless networks drop or  corrupt packets; the operating system masks these
failures to provide the illusion of a reliable service. At a physical level, magnetic disk and
flash RAM support block reads and writes, where the size of the block depends on the
physical device characteristics, addressed by a device-specific block number. Most
programmers prefer to work with byte-addressable files organized by name into hierarchical
directories. Even the type of processor can be virtualized to allow the same, unmodified
application to run on a smartphone, tablet, and laptop computer.
Figure 1.4: A guest operating system running inside a virtual machine.
```

#### Chunk 4

- Chunk ID: `f45b120e6d8ff3de`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `96`
- Score: `n/a `

```text
TLB, there is a trap to the kernel to look up the translation. During the trap, the kernel can update its list of frequently used
pages.
9.7 Case Study: Virtual Memory
We can generalize on the concept of memory-mapped files, by backing every memory segment
with a file on disk. This is called virtual memory. Program executables, individual libraries,
data, stack and heap segments can all be demand paged to disk. Unlike memory-mapped files,
though, process memory is ephemeral: when the process exits, there is no need to write
modified data back to disk, and we can reclaim the disk space.
```

#### Chunk 5

- Chunk ID: `dc5d9c4a13be9e5d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `n/a `

```text
memory. With multiple threads, a program can use explicit read/write calls to pipeline
disk I/O, but it needs to manage the pipeline itself.
Interprocess communication. Two or more processes can share information
instantaneously through a memory-mapped file without needing to shuffle data back and
forth to the kernel or to disk. If the hardware architecture supports it, the page table for
the shared segment can also be shared.
Large files. As long as the page table for the file can fit in physical memory, the only
limit on the size of a memory-mapped file is the size of the virtual address space. For
example, an application may have a giant multi-level tree indexing data spread across a
number of disks in a data center. With read/write system calls, the application needs to
```

## q39

**Question:** What exactly is a page fault, and why is it not always an error?

### Method A

- Retrieval latency: 0.465s
- Generation latency: 8.707s

**Answer:**

A **page fault** is an event that happens when a program accesses a virtual memory page that is **not currently available in physical memory** or whose page table entry is not usable for that access.

In typical steps:

1. The CPU tries to access a virtual address.
2. It checks the TLB/page table.
3. The page table entry may be marked **invalid** or not present.
4. The hardware raises a **page fault exception** and traps into the operating system.
5. The OS decides what to do.

It is **not always an error** because “fault” here means “the CPU needs OS help,” not necessarily “the program is wrong.”

For example, a page fault can be normal when:

- The page is stored on disk and must be loaded into RAM.
- The program is using **demand paging**, where pages are loaded only when first used.
- The OS is doing **lazy allocation**, giving physical memory only when actually needed.
- A page was swapped out and needs to be brought back.
- Copy-on-write memory needs to be duplicated after a write.

In these cases, the OS handles the page fault, updates the page table, and the program continues as if nothing went wrong.

It becomes an actual error only if the access is illegal, for example:

- Accessing an address outside the process’s valid memory.
- Writing to a read-only page.
- Violating memory protection rules.

That kind of page fault may cause the OS to terminate the process, e.g. with a segmentation fault.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `8d1a10baeb68efef`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `91`
- Score: `3.57713 rerank_score`

```text
Figure 9.17: Before a page fault, the page table has an invalid entry for the referenced page and the data for the page is
stored on disk.
Figure 9.18: After the page fault, the page table has a valid entry for the referenced page with the page frame containing
the data that had been stored on disk. The old contents of the page frame are stored on disk and the page table entry that
previously pointed to the page frame is set to invalid.
When the process issues an instruction that touches an invalid mapped address, a sequence of
events occurs, illustrated in Figures 9.17 and  9.18:
TLB miss. The hardware looks the virtual page up in the TLB, and finds that there is not
a valid entry. This triggers a full page table lookup in hardware.
```

#### Chunk 2

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.944804 rerank_score`

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 3

- Chunk ID: `051d0a08cff94c5c`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `125`
- Score: `0.63754 rerank_score`

```text
Figure 10.8: The operation of a user-level page handler. On a page fault, the hardware traps to the kernel; if the fault
is for a segment with a user-level pager, the kernel passes the fault to the user-level handler to manage. The user-level
handler is pinned in memory to avoid recursive faults.
User-level pagers. A more general solution is for applications to specify a user-level
page  handl er for a memory segment. On a page fault or protection violation, the kernel
trap handler is invoked. Instead of handling the fault itself, the kernel passes control to
user-level handler, as in a UNIX signal handler. The user-level handler can then decide
how to manage the trap: where to fetch the missing page, what action to take if the
```

#### Chunk 4

- Chunk ID: `3fd209f9216fc4fc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `91`
- Score: `-0.512899 rerank_score`

```text
a valid entry. This triggers a full page table lookup in hardware.
Page table exception. The hardware walks the multi-level page table and finds the
page table entry is invalid. This causes a hardware page  fault exception trap into the
operating system kernel.
```

#### Chunk 5

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `-0.709587 rerank_score`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

### Method B

- Retrieval latency: 0.283s
- Generation latency: 8.049s

**Answer:**

A **page fault** happens when a program tries to access a virtual memory page, but the CPU cannot currently use that page’s mapping.

Most commonly:

1. The program references some virtual address.
2. The CPU checks the TLB/page table.
3. The page table entry says the page is **invalid** or not currently in physical memory.
4. The CPU traps into the operating system kernel.
5. The OS decides what to do.

It is called a “fault,” but it is **not always an error**.

A page fault is normal if the page is valid for the process but just **not currently loaded into RAM**. For example, with demand paging, the OS may keep some pages on disk until they are actually needed. When the process touches such a page, the OS:

- finds the page on disk,
- loads it into a physical page frame,
- updates the page table entry to valid,
- resumes the program at the instruction that caused the fault.

From the program’s point of view, execution continues normally, just more slowly.

It is an actual error if the process accesses an address it is **not allowed** to access, such as:

- an unmapped address,
- memory belonging to another process,
- a protected page, e.g. writing to a read-only page.

So the key distinction is:

> A page fault means “the current memory access cannot be completed immediately.”  
> The OS then determines whether it is a normal recoverable event or an illegal memory access.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `8d1a10baeb68efef`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `91`
- Score: `0.802903 vector_distance`

```text
Figure 9.17: Before a page fault, the page table has an invalid entry for the referenced page and the data for the page is
stored on disk.
Figure 9.18: After the page fault, the page table has a valid entry for the referenced page with the page frame containing
the data that had been stored on disk. The old contents of the page frame are stored on disk and the page table entry that
previously pointed to the page frame is set to invalid.
When the process issues an instruction that touches an invalid mapped address, a sequence of
events occurs, illustrated in Figures 9.17 and  9.18:
TLB miss. The hardware looks the virtual page up in the TLB, and finds that there is not
a valid entry. This triggers a full page table lookup in hardware.
```

#### Chunk 2

- Chunk ID: `051d0a08cff94c5c`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `125`
- Score: `0.855393 vector_distance`

```text
Figure 10.8: The operation of a user-level page handler. On a page fault, the hardware traps to the kernel; if the fault
is for a segment with a user-level pager, the kernel passes the fault to the user-level handler to manage. The user-level
handler is pinned in memory to avoid recursive faults.
User-level pagers. A more general solution is for applications to specify a user-level
page  handl er for a memory segment. On a page fault or protection violation, the kernel
trap handler is invoked. Instead of handling the fault itself, the kernel passes control to
user-level handler, as in a UNIX signal handler. The user-level handler can then decide
how to manage the trap: where to fetch the missing page, what action to take if the
```

#### Chunk 3

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.876043 vector_distance`

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 4

- Chunk ID: `3fd209f9216fc4fc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `91`
- Score: `0.885457 vector_distance`

```text
a valid entry. This triggers a full page table lookup in hardware.
Page table exception. The hardware walks the multi-level page table and finds the
page table entry is invalid. This causes a hardware page  fault exception trap into the
operating system kernel.
```

#### Chunk 5

- Chunk ID: `0dd79102b293289e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `92`
- Score: `0.933046 vector_distance`

```text
Page table update. The kernel updates the page table entry to poi nt to the page frame
allocated for the block and sets the entry to valid.
Resume process. The operating system resumes execution of the process at the
instruction that caused the exception.
TLB miss. The TLB still does not contain a valid entry for the page, triggering a full
page table lookup.
Page table fetch. The hardware walks the multi-level page table, finds the page table
entry valid, and returns the page frame to the processor. The processor loads the TLB
with the new translation, evicting a previous TLB entry, and then uses the translation to
construct a physical address for the instruction.
To make this work, we need an empty page frame to hold the incoming page from disk. To
```

### Method C

- Retrieval latency: 0.835s
- Generation latency: 9.200s

**Answer:**

A **page fault** is an event where a program tries to access a virtual memory page, but the CPU cannot currently translate that page to a valid physical memory frame.

In other words:

> The program uses a virtual address, but the needed page is not currently available in RAM or is not accessible with the requested permissions.

When this happens, the hardware **traps to the operating system kernel**, and the kernel decides what to do.

It is **not always an error** because many page faults are part of normal virtual memory operation.

Examples of normal page faults:

1. **Demand paging**  
   A program accesses a page that belongs to it, but the page has not been loaded into RAM yet.  
   The OS reads it from disk, updates the page table, and resumes the program.

2. **Memory-mapped files**  
   If a file is mapped into memory, accessing part of the file may cause a page fault so the OS can load that part from disk.

3. **Stack growth**  
   A program’s stack may grow into a new page. The OS can allocate a new page when it is first touched.

4. **Copy-on-write**  
   After `fork()`, parent and child may share pages marked read-only. If one writes to a shared page, a page fault occurs so the OS can make a private copy.

A page fault becomes an actual error only if the access is invalid, for example:

```c
int *p = NULL;
*p = 5;
```

Here the program accesses memory it is not allowed to use, so the OS may terminate it with a **segmentation fault**.

So the key idea is:

> A page fault means “the CPU needs OS help with this memory access,” not necessarily “the program did something wrong.”

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `n/a `

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 2

- Chunk ID: `051d0a08cff94c5c`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `125`
- Score: `n/a `

```text
Figure 10.8: The operation of a user-level page handler. On a page fault, the hardware traps to the kernel; if the fault
is for a segment with a user-level pager, the kernel passes the fault to the user-level handler to manage. The user-level
handler is pinned in memory to avoid recursive faults.
User-level pagers. A more general solution is for applications to specify a user-level
page  handl er for a memory segment. On a page fault or protection violation, the kernel
trap handler is invoked. Instead of handling the fault itself, the kernel passes control to
user-level handler, as in a UNIX signal handler. The user-level handler can then decide
how to manage the trap: where to fetch the missing page, what action to take if the
```

#### Chunk 3

- Chunk ID: `0dd79102b293289e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `92`
- Score: `n/a `

```text
Page table update. The kernel updates the page table entry to poi nt to the page frame
allocated for the block and sets the entry to valid.
Resume process. The operating system resumes execution of the process at the
instruction that caused the exception.
TLB miss. The TLB still does not contain a valid entry for the page, triggering a full
page table lookup.
Page table fetch. The hardware walks the multi-level page table, finds the page table
entry valid, and returns the page frame to the processor. The processor loads the TLB
with the new translation, evicting a previous TLB entry, and then uses the translation to
construct a physical address for the instruction.
To make this work, we need an empty page frame to hold the incoming page from disk. To
```

#### Chunk 4

- Chunk ID: `7069ece085f5f421`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `116`
- Score: `n/a `

```text
for the host kernel to introduce a new layer in the memory hierarchy to save space.
Instead of evicting a relatively unused page, the operating system can compress it. If the
page is a delta of an existing page, the compressed version may be quite small. The
kernel manipulates page table permissions to maintain the illusion that the delta is a real
page. The full copy of the page is marked read-only; the delta is marked invalid. If the
delta is referenced, it can be re-constituted as a full page more quickly than if it was
stored on disk. If the original page is modified, the delta can be re-compressed or
evicted, as necessary.
10.3 Fault Tolerance
All systems break. Despite our best efforts, application code can have bugs that cause the
```

#### Chunk 5

- Chunk ID: `e7a65ad988d57fd7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `92`
- Score: `n/a `

```text
Convert virtual address to file offset. In the exception handler, the kernel looks up in
its segment table to find the file corresponding to the faulting virtual address and
converts the address to a file offset.
Disk block read. The kernel allocates an empty page frame and issues a disk operation
to read the required file block into the allocated page frame. While the disk operation is
in progress, the processor can be used for running other threads or processes.
Disk interrupt. The disk interrupts the processor when the disk read finishes, and the
scheduler resumes the kernel thread handling the page fault exception.
Page table update. The kernel updates the page table entry to poi nt to the page frame
allocated for the block and sets the entry to valid.
```

## q40

**Question:** If caches are supposed to speed things up, why do some access patterns still perform badly even when the same total amount of data is used?

### Method A

- Retrieval latency: 0.730s
- Generation latency: 8.895s

**Answer:**

Because cache performance depends not just on **how much data** you use, but on **how you access it**.

A cache is fast only when it can correctly “guess” what you will need soon. Good access patterns have **locality**:

- **Temporal locality**: you reuse the same data soon.
- **Spatial locality**: you access nearby data soon.

So two programs may use the same total amount of data, but behave very differently.

Example:

```text
Good pattern:
A[0], A[1], A[2], A[3], ...
```

This has spatial locality. When the cache loads `A[0]`, it usually loads nearby values too, so `A[1]`, `A[2]`, etc. may already be cached.

Bad pattern:

```text
A[0], A[1000000], A[2000000], A[3000000], ...
```

This jumps around memory. Each access may require loading a new cache block, while the previously loaded data is not reused.

Another bad case is when the program’s **working set** is larger than the cache. Then useful data gets evicted before it is reused. This causes many **cache misses**, sometimes called **thrashing**.

So even with the same total data size, performance can be bad if the access pattern causes a low cache hit rate:

```text
Average latency =
P(cache hit) × hit latency +
P(cache miss) × miss latency
```

If the access pattern produces many misses, the program spends much more time waiting for slower memory.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `00f14a9c68f65e10`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `76`
- Score: `n/a `

```text
frequently accessed web pages to speed web access and reduce network traffic. Web access
patterns cause two challenges to a cache designer:
New data. New pages are being added to the web at a rapid rate, and page contents also
change. Every time a user accesses a page, the system needs to check whether the page
has changed in the meantime.
No working set. Although some web pages are much more popu lar than others, there is
no small subset of web pages that, if cached, give you the bulk of the benefit. Unlike
with a working set, even very small caches have some value. Conversely, increasing
cache size yields diminishing returns: even very large caches tend to have only modest
cache hit rates, as there are an enormous group of pages that are visited from time to
time.
```

#### Chunk 2

- Chunk ID: `6bf74655cc253b64`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `87`
- Score: `n/a `

```text
system performance. Likewise, if a cached item is expensive to regenerate, it is more important to keep cached than one that
is more easily replaced.
Parallel computing makes the calculus even more complex. The performance of a parallel program depends on its critical
path — the minimum sequence of steps for the program to produce its result. Cache misses that occur on the critical path
affect the response time while those that occur off the critical path do not. For example, a parallel MapReduce job forks a
set of tasks onto processors; each task reads in a file and produces an output. Because MapReduce must wait until all tasks
are complete before moving onto the next step, if any file is not cached it is as bad as if all of the needed files were not
cached.
9.5.6 Belady’s Anomaly
```

#### Chunk 3

- Chunk ID: `7c345f7cb5372cc1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `n/a `

```text
memory of frequently used directories and files, reducing the need for disk accesses.
Conditional branch prediction. Another use of caches is in predicting whether a
conditional branch will be taken or not. In the common case of a correct prediction, the
processor can start decoding the next instruction before the result of the branch is known
for sure; if the prediction turns out to be wrong, the decoding is restarted with the
correct next instruction.
In other words, caches are a central design technique to making computer systems faster.
However, caches are not without their dow nsides. Caches can make understanding the
performance of a system much harder. Something that seems like it should be fast — a nd even
```

#### Chunk 4

- Chunk ID: `071dd5814f2a3c15`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `69`
- Score: `n/a `

```text
referenced at nearly the same time. To exploit this, caches are often designed to load a block
of data at the same time, instead of only a single location. Hardware memory caches often
store 4-64 m emory words as a unit; file caches often store data in pow ers of two of the
hardware page size.
A related design technique that also takes advantage of spatial locality is to prefetch data into
the cache before it is needed. For example, if the file system observes the application reading
a sequence of blocks into memory, it will read the subsequent blocks ahead of time, without
waiting to be asked.
Putting these together, the latency of a read request is as follows:
Latency(read request)   =   Prob(cache hit) × Latency(cache hit)
     + Prob(cache miss) × Latency(cache miss)
```

#### Chunk 5

- Chunk ID: `8a63d280ecef57e0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `69`
- Score: `n/a `

```text
Second, the likelihood of  a cache hit must be high enough to make it worth the effort. One
source of predictability is temporal locality: programs tend to reference the same
instructions and data that they had recently accessed. Examples include the instructions inside
a loop, or  a data structure that is repeatedly accessed. By caching these memory values, we
can improve performance.
Another source of predictability is spatial locality. Programs tend to reference data near
other data that has been recently referenced. For example, the next instruction to execute is
usually near to the previous one, and different fields in the same data structure tend to be
referenced at nearly the same time. To exploit this, caches are often designed to load a block
```

### Method B

- Retrieval latency: 0.429s
- Generation latency: 8.155s

**Answer:**

Because cache speed depends not just on **how much total data** you use, but on **which data you reuse and when**.

A cache only helps if recently or frequently used data is still in the cache when you need it again. Some access patterns destroy that advantage.

For example:

```text
Good pattern:
use A
use A again soon
use A again soon
```

`A` is likely still cached, so later accesses are fast.

But:

```text
Bad pattern:
use A
use B
use C
use D
...
use A much later
```

By the time you return to `A`, it may have been evicted from the cache, so the access is slow again.

So two programs may touch the same total amount of data, but behave differently:

```text
Program 1: repeatedly works on a small region
Program 2: scans through many regions with little reuse
```

Program 1 has good **locality** and gets many cache hits.  
Program 2 has poor locality and gets many cache misses.

This is why caches can make performance hard to predict: something that “should” be fast may be slow if most of the data being accessed is not actually in the cache.

In short:

> Caches speed up repeated nearby accesses, not arbitrary access to the same total amount of data.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `00f14a9c68f65e10`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `76`
- Score: `4.18576 rerank_score`

```text
frequently accessed web pages to speed web access and reduce network traffic. Web access
patterns cause two challenges to a cache designer:
New data. New pages are being added to the web at a rapid rate, and page contents also
change. Every time a user accesses a page, the system needs to check whether the page
has changed in the meantime.
No working set. Although some web pages are much more popu lar than others, there is
no small subset of web pages that, if cached, give you the bulk of the benefit. Unlike
with a working set, even very small caches have some value. Conversely, increasing
cache size yields diminishing returns: even very large caches tend to have only modest
cache hit rates, as there are an enormous group of pages that are visited from time to
time.
```

#### Chunk 2

- Chunk ID: `7d400ea903848ebe`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `0.0480243 rerank_score`

```text
performance of a system much harder. Something that seems like it should be fast — a nd even
something that usually is fast — c an end up being very slow if most of the data is not in the
cache. Because the details of the cache are often hidden behind a level of abstraction, the user
or the programmer may have little idea as to what is causing the poor  performance. In other
```

#### Chunk 3

- Chunk ID: `7c345f7cb5372cc1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `-0.242078 rerank_score`

```text
memory of frequently used directories and files, reducing the need for disk accesses.
Conditional branch prediction. Another use of caches is in predicting whether a
conditional branch will be taken or not. In the common case of a correct prediction, the
processor can start decoding the next instruction before the result of the branch is known
for sure; if the prediction turns out to be wrong, the decoding is restarted with the
correct next instruction.
In other words, caches are a central design technique to making computer systems faster.
However, caches are not without their dow nsides. Caches can make understanding the
performance of a system much harder. Something that seems like it should be fast — a nd even
```

#### Chunk 4

- Chunk ID: `f46cebc27e114bc0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `67`
- Score: `-0.900365 rerank_score`

```text
words, the abstraction of fast access to data can cause problems if the abstraction does not
live up to its promise. One of our aims is to help you understand when caches do a nd do n ot
work well.
In this chapter, we will focus on the caching of memory values, but the principles we discuss
apply much more widely. Memory caching is common in both hardware (by the processor to
improve memory latency) and in software (by the operating system to hide disk and network
latency). Further, the structure and organization of processor caches requires special care by
the operating system in setting up page tables; otherwise, much of the advantage of processor
caches can evaporate.
Regardless of the context, all caches face three design challenges:
```

#### Chunk 5

- Chunk ID: `08d3514f57b7c6c8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `38`
- Score: `-1.22432 rerank_score`

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

- Retrieval latency: 0.335s
- Generation latency: 9.206s

**Answer:**

Because cache performance depends less on the **total amount of data** and more on **which data is reused, when, and in what order**.

Caches speed things up only when they can predictably give you **cache hits**. That usually relies on:

1. **Temporal locality**  
   You access the same data again soon.

   ```text
   use A
   use A again soon  → likely still in cache
   ```

2. **Spatial locality**  
   You access nearby data.

   ```text
   use array[i]
   then array[i+1], array[i+2], ...
   ```

   Since caches load blocks of nearby memory, sequential access is usually fast.

Some access patterns perform badly because they do not reuse cached data effectively.

For example:

```text
Good pattern:
A B C D A B C D A B C D
```

If `A B C D` fit in cache, later accesses are fast.

But:

```text
Bad pattern:
A B C D E F G H A B C D E F G H
```

If the cache is too small to hold all of them, by the time you come back to `A`, it may have already been evicted.

So even if both programs use the same total amount of data, one may have many cache hits while the other has many cache misses.

In short:

> Caches help when the working data is reused before it gets evicted.  
> Bad access patterns defeat this by spreading accesses out, jumping around, or touching more data than the cache can effectively hold.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `00f14a9c68f65e10`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `76`
- Score: `0.639239 vector_distance`

```text
frequently accessed web pages to speed web access and reduce network traffic. Web access
patterns cause two challenges to a cache designer:
New data. New pages are being added to the web at a rapid rate, and page contents also
change. Every time a user accesses a page, the system needs to check whether the page
has changed in the meantime.
No working set. Although some web pages are much more popu lar than others, there is
no small subset of web pages that, if cached, give you the bulk of the benefit. Unlike
with a working set, even very small caches have some value. Conversely, increasing
cache size yields diminishing returns: even very large caches tend to have only modest
cache hit rates, as there are an enormous group of pages that are visited from time to
time.
```

#### Chunk 2

- Chunk ID: `6bf74655cc253b64`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `87`
- Score: `0.718134 vector_distance`

```text
system performance. Likewise, if a cached item is expensive to regenerate, it is more important to keep cached than one that
is more easily replaced.
Parallel computing makes the calculus even more complex. The performance of a parallel program depends on its critical
path — the minimum sequence of steps for the program to produce its result. Cache misses that occur on the critical path
affect the response time while those that occur off the critical path do not. For example, a parallel MapReduce job forks a
set of tasks onto processors; each task reads in a file and produces an output. Because MapReduce must wait until all tasks
are complete before moving onto the next step, if any file is not cached it is as bad as if all of the needed files were not
cached.
9.5.6 Belady’s Anomaly
```

#### Chunk 3

- Chunk ID: `7c345f7cb5372cc1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `66`
- Score: `0.772674 vector_distance`

```text
memory of frequently used directories and files, reducing the need for disk accesses.
Conditional branch prediction. Another use of caches is in predicting whether a
conditional branch will be taken or not. In the common case of a correct prediction, the
processor can start decoding the next instruction before the result of the branch is known
for sure; if the prediction turns out to be wrong, the decoding is restarted with the
correct next instruction.
In other words, caches are a central design technique to making computer systems faster.
However, caches are not without their dow nsides. Caches can make understanding the
performance of a system much harder. Something that seems like it should be fast — a nd even
```

#### Chunk 4

- Chunk ID: `071dd5814f2a3c15`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `69`
- Score: `0.773315 vector_distance`

```text
referenced at nearly the same time. To exploit this, caches are often designed to load a block
of data at the same time, instead of only a single location. Hardware memory caches often
store 4-64 m emory words as a unit; file caches often store data in pow ers of two of the
hardware page size.
A related design technique that also takes advantage of spatial locality is to prefetch data into
the cache before it is needed. For example, if the file system observes the application reading
a sequence of blocks into memory, it will read the subsequent blocks ahead of time, without
waiting to be asked.
Putting these together, the latency of a read request is as follows:
Latency(read request)   =   Prob(cache hit) × Latency(cache hit)
     + Prob(cache miss) × Latency(cache miss)
```

#### Chunk 5

- Chunk ID: `8a63d280ecef57e0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `69`
- Score: `0.77986 vector_distance`

```text
Second, the likelihood of  a cache hit must be high enough to make it worth the effort. One
source of predictability is temporal locality: programs tend to reference the same
instructions and data that they had recently accessed. Examples include the instructions inside
a loop, or  a data structure that is repeatedly accessed. By caching these memory values, we
can improve performance.
Another source of predictability is spatial locality. Programs tend to reference data near
other data that has been recently referenced. For example, the next instruction to execute is
usually near to the previous one, and different fields in the same data structure tend to be
referenced at nearly the same time. To exploit this, caches are often designed to load a block
```

## q41

**Question:** Why can a program’s working set matter more for performance than its total size?

### Method A

- Retrieval latency: 0.696s
- Generation latency: 6.566s

**Answer:**

A program’s **working set** matters more than its total size because performance depends mainly on the data/code the program is **actively using right now**, not everything it contains.

If the working set fits in a fast level of memory, such as cache or RAM, most accesses are fast:

- working set fits in cache → many cache hits → fast execution
- working set fits in RAM but not cache → slower, but still reasonable
- working set does not fit in RAM → frequent paging/swapping → very slow, possibly thrashing

The program’s **total size** may be large, but much of it might not be used during the current phase of execution. For example, a compiler may use parser data during parsing and code-generation data later. Each phase has a different working set.

So a large program with a small active working set can run well, while a smaller program whose active working set does not fit in memory can perform badly.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d40938611c1d5ae8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `74`
- Score: `1.27733 rerank_score`

```text
literally make the disk drive shake violently, making it very obvious to everyone nearby why the system was not performing
well.
The notion of a working set can also apply to user behavior. Consider what happens when
you are developing code for a homework assignment. If the files you need fit in memory,
compilation will be rapid; if not, compilation will be slow as each file is brought in from
disk as it is used.
Different programs, and different users, will have working sets of different sizes. Even within
the same program, different phases of the program may have different size working sets. For
example, the parser for a compiler needs different data in cache than the code generator. In a
text editor, the working set shifts when we switch from one page to the next. Users also
```

#### Chunk 2

- Chunk ID: `1054ce9a1d7a3485`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `99`
- Score: `1.13742 rerank_score`

```text
working set takes up 2/3rds of memory and the other takes up 1/3rd. If they coope rate, both
can run efficiently because the system has room for both working sets. However, if we need
to bulletproof the operating system against malicious programs by self-paging, then each will
be assigned half of memory and the larger program will thrash.
9.7.2 Swapping
Another issue is what happens as we increase the workload for a system with virtual memory.
If we are running a data center, for example, we can share physical machines among a much
larger number of applications each running in a separate virtual machine. To reduce costs, the
data center needs to support the maximum number of applications on each server, within some
performance constraint.
```

#### Chunk 3

- Chunk ID: `00f3ecc920b1afdc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `73`
- Score: `0.45885 rerank_score`

```text
of the hash table, each time we do a  lookup, the hash bucket we need will no longer be in the
cache.
Most programs will have an inflection point, or knee of the curve, where a critical mass of
program data can just barely fit in the cache. This critical mass is called the program’s
working set. As long as the working set can fit in the cache, most references will be a cache
hit, and application performance will be good.
```

#### Chunk 4

- Chunk ID: `97a950540e1310ae`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `75`
- Score: `-0.0723904 rerank_score`

```text
The result of this phas e change  behavior is that caches will often have bursty miss rates:
periods of low cache misses interspersed with periods of high cache misses, as shown in
Figure 9.5. Process context switches will also cause bursty cache misses, as the cache
discards the working set from the old process and brings in the working set of the new
process.
We can combine the graph in Figure 9.4 with the table in Figure 9.3 to see the impact of the
size of the working set on computer system performance. A program whose working set fits in
the first level cache will run four times faster than one whose working set fits in the second
level cache. A program whose working set does not fit in main memory will run a thousand
```

#### Chunk 5

- Chunk ID: `e5f2f3d26e232fd8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `123`
- Score: `-1.98895 rerank_score`

```text
models for managing sharing between regions of untrusted code.
Which pages should be evicted. Often, an application will have better information than
the operating system over which pages it will reference in the near future.
Many applications can adapt the size of their working set to the resources provided by the
kernel but they will have worse performance whenever there is a mismatch.
```

### Method B

- Retrieval latency: 0.189s
- Generation latency: 8.348s

**Answer:**

A program’s **working set** matters more than its total size because performance depends mainly on the data and code the program is actively using *right now*, not everything it contains.

The **working set** is the set of memory pages/cache blocks a program needs during a particular phase of execution.

- If the working set **fits in cache or main memory**, most accesses are fast.
- If the working set **does not fit**, the program keeps fetching data from slower levels like main memory or disk, causing many cache misses or page faults.
- This can make the program dramatically slower, even if the total program size is not huge.

For example, a compiler may have different phases: parsing, optimization, and code generation. Each phase uses different data. The total compiler may be large, but at any moment it may only need one subset of its data. If that subset fits in memory, it runs efficiently.

So:

> Total size tells you how big the whole program is.  
> Working set tells you how much memory the program actually needs to run efficiently at a given time.

That is why a large program with a small working set can perform well, while a smaller program with a working set too large for memory can perform poorly or even thrash.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d40938611c1d5ae8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `74`
- Score: `0.736731 vector_distance`

```text
literally make the disk drive shake violently, making it very obvious to everyone nearby why the system was not performing
well.
The notion of a working set can also apply to user behavior. Consider what happens when
you are developing code for a homework assignment. If the files you need fit in memory,
compilation will be rapid; if not, compilation will be slow as each file is brought in from
disk as it is used.
Different programs, and different users, will have working sets of different sizes. Even within
the same program, different phases of the program may have different size working sets. For
example, the parser for a compiler needs different data in cache than the code generator. In a
text editor, the working set shifts when we switch from one page to the next. Users also
```

#### Chunk 2

- Chunk ID: `1054ce9a1d7a3485`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `99`
- Score: `0.757751 vector_distance`

```text
working set takes up 2/3rds of memory and the other takes up 1/3rd. If they coope rate, both
can run efficiently because the system has room for both working sets. However, if we need
to bulletproof the operating system against malicious programs by self-paging, then each will
be assigned half of memory and the larger program will thrash.
9.7.2 Swapping
Another issue is what happens as we increase the workload for a system with virtual memory.
If we are running a data center, for example, we can share physical machines among a much
larger number of applications each running in a separate virtual machine. To reduce costs, the
data center needs to support the maximum number of applications on each server, within some
performance constraint.
```

#### Chunk 3

- Chunk ID: `83c62e5df62f7e7b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `75`
- Score: `0.816218 vector_distance`

```text
level cache. A program whose working set does not fit in main memory will run a thousand
times slower than one who doe s, assuming it has access to data center memory. It will run a
hundred thousand times slower if it needs to go to disk.
Because of the increasing depth and complexity of the memory hierarchy, an important area of
work is the design of algorithms that adapt their working set to the memory hierarchy. One
focus has been on algorithms that manage the gap between main memory and disk, but the
same principles apply at other levels of the memory hierarchy.
Figure 9.6: Algorithm to sort a large array that does not fit into main memory, by breaking the problem into pieces that do fit
into memory.
```

#### Chunk 4

- Chunk ID: `98098a88cc18b1be`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `73`
- Score: `0.90272 vector_distance`

```text
Thus, neither the cache size nor the program behavior alone governs the effectiveness of
caching. Rather, the interaction between the two determines cache effectiveness.
Figure 9.4: Cache hit rate as a function of cache size for a million instruction run of a C compiler. The hit rate vs. cache
size graph has a similar shape for many programs. The knee of the curve is called the working set of the program.
9.3.1 Working Set Model
A useful graph to consider is the cache hit rate versus the size of the cache. We give an
example in Figure 9.4; of course, the precise shape of the graph will vary from program to
program.
Regardless of the program, a sufficiently large cache will have a high cache hit rate. In the
```

#### Chunk 5

- Chunk ID: `4751e5778c940dac`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `124`
- Score: `0.926082 vector_distance`

```text
exactly as much memory as the kernel is able to provide, and no more. If the runtime
heap is too small, the program must garbage collect, even though more page frames
available. If the heap is too large, the kernel will page parts of the heap to disk instead
of asking the application to pay the lower overhead of compacting its memory.
Databases. Databases and other data processing systems often manipulate huge data sets
that must be streamed from disk into memory. As we noted in Chapter 9, algorithms for
large data sets will be more efficient if they are customized to the amount of available
physical memory. If the operating system evicts a page that the database expects to be in
memory, these algorithms will run much more slowly.
```

### Method C

- Retrieval latency: 0.950s
- Generation latency: 5.976s

**Answer:**

A program’s **working set** matters more than its **total size** because performance depends mostly on the data/instructions the program is actively using *right now*, not everything it contains.

- If the current working set fits in cache or main memory, most accesses are fast → high cache hit rate.
- If the working set does **not** fit, the program keeps evicting and reloading needed data → many misses/page faults → much slower performance, possibly thrashing.

Example: a compiler may be large overall, but during parsing it mainly uses parser-related code and data. Later, during code generation, its working set changes. The whole compiler size is less important than whether the active phase’s working set fits in the available memory/cache.

So a huge program can run well if its active working set is small, while a smaller program can run poorly if its working set exceeds the memory/cache available.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `d40938611c1d5ae8`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `74`
- Score: `n/a `

```text
literally make the disk drive shake violently, making it very obvious to everyone nearby why the system was not performing
well.
The notion of a working set can also apply to user behavior. Consider what happens when
you are developing code for a homework assignment. If the files you need fit in memory,
compilation will be rapid; if not, compilation will be slow as each file is brought in from
disk as it is used.
Different programs, and different users, will have working sets of different sizes. Even within
the same program, different phases of the program may have different size working sets. For
example, the parser for a compiler needs different data in cache than the code generator. In a
text editor, the working set shifts when we switch from one page to the next. Users also
```

#### Chunk 2

- Chunk ID: `1054ce9a1d7a3485`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `99`
- Score: `n/a `

```text
working set takes up 2/3rds of memory and the other takes up 1/3rd. If they coope rate, both
can run efficiently because the system has room for both working sets. However, if we need
to bulletproof the operating system against malicious programs by self-paging, then each will
be assigned half of memory and the larger program will thrash.
9.7.2 Swapping
Another issue is what happens as we increase the workload for a system with virtual memory.
If we are running a data center, for example, we can share physical machines among a much
larger number of applications each running in a separate virtual machine. To reduce costs, the
data center needs to support the maximum number of applications on each server, within some
performance constraint.
```

#### Chunk 3

- Chunk ID: `83c62e5df62f7e7b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `75`
- Score: `n/a `

```text
level cache. A program whose working set does not fit in main memory will run a thousand
times slower than one who doe s, assuming it has access to data center memory. It will run a
hundred thousand times slower if it needs to go to disk.
Because of the increasing depth and complexity of the memory hierarchy, an important area of
work is the design of algorithms that adapt their working set to the memory hierarchy. One
focus has been on algorithms that manage the gap between main memory and disk, but the
same principles apply at other levels of the memory hierarchy.
Figure 9.6: Algorithm to sort a large array that does not fit into main memory, by breaking the problem into pieces that do fit
into memory.
```

#### Chunk 4

- Chunk ID: `98098a88cc18b1be`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `73`
- Score: `n/a `

```text
Thus, neither the cache size nor the program behavior alone governs the effectiveness of
caching. Rather, the interaction between the two determines cache effectiveness.
Figure 9.4: Cache hit rate as a function of cache size for a million instruction run of a C compiler. The hit rate vs. cache
size graph has a similar shape for many programs. The knee of the curve is called the working set of the program.
9.3.1 Working Set Model
A useful graph to consider is the cache hit rate versus the size of the cache. We give an
example in Figure 9.4; of course, the precise shape of the graph will vary from program to
program.
Regardless of the program, a sufficiently large cache will have a high cache hit rate. In the
```

#### Chunk 5

- Chunk ID: `74a8b57c52f1cdb4`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `73`
- Score: `n/a `

```text
program.
Regardless of the program, a sufficiently large cache will have a high cache hit rate. In the
limit, if the cache can fit all of the program’s memory and data, the miss rate will be zero
once the data is loaded into the cache. At the other extreme, a sufficiently small cache will
have a very low cache hit rate. Anything other than a trivial program will have multiple
procedures and multiple data structures; if the cache is sufficiently small, each new
instruction and data reference will push out something from the cache that will be used in the
near future. For the hash table example, if the size of the cache is much smaller than the size
of the hash table, each time we do a  lookup, the hash bucket we need will no longer be in the
cache.
```

## q42

**Question:** If LRU sounds smarter than FIFO, why don’t systems always implement perfect LRU?

### Method A

- Retrieval latency: 0.656s
- Generation latency: 8.173s

**Answer:**

Because “perfect LRU” is expensive to implement and not always the best policy.

Main reasons:

1. **Every access must update metadata**  
   Perfect LRU needs to know the exact order of all cached pages/blocks by recency.  
   That means on every memory or cache access, the system must update timestamps, counters, or a linked list.

2. **That overhead can be too high**  
   For hardware caches or OS page replacement, accesses happen extremely often. Maintaining exact LRU can cost extra time, memory, and complexity.

3. **Approximate LRU is often good enough**  
   Systems often use cheaper approximations, such as reference bits, clock algorithms, or aging. These capture the main idea of LRU without tracking the exact order.

4. **LRU is not always better**  
   LRU performs well when there is temporal locality: recently used items are likely to be used again soon. But for repeated scans through data larger than the cache, LRU can perform badly, sometimes like FIFO, causing misses on nearly every reference.

So systems do not always implement perfect LRU because the extra accuracy may not justify the cost, and in some workloads LRU is not actually the ideal choice.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `2c58cc3f500e268a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `87`
- Score: `n/a `

```text
Many systems meld the two approaches to gain the benefits of each. LRU is better at keeping
the current working set in memory; once the working set is taken care of, however, LRU will
yield diminishing returns. Instead, LFU may be better at predicting what files or memory
blocks will be needed in the more distant future, e.g., after the next working set phase change.
Replacement policy and file size
Our discussion up to now has assumed that all cached items are equal, both in size and in cost to replace. When these
assumptions do not hold, however, we may sometimes want to vary the policy from LFU or LFU, that is, to keep some items
that are less frequently or less recently used ahead of others that are more frequently or more recently used.
```

#### Chunk 2

- Chunk ID: `78ed921f818a7e31`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `n/a `

```text
reference pattern that exhibits a high degree of temporal locality; when recent references are
more likely to be referenced in the near future, LRU can outperform FIFO.
LRU
Ref.  A  B  C  D  E  A  B  C  D  E  A  B  C  D  E
1  A     E     D     C  
2   B     A     E     D 
3    C     B     A     E
4     D     C     B   
MIN
1  A      +      +    + 
2   B      +      +  C  
3    C      +  D      + 
4     D  E      +      +
Figure 9.15: Cache behavior for LRU (top) and MIN (bottom) for a reference pattern that repeatedly scans through
memory. Each row represents the contents of a page frame or cache block; + indicates a cache hit. On this reference
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
```

#### Chunk 3

- Chunk ID: `7676a90b38eb5e64`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `84`
- Score: `n/a `

```text
Unfortunately, FIFO can be the worst possible replacement policy for workloads that happen
quite often in practice. Consider a program that cycles through a memory array repeatedly, but
where the array is too large to fit in the cache. Many scientific applications do a n operation
on every element in an array, and then repeat that operation until the data reaches a fixed
point. Google’s PageRank algorithm for determining which search results to display uses a
similar approach. PageRank iterates repeatedly through all pages, estimating the popu larity of
a page based on the popu larity of the pages that refer to it as computed in the previous
iteration.
FIFO
Ref.  A  B  C  D  E  A  B  C  D  E  A  B  C  D  E
1  A     E     D     C  
2   B     A     E     D 
3    C     B     A     E
```

#### Chunk 4

- Chunk ID: `269323bfeaeb0633`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `88`
- Score: `n/a `

```text
have a cache of size k + 1 blocks, we will keep all of the same blocks as with a k sized
cache, plus the additional block that will be the k + 1 next reference.
We can make a similar argument for LRU and LFU. For LRU, a cache of size k + 1 keeps all
of the same blocks as a k sized cache, plus the block that is referenced farthest in the past.
Even if LRU is a lousy replacement policy — if it rarely keeps the blocks that will be used in
the near future — it will always do a t least as well as a slightly smaller cache also using the
same replacement policy. An equivalent argument can be used for LFU.
FIFO (3 slots)
Ref.  A  B  C  D  A  B  E  A  B  C  D  E
1  A    D    E      +
2   B    A    +   C  
3    C    B    +   D 
FIFO (4 slots)
1  A     +   E     D 
2   B     +   A     E
```

#### Chunk 5

- Chunk ID: `1bc5bedc4acb6cc3`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `n/a `

```text
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
used page, as that will be referenced farthest into the future.
On this particular sequence of references, LRU behaves similarly to the optimal strategy
MIN, but that will not always be the case. In fact, LRU can sometimes be the worst possible
cache replacement policy. This occurs whenever the least recently used block is the next one
to be referenced. A common situation where LRU is pessimal is when the program makes
```

### Method B

- Retrieval latency: 0.462s
- Generation latency: 6.595s

**Answer:**

Because **perfect LRU is expensive to implement**, and it is not always worth the cost.

LRU requires the system to know the exact recency order of all cached pages/blocks. That means:

- On **every access**, even a cache hit, the system must update LRU information.
- In software, this might mean moving an item to the front of a list.
- In hardware caches, doing that at high speed is too complex and costly.
- It needs extra metadata and update logic, which can slow the cache down.

Also, **LRU is not always the best policy**. It works well when programs have **temporal locality** — recently used data is likely to be used again soon. But for patterns like scanning through a large array once, LRU can behave badly, sometimes like FIFO, causing many misses.

So real systems often use **approximations of LRU**, such as clock/second-chance algorithms, because they are cheaper and usually good enough.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1bc5bedc4acb6cc3`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `2.04174 rerank_score`

```text
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
used page, as that will be referenced farthest into the future.
On this particular sequence of references, LRU behaves similarly to the optimal strategy
MIN, but that will not always be the case. In fact, LRU can sometimes be the worst possible
cache replacement policy. This occurs whenever the least recently used block is the next one
to be referenced. A common situation where LRU is pessimal is when the program makes
```

#### Chunk 2

- Chunk ID: `269323bfeaeb0633`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `88`
- Score: `0.230065 rerank_score`

```text
have a cache of size k + 1 blocks, we will keep all of the same blocks as with a k sized
cache, plus the additional block that will be the k + 1 next reference.
We can make a similar argument for LRU and LFU. For LRU, a cache of size k + 1 keeps all
of the same blocks as a k sized cache, plus the block that is referenced farthest in the past.
Even if LRU is a lousy replacement policy — if it rarely keeps the blocks that will be used in
the near future — it will always do a t least as well as a slightly smaller cache also using the
same replacement policy. An equivalent argument can be used for LFU.
FIFO (3 slots)
Ref.  A  B  C  D  A  B  E  A  B  C  D  E
1  A    D    E      +
2   B    A    +   C  
3    C    B    +   D 
FIFO (4 slots)
1  A     +   E     D 
2   B     +   A     E
```

#### Chunk 3

- Chunk ID: `78ed921f818a7e31`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `-1.3595 rerank_score`

```text
reference pattern that exhibits a high degree of temporal locality; when recent references are
more likely to be referenced in the near future, LRU can outperform FIFO.
LRU
Ref.  A  B  C  D  E  A  B  C  D  E  A  B  C  D  E
1  A     E     D     C  
2   B     A     E     D 
3    C     B     A     E
4     D     C     B   
MIN
1  A      +      +    + 
2   B      +      +  C  
3    C      +  D      + 
4     D  E      +      +
Figure 9.15: Cache behavior for LRU (top) and MIN (bottom) for a reference pattern that repeatedly scans through
memory. Each row represents the contents of a page frame or cache block; + indicates a cache hit. On this reference
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
```

#### Chunk 4

- Chunk ID: `2c58cc3f500e268a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `87`
- Score: `-2.46414 rerank_score`

```text
Many systems meld the two approaches to gain the benefits of each. LRU is better at keeping
the current working set in memory; once the working set is taken care of, however, LRU will
yield diminishing returns. Instead, LFU may be better at predicting what files or memory
blocks will be needed in the more distant future, e.g., after the next working set phase change.
Replacement policy and file size
Our discussion up to now has assumed that all cached items are equal, both in size and in cost to replace. When these
assumptions do not hold, however, we may sometimes want to vary the policy from LFU or LFU, that is, to keep some items
that are less frequently or less recently used ahead of others that are more frequently or more recently used.
```

#### Chunk 5

- Chunk ID: `92ccda3d0eb7cdc4`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `85`
- Score: `-2.60676 rerank_score`

```text
data in memory and never have a cache miss.
9.5.4 Least Recently Used (LRU)
One way to predict the future is to look at the past. If programs exhibit temporal locality, the
locations they reference in the future are likely to be the same as the ones they have
referenced in the recent past.
A replacement policy that captures this effect is to evict the block that has not been used for
the longest period of  time, or the least recently used (LRU) block. In software, LRU is simple
to implement: on every cache hit, you move the block to the front of the list, and on a cache
miss, you evict the block at the end of the list. In hardware, keeping a linked list of cached
blocks is too complex to implement at high speed; instead, we need to approximate LRU, and
```

### Method C

- Retrieval latency: 0.224s
- Generation latency: 7.460s

**Answer:**

Because **perfect LRU is expensive to implement**, and it is not always much better.

To do *true* LRU, the system must know the exact order in which every page/cache block was last used. That means on **every memory reference** it would need to update some data structure or timestamp. For real systems with huge numbers of memory accesses, that overhead is too high.

So systems usually use **approximations** of LRU, such as reference bits, clock/second-chance algorithms, or aging counters. These capture “recently used enough” without tracking the exact order.

Also, LRU is not always optimal. For example, if a program repeatedly scans through data larger than the cache, LRU can behave like FIFO and miss on every reference. In that case, “least recently used” may actually be the next thing needed only after the whole scan repeats.

So the short answer is:

**LRU is smarter in many common cases, but perfect LRU costs too much to maintain, and it can still perform badly on some access patterns.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `1bc5bedc4acb6cc3`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `0.644808 vector_distance`

```text
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
used page, as that will be referenced farthest into the future.
On this particular sequence of references, LRU behaves similarly to the optimal strategy
MIN, but that will not always be the case. In fact, LRU can sometimes be the worst possible
cache replacement policy. This occurs whenever the least recently used block is the next one
to be referenced. A common situation where LRU is pessimal is when the program makes
```

#### Chunk 2

- Chunk ID: `2c58cc3f500e268a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `87`
- Score: `0.6995 vector_distance`

```text
Many systems meld the two approaches to gain the benefits of each. LRU is better at keeping
the current working set in memory; once the working set is taken care of, however, LRU will
yield diminishing returns. Instead, LFU may be better at predicting what files or memory
blocks will be needed in the more distant future, e.g., after the next working set phase change.
Replacement policy and file size
Our discussion up to now has assumed that all cached items are equal, both in size and in cost to replace. When these
assumptions do not hold, however, we may sometimes want to vary the policy from LFU or LFU, that is, to keep some items
that are less frequently or less recently used ahead of others that are more frequently or more recently used.
```

#### Chunk 3

- Chunk ID: `78ed921f818a7e31`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `86`
- Score: `0.828389 vector_distance`

```text
reference pattern that exhibits a high degree of temporal locality; when recent references are
more likely to be referenced in the near future, LRU can outperform FIFO.
LRU
Ref.  A  B  C  D  E  A  B  C  D  E  A  B  C  D  E
1  A     E     D     C  
2   B     A     E     D 
3    C     B     A     E
4     D     C     B   
MIN
1  A      +      +    + 
2   B      +      +  C  
3    C      +  D      + 
4     D  E      +      +
Figure 9.15: Cache behavior for LRU (top) and MIN (bottom) for a reference pattern that repeatedly scans through
memory. Each row represents the contents of a page frame or cache block; + indicates a cache hit. On this reference
pattern, LRU is the same as FIFO, with a cache miss on every reference; the optimal strategy is to replace the most recently
```

#### Chunk 4

- Chunk ID: `269323bfeaeb0633`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `88`
- Score: `0.841834 vector_distance`

```text
have a cache of size k + 1 blocks, we will keep all of the same blocks as with a k sized
cache, plus the additional block that will be the k + 1 next reference.
We can make a similar argument for LRU and LFU. For LRU, a cache of size k + 1 keeps all
of the same blocks as a k sized cache, plus the block that is referenced farthest in the past.
Even if LRU is a lousy replacement policy — if it rarely keeps the blocks that will be used in
the near future — it will always do a t least as well as a slightly smaller cache also using the
same replacement policy. An equivalent argument can be used for LFU.
FIFO (3 slots)
Ref.  A  B  C  D  A  B  E  A  B  C  D  E
1  A    D    E      +
2   B    A    +   C  
3    C    B    +   D 
FIFO (4 slots)
1  A     +   E     D 
2   B     +   A     E
```

#### Chunk 5

- Chunk ID: `7676a90b38eb5e64`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `84`
- Score: `0.869333 vector_distance`

```text
Unfortunately, FIFO can be the worst possible replacement policy for workloads that happen
quite often in practice. Consider a program that cycles through a memory array repeatedly, but
where the array is too large to fit in the cache. Many scientific applications do a n operation
on every element in an array, and then repeat that operation until the data reaches a fixed
point. Google’s PageRank algorithm for determining which search results to display uses a
similar approach. PageRank iterates repeatedly through all pages, estimating the popu larity of
a page based on the popu larity of the pages that refer to it as computed in the previous
iteration.
FIFO
Ref.  A  B  C  D  E  A  B  C  D  E  A  B  C  D  E
1  A     E     D     C  
2   B     A     E     D 
3    C     B     A     E
```

## q43

**Question:** How can adding more page frames ever make a paging policy perform worse?

### Method A

- Retrieval latency: 0.933s
- Generation latency: 8.520s

**Answer:**

Adding more page frames can make a paging policy perform worse if the policy is **not a stack algorithm**.

The classic example is **FIFO page replacement**.

FIFO evicts the page that has been in memory the longest, regardless of whether it is about to be used again. With more frames, pages stay in memory longer, which can change the eviction order in a bad way. A page that would have been evicted earlier with fewer frames might now remain, causing a more useful page to be evicted instead.

This surprising effect is called **Belady’s anomaly**.

Example idea:

- With 3 frames, FIFO might accidentally evict pages in a helpful order.
- With 4 frames, the changed queue order may cause more future-needed pages to be removed.
- So the number of page faults can increase even though memory increased.

This cannot happen with policies like **LRU** or **optimal replacement**, because they have the **stack property**: the pages kept with `n` frames are always a subset of the pages kept with `n+1` frames. Therefore, adding frames cannot make them worse.

So the short answer is:

> More frames can make performance worse when the replacement policy’s decisions change in a way that evicts more useful pages. FIFO is the standard example.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `n/a `

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

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

#### Chunk 3

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `n/a `

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 4

- Chunk ID: `3cad8530570e0f08`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `96`
- Score: `n/a `

```text
Each sweep of the clock algorithm through memory collects one bit of information about page
usage; by adjusting the frequency of the clock algorithm, we can collect increasingly fine-
grained information about usage, at the cost of increased software overhead. On modern
systems with hundreds of thousands and sometimes millions of physical page frames, the
overhead of the clock algorithm can be substantial.
The policy for what to do w ith the usage information is up to the operating system kernel. A
common policy is called not recently used, or k’th chance. If the operating system needs to
evict a page, the kernel picks one that has not been used (has not had its use bit set) for the
last k sweeps of the clock algorithm. The clock algorithm partitions pages based on how
```

#### Chunk 5

- Chunk ID: `aa35eaa9299f196a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `124`
- Score: `n/a `

```text
physical memory. If the operating system evicts a page that the database expects to be in
memory, these algorithms will run much more slowly.
Virtual machines. A similar issue arises with virtual machines. The guest operating
system running inside of a virtual machine thinks it has a set of physical page frames,
which it can assign to the virtual pages of applications running in the virtual machine. In
reality, however, the page frames in the guest operating system are virtual and can be
paged to disk by the host operating system. If the host operating system could tell the
guest operating system when it needed to steal a page frame (or donate a page frame),
then the guest would know exactly how many page frames were available to be
allocated to its applications.
```

### Method B

- Retrieval latency: 0.445s
- Generation latency: 7.898s

**Answer:**

Adding more page frames can make a paging policy perform worse when the policy does **not preserve the “useful” pages consistently** as memory size grows.

This is called **Belady’s anomaly**.

For example, with **FIFO page replacement**, the OS evicts the page that has been in memory the longest, regardless of whether it will be needed soon. If you give FIFO more frames, the order in which pages enter and leave memory can change. That can cause FIFO to keep some less useful pages longer and evict pages that will soon be reused.

So paradoxically:

> more frames → different eviction pattern → more page faults

This does **not** happen with all policies. Policies with the **stack property**, like **LRU** and **optimal replacement**, do not suffer from this anomaly. With those policies, the set of pages in memory with `n` frames is always a subset of the pages in memory with `n+1` frames, so adding frames cannot increase page faults.

In short:

- **FIFO** can perform worse with more frames.
- **LRU/optimal** cannot.
- The issue is not “more memory is bad,” but that some replacement policies behave badly when memory size changes.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `-0.0661749 rerank_score`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

#### Chunk 2

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `-0.147379 rerank_score`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 3

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `-0.618842 rerank_score`

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 4

- Chunk ID: `5bd5b4037b4bb72f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `82`
- Score: `-0.786083 rerank_score`

```text
KB (4 KB pages times the 8-way set associativity). This makes it a lot more likely for the
application to thrash.
Even worse, the application would have no way to know this had happened. If by random
chance an application ended up with page frames that map to the same cache buckets, its
performance will be poor . Then, when the user re-runs the application, the operating system
might assign the application a completely different set of page frames, and performance
returns to normal.
To make cache behavior more predictable and more effective, ope rating systems use a
concept called page  coloring. With page coloring, physical page frames are partitioned into
sets based on which cache buckets they will use. For example, with a 2 MB 8-way set
```

#### Chunk 5

- Chunk ID: `7782e63ed2f7e473`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `-0.930943 rerank_score`

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

### Method C

- Retrieval latency: 0.224s
- Generation latency: 7.682s

**Answer:**

Adding more page frames can make performance worse for some paging policies because the policy’s eviction choices can change in a bad way when the number of frames changes.

This is called **Belady’s anomaly**.

Example: with **FIFO page replacement**, the OS evicts the page that has been in memory the longest. But FIFO does **not** care whether that page is about to be used again soon.

So when you add more frames:

- pages stay in memory longer,
- the FIFO order changes,
- and the page evicted later may actually be more important than the one evicted with fewer frames.

That can lead to **more page faults**, not fewer.

A classic example reference string is:

```text
1 2 3 4 1 2 5 1 2 3 4 5
```

With FIFO:

- 3 frames → 9 page faults
- 4 frames → 10 page faults

So adding a frame makes FIFO worse.

However, this does **not** happen for all policies. Algorithms like **LRU** and **MIN/OPT** have the **stack property**: the pages in memory with `n` frames are always a subset of the pages in memory with `n+1` frames. Therefore, adding frames cannot increase page faults for those policies.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `97ea247740220923`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `0.866662 vector_distance`

```text
should a page frame be? A larger page frame can waste space if a process does not use all of
the memory inside the frame. This is called internal fragmentation. Fixed-size chunks are
easier to allocate, but waste space if the entire chunk is not used. Unfortunately, this means
that with paging, either pages are very large (wasting space due to internal fragmentation), or
the page table is very large (wasting space), or both. For example, with 16 K B pages and a
64 bi t virtual address space, we might need 250 page table entries!
8.2.3 Multi-Level Translation
If you were to design an efficient system for doing a lookup on a sparse keyspace, you
probably would not pick a simple array. A tree or a hash table are more appropriate, and
```

#### Chunk 2

- Chunk ID: `9c972abb12f7b6a0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `98`
- Score: `0.884006 vector_distance`

```text
frames, and beyond that any page faults it triggers would evict its own pages.
Unfortunately, self-paging comes at a cost in reduced resource utilization. Suppos e we have
two processes, both of which allocate large amounts of virtual address space. However, the
working sets of the two programs can fit in memory at the same time, for example, if one
```

#### Chunk 3

- Chunk ID: `bd4eddd0e9c2163b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `97`
- Score: `0.89397 vector_distance`

```text
add a few extra page faults to a system, no one will notice. However, a modern disk can
handle at most 100 pa ge faults per second, while a modern multi-core processor can execute
10 bi llion instructions per second. Thus, if page faults are anything but extremely rare,
performance will suffer.
9.7.1 Self-Paging
One consideration is that the behavior of one process can significantly hurt the performance
of other programs running at the same time. For example, suppos e we have two processes.
One is a normal program, with a working set equal to say, a quarter of physical memory. The
other program is greedy; while it can run fine with less memory, it will run faster if it is given
more memory. We gave an example of this earlier with the sort program.
```

#### Chunk 4

- Chunk ID: `5bd5b4037b4bb72f`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `82`
- Score: `0.973338 vector_distance`

```text
KB (4 KB pages times the 8-way set associativity). This makes it a lot more likely for the
application to thrash.
Even worse, the application would have no way to know this had happened. If by random
chance an application ended up with page frames that map to the same cache buckets, its
performance will be poor . Then, when the user re-runs the application, the operating system
might assign the application a completely different set of page frames, and performance
returns to normal.
To make cache behavior more predictable and more effective, ope rating systems use a
concept called page  coloring. With page coloring, physical page frames are partitioned into
sets based on which cache buckets they will use. For example, with a 2 MB 8-way set
```

#### Chunk 5

- Chunk ID: `c07f743f8f26373b`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `101`
- Score: `0.973422 vector_distance`

```text
cache (on the same reference pattern).
b. Adding a cache never hurts performance.
4. Suppos e an application is assigned 4 pa ges of physical memory and the memory is
initially empty. It then references pages in the following sequence:
      ACBDBAEFBFAGEFA
a. Show how the system would fault pages into the four frames of physical memory,
using the LRU replacement policy.
b. Show how the system would fault pages into the four frames of physical memory,
using the MIN replacement policy.
c. Show how the system would fault pages into the four frames of physical memory,
using the clock replacement policy.
5. Is least recently used a good c ache replacement algorithm to use for a workload
following a zipf distribution? Briefly explain why or why not.
```

## q44

**Question:** If memory-mapped files let a file be accessed like memory, does that mean file I/O and memory access become the same thing?

### Method A

- Retrieval latency: 0.226s
- Generation latency: 8.832s

**Answer:**

Not exactly.

A **memory-mapped file** makes file access *look like* memory access to the program, but file I/O and ordinary memory access are still different underneath.

With `mmap()`:

```c
char *p = mmap(...);
x = p[100];      // looks like a normal memory load
p[200] = 'A';    // looks like a normal memory store
```

From the program’s point of view, you use pointers instead of `read()` / `write()`.

But internally:

- If the needed file page is not in RAM, the access causes a **page fault**.
- The OS loads the relevant part of the file from disk into memory.
- Later, modified pages may be written back to disk.
- This is still file I/O, just handled automatically by the OS.

So the key idea is:

> **The interface becomes memory-like, but the underlying behavior is still file-backed and managed by the OS.**

Ordinary memory access is usually just accessing RAM.  
Memory-mapped file access may be RAM access *if the page is already loaded*, or it may trigger disk I/O if not.

So they become similar from the programmer’s perspective, but not identical in performance or behavior.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ddd96f2907916a71`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `30`
- Score: `0.713227 vector_distance`

```text
file.
Rather than using read() and write() to access a file’s data, an application can use mmap() to
establish a mapping between a region of the process’s virtual memory and some region of the
file. Once a file has been mapped, memory loads and stores to that virtual memory region
will read and write the file’s data either by accessing a shared page from the kernel’s file
```

#### Chunk 2

- Chunk ID: `9f53c4a52636c233`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `0.726976 vector_distance`

```text
done entirely by the operating system.
9.6.1 Advantages
Memory-mapped files offer a number of advantages:
Transparency. The program can operate on the bytes in the file as if they are part of
memory; specifically, the program can use a pointer into the file without needing to
check if that portion of the file is in memory or not.
```

#### Chunk 3

- Chunk ID: `54737445a9bce14e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `0.73739 vector_distance`

```text
entries are set to invalid — i f the process accesses a page that has not reached memory yet,
the hardware traps to the operating system and then waits until the page is available so it can
continue to execute. From the program’s perspective, there is no difference (except for
performance) between whether the executable image is entirely in memory or still mostly on
disk.
We can generalize this concept to any file stored on disk, allowing applications to treat any
file as part of its virtual address space. File blocks are brought in by the operating system
when they are referenced, and modified blocks are copied back to disk, with the book keeping
done entirely by the operating system.
9.6.1 Advantages
Memory-mapped files offer a number of advantages:
```

#### Chunk 4

- Chunk ID: `8c8c36345e05e56e`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `37`
- Score: `0.746025 vector_distance`

```text
Memory mapped I/O
 
 MOV register, memAddr // To read 
 MOV memAddr, register // To write 
 
Port mapped I/O
 
 IN register, portAddr  // To read 
 OUT portAddr, register // To write 
 
Port mapped I/O can be useful in architectures with constrained physical memory addresses since I/O devices do not need to
consume ranges of physical memory addresses. On the other hand, for systems with sufficiently large physical address
spaces, memory-mapped I/O can be simpler since no new instructions or address ranges need to be defined and since device
drivers can use any standard memory access instructions to access devices. Also, memory-mapped I/O provides a more
unified model for supporting DMA — direct transfers between I/O devices and main memory.
```

#### Chunk 5

- Chunk ID: `dc5d9c4a13be9e5d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `0.765882 vector_distance`

```text
memory. With multiple threads, a program can use explicit read/write calls to pipeline
disk I/O, but it needs to manage the pipeline itself.
Interprocess communication. Two or more processes can share information
instantaneously through a memory-mapped file without needing to shuffle data back and
forth to the kernel or to disk. If the hardware architecture supports it, the page table for
the shared segment can also be shared.
Large files. As long as the page table for the file can fit in physical memory, the only
limit on the size of a memory-mapped file is the size of the virtual address space. For
example, an application may have a giant multi-level tree indexing data spread across a
number of disks in a data center. With read/write system calls, the application needs to
```

### Method B

- Retrieval latency: 1.006s
- Generation latency: 8.866s

**Answer:**

Not exactly.

With a **memory-mapped file**, the program can *treat* file contents like memory:

```c
ptr[i] = 'A';
x = ptr[j];
```

So from the program’s point of view, file access looks like ordinary loads and stores.

But internally, **file I/O and memory access are still different**.

### What becomes similar?
The programming interface changes:

- Instead of calling `read()` / `write()`,
- the program accesses bytes through pointers.

The OS gives the illusion that the file is part of the process’s virtual address space.

### What is still different?
If the accessed part of the file is not currently in RAM:

1. the memory access causes a **page fault**,
2. the OS loads the needed file block/page from disk,
3. execution continues.

So a simple-looking memory load may secretly trigger disk I/O, which is much slower than normal RAM access.

### Key distinction

| Normal memory access | Memory-mapped file access |
|---|---|
| Accesses RAM-backed memory | Accesses file-backed virtual memory |
| Usually volatile | Changes may be written back to disk |
| No file involved | OS maps file pages into memory |
| Fast if page is resident | May cause disk I/O on page fault |

So the best way to say it is:

> Memory-mapped files make **file I/O look like memory access to the program**, but the operating system still manages the difference between RAM and disk underneath.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `dc5d9c4a13be9e5d`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `n/a `

```text
memory. With multiple threads, a program can use explicit read/write calls to pipeline
disk I/O, but it needs to manage the pipeline itself.
Interprocess communication. Two or more processes can share information
instantaneously through a memory-mapped file without needing to shuffle data back and
forth to the kernel or to disk. If the hardware architecture supports it, the page table for
the shared segment can also be shared.
Large files. As long as the page table for the file can fit in physical memory, the only
limit on the size of a memory-mapped file is the size of the virtual address space. For
example, an application may have a giant multi-level tree indexing data spread across a
number of disks in a data center. With read/write system calls, the application needs to
```

#### Chunk 2

- Chunk ID: `9f53c4a52636c233`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `n/a `

```text
done entirely by the operating system.
9.6.1 Advantages
Memory-mapped files offer a number of advantages:
Transparency. The program can operate on the bytes in the file as if they are part of
memory; specifically, the program can use a pointer into the file without needing to
check if that portion of the file is in memory or not.
```

#### Chunk 3

- Chunk ID: `d8eb76ef9cb21b77`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `n/a `

```text
number of disks in a data center. With read/write system calls, the application needs to
explicitly manage which parts of the tree are kept in memory and which are on disk;
alternatively, with memory-mapped files, the application can leave that book keeping to
the operating system.
9.6.2 Implementation
To implement memory-mapped files, the operating system provides a system call to map the
file into a portion of the virtual address space. In the system call, the kernel initializes a set of
page table entries for that region of the virtual address space, setting each entry to invalid.
The kernel then returns to the user process.
```

#### Chunk 4

- Chunk ID: `54737445a9bce14e`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `n/a `

```text
entries are set to invalid — i f the process accesses a page that has not reached memory yet,
the hardware traps to the operating system and then waits until the page is available so it can
continue to execute. From the program’s perspective, there is no difference (except for
performance) between whether the executable image is entirely in memory or still mostly on
disk.
We can generalize this concept to any file stored on disk, allowing applications to treat any
file as part of its virtual address space. File blocks are brought in by the operating system
when they are referenced, and modified blocks are copied back to disk, with the book keeping
done entirely by the operating system.
9.6.1 Advantages
Memory-mapped files offer a number of advantages:
```

#### Chunk 5

- Chunk ID: `aab3b7f3e6de64f1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `n/a `

```text
without affecting the underlying file. For example, it can convert the file from the disk format
into a more convenient in-memory format. To write changes back to the file, the program
invokes the system call write to copy the data from the program buffers out to disk. Reading
and writing files via system calls is simple to understand and reasonably efficient for small
files.
An alternative model for file I/O is to map the file contents into the program’s virtual address
space. For a memory-mappe d file, the operating system provides the illusion that the file is a
program segment; like any memory segment, the program can directly issue instructions to
load and store values to the memory. Unlike file read/write, the load and store instructions do
```

### Method C

- Retrieval latency: 0.488s
- Generation latency: 8.038s

**Answer:**

Not exactly. **They become similar from the program’s point of view**, but they are not the same underneath.

With a **memory-mapped file**, the OS maps part of a file into the process’s virtual address space. Then the program can do things like:

```c
char c = mapped_region[10];
mapped_region[20] = 'A';
```

instead of calling:

```c
read(fd, buffer, size);
write(fd, buffer, size);
```

So at the **programming interface level**, file access looks like memory access.

But internally, important differences remain:

- **Normal memory access** usually goes to RAM.
- **Memory-mapped file access** may cause a page fault if that part of the file is not currently in RAM.
- The OS may then load the needed file page from disk.
- Writes may not immediately go to disk; the OS can mark the page dirty and write it back later.
- The mapped region is backed by a file, so its contents may persist after the process exits.

So the best way to say it is:

> Memory-mapped files make file I/O look like memory access to the program, but the OS still manages disk I/O behind the scenes.

They are unified in the **virtual memory interface**, not identical in performance or behavior.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5f2b173f0f6f35a1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `3.63506 rerank_score`

```text
Copy-on-write. Copy-on-write allows multiple processes to have logically separate
copies of the same memory region, backed by a single physical copy in memory. Each
page in the region is mapped read-only in each process; the operating system makes a
physical copy only when (and if) a page is modified.
Memory-mapped files. Disk files can be made part of a process’s virtual address
space, allowing the process to access the data in the file using normal processor
instructions. When a page from a memory-mapped file is first accessed, a protection
fault traps to the operating system so that it can bring the page into memory from disk.
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
```

#### Chunk 2

- Chunk ID: `264727607d1c28c3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `36`
- Score: `3.42983 rerank_score`

```text
Port mapped I/O
Today, memory-mapped I/O is the dominant paradigm for accessing I/O device’s control registers. However an older style,
port mapped I/O, is still sometimes used. Notably, the x86 architecture supports both memory-mapped I/O and port mapped
I/O.
Port mapped I/O is similar to memory-mapped I/O in that instructions read from and write to specified addresses to control
I/O devices. There are two differences. First, where memory-mapped I/O uses standard memory-access instructions (e.g.,
load and store) to communicate with devices, port mapped I/O uses distinct I/O instructions. For example, the x86
architecture uses the in and out instructions for port mapped I/O. Second, whereas memory-mapped I/O uses the same
```

#### Chunk 3

- Chunk ID: `b1fd93a11946c9a1`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `36`
- Score: `2.88985 rerank_score`

```text
architecture uses the in and out instructions for port mapped I/O. Second, whereas memory-mapped I/O uses the same
physical address space as is used for the system’s main memory, the address space for port mapped I/O is distinct from the
main memory address space.
For example, in x86 I/O can be done using either memory-mapped or port mapped I/O, and the low-level assembly code is
similar for both cases:
```

#### Chunk 4

- Chunk ID: `9f53c4a52636c233`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `2.23062 rerank_score`

```text
done entirely by the operating system.
9.6.1 Advantages
Memory-mapped files offer a number of advantages:
Transparency. The program can operate on the bytes in the file as if they are part of
memory; specifically, the program can use a pointer into the file without needing to
check if that portion of the file is in memory or not.
```

#### Chunk 5

- Chunk ID: `48071e19ff2cbafc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `89`
- Score: `2.22286 rerank_score`

```text
blocks. When the application accesses a missing memory page, it is transparently brought in
from disk. We start with the simpler case of a demand paging for a single, memory-mapped
file and then extend the discussion to managing multiple processes competing for space in
main memory.
As we discussed in Chapter 3, m ost programs use explicit read/write system calls to perform
file I/O. Read/write system calls allow the program to work on a copy of file data. The
program opens a file and then invokes the system call read to copy chunks of file data into
buffers in the program’s address space. The program can then use and modify those chunks,
without affecting the underlying file. For example, it can convert the file from the disk format
```

## q45

**Question:** If zero-copy I/O avoids copying data, where does the data actually live while it is being moved?

### Method A

- Retrieval latency: 0.389s
- Generation latency: 8.139s

**Answer:**

In zero-copy I/O, the data still lives in **physical memory** somewhere — zero-copy just avoids making an extra **memory-to-memory copy** between kernel space and user space.

Typical case:

1. The disk or device transfers data into a physical memory page, often a **kernel buffer** or **page cache** page.
2. Instead of copying that data into a separate user-space buffer, the OS changes the process’s **page table entries** so the user program’s virtual address points to that same physical page.
3. The program accesses the data through its own virtual address space, but the actual bytes are still in the same physical memory page.

So conceptually:

```text
Without zero-copy:

disk -> kernel buffer -> copied to user buffer
```

With zero-copy:

```text
disk -> physical memory page
        ↑
   kernel maps this page into user space
```

The data may also briefly pass through hardware/device buffers, but the key point is:

> Zero-copy does not mean “the data is nowhere” or “not moved at all.”  
> It means the OS avoids an extra copy across the kernel-user boundary by sharing/remapping the same physical memory page.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5bfe841535996301`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `2.86675 rerank_score`

```text
Zero copy I/O. The operating system does not need to copy file data from kernel buffers
into user memory and back; rather, it just changes the program’s page table entry to poi nt
to the physical page frame containing that portion of the file. The kernel is responsible
for copying data back and forth to disk. We should note that it is possible to implement
zero copy I/O for explicit read/write file system calls in certain restricted cases; we
will explain how in the next chapter.
Pipelining. The program can start operating on the data in the file as soon as the page
tables have been set up; it does not need to wait for the entire file to be read into
memory. With multiple threads, a program can use explicit read/write calls to pipeline
disk I/O, but it needs to manage the pipeline itself.
```

#### Chunk 2

- Chunk ID: `3dd5527e74d532bb`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `109`
- Score: `1.69404 rerank_score`

```text
solution; it would not work if the application needed to do a ny work on the buffer as oppos ed
to only transferring it from one hardware device to another.
Instead, two solutions to zero-copy I/O are used in practice. Both eliminate the copy across
the kernel-user boundary for large blocks of data; for small chunks of data, the extra copy
does not hurt performance.
The more widely used approach manipulates the process page table to simulate a copy. For
this to work, the application must first align its user-level buffer to a page boundary. The
user-level buffer is provided to the kernel on a read or write system call, and its alignment
and size is up to the application.
```

#### Chunk 3

- Chunk ID: `7891ce4a1097f27a`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `167`
- Score: `-0.549744 rerank_score`

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

#### Chunk 4

- Chunk ID: `5ba709aed5255924`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `202`
- Score: `-0.549744 rerank_score`

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

#### Chunk 5

- Chunk ID: `8eb78a2bb6480834`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `168`
- Score: `-0.549744 rerank_score`

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

### Method B

- Retrieval latency: 0.336s
- Generation latency: 7.381s

**Answer:**

In zero-copy I/O, the data still lives in **physical memory pages** — the key point is that it is **not copied between a kernel buffer and a user buffer**.

Usually, one of these happens:

1. **Page-table remapping**
   - The data is in a physical page frame, often filled by the kernel/device.
   - Instead of copying that data into the process’s user-space buffer, the OS changes the process’s **page table** so the user virtual address points to that same physical page.

2. **Direct device transfer**
   - The hardware device may transfer data directly into the physical pages backing the user buffer.
   - When the I/O finishes, the data is already at the memory location the application expects.

So the data “lives” in **RAM**, in physical page frames. Zero-copy means avoiding the extra memory-to-memory copy across the **kernel-user boundary**, not that the data exists nowhere or never moves at all.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `3dd5527e74d532bb`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `109`
- Score: `0.708294 vector_distance`

```text
solution; it would not work if the application needed to do a ny work on the buffer as oppos ed
to only transferring it from one hardware device to another.
Instead, two solutions to zero-copy I/O are used in practice. Both eliminate the copy across
the kernel-user boundary for large blocks of data; for small chunks of data, the extra copy
does not hurt performance.
The more widely used approach manipulates the process page table to simulate a copy. For
this to work, the application must first align its user-level buffer to a page boundary. The
user-level buffer is provided to the kernel on a read or write system call, and its alignment
and size is up to the application.
```

#### Chunk 2

- Chunk ID: `5bfe841535996301`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `90`
- Score: `0.736907 vector_distance`

```text
Zero copy I/O. The operating system does not need to copy file data from kernel buffers
into user memory and back; rather, it just changes the program’s page table entry to poi nt
to the physical page frame containing that portion of the file. The kernel is responsible
for copying data back and forth to disk. We should note that it is possible to implement
zero copy I/O for explicit read/write file system calls in certain restricted cases; we
will explain how in the next chapter.
Pipelining. The program can start operating on the data in the file as soon as the page
tables have been set up; it does not need to wait for the entire file to be read into
memory. With multiple threads, a program can use explicit read/write calls to pipeline
disk I/O, but it needs to manage the pipeline itself.
```

#### Chunk 3

- Chunk ID: `07d37d4f68cfc154`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `110`
- Score: `0.817597 vector_distance`

```text
data appears exactly where it was expected! The kernel can reclaim any physical memory
behind the empty buffer.
More recently, some hardware I/O devices have been designed to be able to transfer data to
and from virtual addresses, rather than only to and from physical addresses. The kernel hands
the virtual address of the user-level buffer to the hardware device. The hardware device,
rather than the kernel, walks the multi-level page table to determine which physical page
frame to use for the device transfer. When the transfer completes, the data is automatically
where it belongs, with no extra work by the kernel. This procedure is a bit more complicated
for incoming network packets, as the decision as to which process should receive which
```

#### Chunk 4

- Chunk ID: `5ba709aed5255924`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `202`
- Score: `0.957601 vector_distance`

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

#### Chunk 5

- Chunk ID: `8eb78a2bb6480834`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `168`
- Score: `0.957601 vector_distance`

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

### Method C

- Retrieval latency: 0.779s
- Generation latency: 6.654s

**Answer:**

In zero-copy I/O, the data still lives in **physical memory** — it just is not copied from one memory buffer to another across the kernel/user boundary.

Usually one of these happens:

1. **Page table remapping**
   - The device or kernel puts the data into a **kernel buffer** in physical memory.
   - Instead of copying the bytes into the user process’s buffer, the OS changes the process’s **page table entry** so that the user virtual address now points to that same physical page.
   - So to the program, the data appears in its buffer, but really the mapping changed.

2. **Device writes directly into user memory**
   - Some hardware can transfer data directly to/from the physical pages behind a user-level buffer.
   - The kernel gives the device enough address/mapping information, and the device performs the transfer directly.
   - When the I/O finishes, the data is already in the user buffer’s memory pages.

So the short answer is:

> The data lives in physical memory pages; zero-copy avoids duplicating it by either remapping those pages into the process or letting the hardware transfer directly into the process’s pages.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `3dd5527e74d532bb`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `109`
- Score: `n/a `

```text
solution; it would not work if the application needed to do a ny work on the buffer as oppos ed
to only transferring it from one hardware device to another.
Instead, two solutions to zero-copy I/O are used in practice. Both eliminate the copy across
the kernel-user boundary for large blocks of data; for small chunks of data, the extra copy
does not hurt performance.
The more widely used approach manipulates the process page table to simulate a copy. For
this to work, the application must first align its user-level buffer to a page boundary. The
user-level buffer is provided to the kernel on a read or write system call, and its alignment
and size is up to the application.
```

#### Chunk 2

- Chunk ID: `07d37d4f68cfc154`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `110`
- Score: `n/a `

```text
data appears exactly where it was expected! The kernel can reclaim any physical memory
behind the empty buffer.
More recently, some hardware I/O devices have been designed to be able to transfer data to
and from virtual addresses, rather than only to and from physical addresses. The kernel hands
the virtual address of the user-level buffer to the hardware device. The hardware device,
rather than the kernel, walks the multi-level page table to determine which physical page
frame to use for the device transfer. When the transfer completes, the data is automatically
where it belongs, with no extra work by the kernel. This procedure is a bit more complicated
for incoming network packets, as the decision as to which process should receive which
```

#### Chunk 3

- Chunk ID: `5fe237045df373b7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `110`
- Score: `n/a `

```text
the program will trap to the kernel and the kernel can make an explicit copy at that point.
Figure 10.2: The contents of the page table before and after the kernel “copies” data to user-level by swapping the page
table entry to point to the kernel buffer.
In the other direction, once the data is in the kernel buffer, the operating system can simulate a
copy up to user-space by switching the pointer in the page table, as shown in Figure 10.2. The
process page table originally pointed to the page frame containing the (empty) user buffer;
now it points to the page frame containing the (full) kernel buffer. To the user program, the
data appears exactly where it was expected! The kernel can reclaim any physical memory
behind the empty buffer.
```

#### Chunk 4

- Chunk ID: `8eb78a2bb6480834`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `168`
- Score: `n/a `

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

#### Chunk 5

- Chunk ID: `a2d55c0a2c9fa254`
- Source: `649b3c369d4f4b6596d4bc6774e9d03f_OS_Principles_Practice_Vol_2.pdf`
- Page: `300`
- Score: `n/a `

```text
wound wait
An approach to deadlock recovery that ensures progress by aborting the most recent
transaction in any deadlock.
write acceleration
Data to be stored on disk is first written to the disk’s buffer memory. The write is then
acknowledged and completed in the background.
write-back cache
A cache where updates can be stored in the cache and only sent to memory when the
cache runs out of space.
write-through cache
A cache where updates are sent immediately to memory.
zero-copy I/O
A technique for transferring data across the kernel-user boundary without a memory-to-
memory copy, e.g., by manipulating page table entries.
```

## q46

**Question:** If a virtual machine is “just software pretending to be hardware,” why isn’t it unbearably slow?

### Method A

- Retrieval latency: 0.221s
- Generation latency: 9.265s

**Answer:**

Because a VM usually **does not simulate every CPU instruction in software**.

Most of the time, the guest OS and its applications run **directly on the real CPU**, almost like normal programs. The virtual machine monitor / hypervisor only steps in for sensitive operations, such as:

- accessing hardware devices,
- changing page tables,
- handling privileged CPU instructions,
- managing interrupts,
- scheduling CPU time.

So the VM is “pretending to be hardware,” but it relies heavily on **real hardware execution**.

Modern VMs are fast mainly because of:

1. **Hardware virtualization support**  
   CPUs have features that make it efficient to run guest operating systems safely. The guest thinks it is privileged, but the host/hypervisor still remains in control.

2. **Trapping only special operations**  
   Ordinary instructions like arithmetic, memory operations, and application code run normally on the processor. Only privileged actions trap into the hypervisor.

3. **Paravirtualization optimizations**  
   Sometimes the guest OS knows it is virtualized and cooperates with the host. For example, if the guest has no work to do, instead of spinning in an idle loop, it can yield the CPU to the host immediately.

4. **Efficient device virtualization**  
   Devices are often not fully emulated instruction-by-instruction. Instead, VMs use optimized virtual drivers or direct hardware support.

So a VM can be much slower if it fully emulates different hardware, but normal virtualization is not like that. It is more like:

> “Run directly on the real machine most of the time, and ask the hypervisor for help only when necessary.”

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ae427b00e908be27`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `113`
- Score: `0.701502 vector_distance`

```text
machine. The hardware dependent layer, specific to the underlying hardware, is replaced with code that understands about
the virtual machine. This is called paravirtualization, because the resulting guest operating system is almost, but not precisely,
the same as if it were running on real, physical hardware.
Paravirtualization is helpful in several ways. Perhaps the most important is handling the idle loop. What should happen when
the guest operating system has no threads to run? If the guest believes it is running on physical hardware, then nothing — the
guest spins waiting for more work to do, perhaps putting itself in low power mode. Eventually the hardware will cause a
```

#### Chunk 2

- Chunk ID: `fc6cfb800d7d9264`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `24`
- Score: `0.774181 vector_distance`

```text
While some applications are designed to take advantage of a computer’s specific hardware
configuration and resource assignment, most programmers prefer to use a higher level of
abstraction.
Virtualization provides an application with the illusion of resources that are not physically
present. For example, the operating system can provide the abstraction that each application
has a dedicated processor, even though at a physical level there may be only a single
processor shared among all the applications running on the computer.
With the right hardware and ope rating system support, most physical resources can be
virtualized. For example, hardware provides only a small, finite amount of memory, while the
```

#### Chunk 3

- Chunk ID: `521890ce5e1e6fe2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `44`
- Score: `0.803144 vector_distance`

```text
share the same physical hardware. The primary design goal for virtual machines is thus
efficiency and low overhead.
Embedded systems. Over time, computers have become cheap enough to integrate into
any number of consumer devices, from cable TV set-top boxes, to microwave ovens, the
control systems for automobiles and airplanes, LEGO robots, and medical devices, such
as MRI machines and WiFi-based intravenous titration systems. Embedded devices
typically run a customized operating system bundled with the task-specific software that
controls the device. Although you might think these systems as too simple to merit much
attention, software errors in them can have devastating effects. One example is the
Therac-25, an early computer-controlled radiology device. Programming errors in the
```

#### Chunk 4

- Chunk ID: `a39d106c5ad76944`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `113`
- Score: `0.839307 vector_distance`

```text
guest spins waiting for more work to do, perhaps putting itself in low power mode. Eventually the hardware will cause a
timer interrupt, transferring control to the host operating system. The host can then decide whether to resume the virtual
machine or run some other thread (or even some other virtual machine).
With paravirtualization, however, the idle loop can be more efficient. The hardware dependent software implementing the idle
loop can trap into the host kernel, yielding the processor immediately to some other use.
Likewise, with paravirtualization, the hardware dependent code inside the guest operating system can make explicit calls to
the host kernel to change its page tables, removing the need for the host to simulate guest page table management.
```

#### Chunk 5

- Chunk ID: `1f237606d22be627`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `95`
- Score: `0.84084 vector_distance`

```text
the CPU, with precise exceptions. How would that affect the user-kernel switching
overhead?
9. With virtual machines, the host kernel runs in privileged mode to create a virtual
machine that runs in user mode. The virtual machine provides the illusion that the guest
kernel runs on its own machine in privileged mode, even though it is actually running in
user mode.
Early versions of the x86 architecture (pre-2006)  were not completely virtualizable —
these systems could not guarantee to run unmodified guest operating systems properly.
```

### Method B

- Retrieval latency: 0.661s
- Generation latency: 9.952s

**Answer:**

Because a VM usually **doesn’t pretend in software for every instruction**.

The key idea is:

> Most of the guest OS and its programs run **directly on the real CPU**.  
> The virtual machine monitor/hypervisor only intervenes when necessary.

So it is not like a slow full emulator translating every instruction one by one.

A simplified picture:

1. **Normal application instructions run natively**
   - Arithmetic, function calls, loops, ordinary memory operations mostly execute on the physical processor.
   - So they are close to normal speed.

2. **Privileged operations trap to the hypervisor**
   - If the guest OS tries to do something sensitive, like modify page tables, access hardware, or change CPU state, the hypervisor steps in.
   - It checks or emulates the operation safely.

3. **Modern CPUs have virtualization support**
   - Technologies like Intel VT-x and AMD-V are designed specifically to make this efficient.
   - The CPU helps separate host and guest execution instead of forcing everything to be simulated manually.

4. **Devices are often virtualized efficiently**
   - Disk, network, and graphics may use optimized virtual drivers.
   - In paravirtualization, the guest OS may even know it is in a VM and cooperate with the hypervisor for better performance.

So a VM is “software pretending to be hardware,” but it is a clever kind of pretending:

> run directly whenever possible, intercept only when necessary.

That is why VMs can be fast enough for normal use, though they can still be slower for workloads with lots of I/O, memory management, or hardware access.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `e4b42e87a01797c0`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `42`
- Score: `1.04202 rerank_score`

```text
The host operating system, also called a virtual machine monitor, exports an abstract
virtual machine (AVM) that is identical to the underlying hardware. The test operating system
running on top of  the virtual machine does not need to know that it is running in a virtual
environment — it executes instructions, accesses hardware devices, and restores application
state after an interrupt just as if it were running on real hardware.
Virtual machines are now widely used for operating system development, backward
compatibility, and cross-platform support. Application software that runs only on an old
version of an operating system can share hardware with entirely new applications. The
virtual machine monitor runs two virtual machines — on e for the new operating system for
```

#### Chunk 2

- Chunk ID: `c23c33d1090afe2e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `41`
- Score: `0.570892 rerank_score`

```text
of the hardware. New versions can only be tested by stopping every application and
rebooting the system, essentially turning the computer back into a single-user system.
Needless to say, this was an expensive operation, often scheduled for the dead of the night.
Virtual machines address this limitation (see Figure 1.4). Instead of running a test operating
system directly on the hardware, virtual machines run an operating system as an application.
```

#### Chunk 3

- Chunk ID: `ae427b00e908be27`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `113`
- Score: `0.450698 rerank_score`

```text
machine. The hardware dependent layer, specific to the underlying hardware, is replaced with code that understands about
the virtual machine. This is called paravirtualization, because the resulting guest operating system is almost, but not precisely,
the same as if it were running on real, physical hardware.
Paravirtualization is helpful in several ways. Perhaps the most important is handling the idle loop. What should happen when
the guest operating system has no threads to run? If the guest believes it is running on physical hardware, then nothing — the
guest spins waiting for more work to do, perhaps putting itself in low power mode. Eventually the hardware will cause a
```

#### Chunk 4

- Chunk ID: `68a2ecd742b66382`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `111`
- Score: `0.233421 rerank_score`

```text
A virtual machine is a way for a host operating system to run a guest operating system as an
application process. The host simulates the behavior of a physical machine so that the guest
system behaves as if it was running on real hardware. Virtual machines are widely used on
client machines to run applications that are not native to the current version of the operating
system. They are also widely used in data centers to allow a single physical machine to be
shared between multiple independent uses, each of which can be written as if it has system
administrator control over the entire (virtual) machine. For example, multiple web servers,
representing different web sites, can be hosted on the same physical machine if they each run
inside a separate virtual machine.
```

#### Chunk 5

- Chunk ID: `a57c6dfbad2bf4e0`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `114`
- Score: `0.0162378 rerank_score`

```text
Although this hardware support simplifies the construction of virtual machines, it is not clear
if it improves performance. The handling of a TLB miss is slower since the host operating
system must consult two page tables instead of one; changes to the guest page table are faster
because the host does not need to maintain the shadow page table. It remains to be seen if this
tradeoff is useful in practice.
10.2.2 Transparent Memory Compression
A theme running throughout this book  is the difficulty of multiplexing multiplexors. With
virtual machines, both the host operating system and the guest operating system are attempting
to do t he same task: to efficiently multiplex a set of tasks onto a limited amount of memory.
```

### Method C

- Retrieval latency: 0.840s
- Generation latency: 9.107s

**Answer:**

Because a VM usually **does not simulate every hardware action in software**.

The key idea is: most of the time, the guest OS and its programs run **directly on the real CPU**.

A virtual machine monitor / hypervisor only steps in when something sensitive happens.

For example:

- Normal program instructions like arithmetic, function calls, memory operations → run directly on the physical processor.
- Privileged operations like changing page tables, accessing devices, handling interrupts → intercepted by the hypervisor.
- I/O operations like disk and network access → often handled through optimized virtual devices or paravirtualized drivers.

So a VM is not like a slow full software emulator where every instruction is interpreted. It is more like:

> “Run normally, but trap to the hypervisor when the guest tries to do something that needs virtualization.”

Modern CPUs also include **hardware support for virtualization**, such as Intel VT-x and AMD-V. These features make it efficient for the processor to switch between the guest VM and the hypervisor.

Also, many VM systems use optimizations like:

- **paravirtualized drivers**, where the guest OS knows it is in a VM and cooperates with the hypervisor;
- **memory virtualization hardware**, so address translation is faster;
- **batching/caching I/O**, reducing expensive transitions.

That is why VMs have overhead, but not usually “unbearable” overhead.

A short way to say it:

> A VM is software pretending to be hardware, but it lets the real hardware do most of the work.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `ae427b00e908be27`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `113`
- Score: `n/a `

```text
machine. The hardware dependent layer, specific to the underlying hardware, is replaced with code that understands about
the virtual machine. This is called paravirtualization, because the resulting guest operating system is almost, but not precisely,
the same as if it were running on real, physical hardware.
Paravirtualization is helpful in several ways. Perhaps the most important is handling the idle loop. What should happen when
the guest operating system has no threads to run? If the guest believes it is running on physical hardware, then nothing — the
guest spins waiting for more work to do, perhaps putting itself in low power mode. Eventually the hardware will cause a
```

#### Chunk 2

- Chunk ID: `fc6cfb800d7d9264`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `24`
- Score: `n/a `

```text
While some applications are designed to take advantage of a computer’s specific hardware
configuration and resource assignment, most programmers prefer to use a higher level of
abstraction.
Virtualization provides an application with the illusion of resources that are not physically
present. For example, the operating system can provide the abstraction that each application
has a dedicated processor, even though at a physical level there may be only a single
processor shared among all the applications running on the computer.
With the right hardware and ope rating system support, most physical resources can be
virtualized. For example, hardware provides only a small, finite amount of memory, while the
```

#### Chunk 3

- Chunk ID: `521890ce5e1e6fe2`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `44`
- Score: `n/a `

```text
share the same physical hardware. The primary design goal for virtual machines is thus
efficiency and low overhead.
Embedded systems. Over time, computers have become cheap enough to integrate into
any number of consumer devices, from cable TV set-top boxes, to microwave ovens, the
control systems for automobiles and airplanes, LEGO robots, and medical devices, such
as MRI machines and WiFi-based intravenous titration systems. Embedded devices
typically run a customized operating system bundled with the task-specific software that
controls the device. Although you might think these systems as too simple to merit much
attention, software errors in them can have devastating effects. One example is the
Therac-25, an early computer-controlled radiology device. Programming errors in the
```

#### Chunk 4

- Chunk ID: `c23c33d1090afe2e`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `41`
- Score: `n/a `

```text
of the hardware. New versions can only be tested by stopping every application and
rebooting the system, essentially turning the computer back into a single-user system.
Needless to say, this was an expensive operation, often scheduled for the dead of the night.
Virtual machines address this limitation (see Figure 1.4). Instead of running a test operating
system directly on the hardware, virtual machines run an operating system as an application.
```

#### Chunk 5

- Chunk ID: `e4b42e87a01797c0`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `42`
- Score: `n/a `

```text
The host operating system, also called a virtual machine monitor, exports an abstract
virtual machine (AVM) that is identical to the underlying hardware. The test operating system
running on top of  the virtual machine does not need to know that it is running in a virtual
environment — it executes instructions, accesses hardware devices, and restores application
state after an interrupt just as if it were running on real hardware.
Virtual machines are now widely used for operating system development, backward
compatibility, and cross-platform support. Application software that runs only on an old
version of an operating system can share hardware with entirely new applications. The
virtual machine monitor runs two virtual machines — on e for the new operating system for
```

## q47

**Question:** Why can copy-on-write make operations like process creation or snapshotting much cheaper than they first appear?

### Method A

- Retrieval latency: 0.782s
- Generation latency: 6.225s

**Answer:**

Copy-on-write makes operations like **process creation** or **snapshotting** cheaper because it avoids making a full physical copy immediately.

Instead of copying all memory/pages up front:

1. The OS lets the two “copies” share the same physical pages.
2. Those shared pages are marked **read-only**.
3. If either process/snapshot tries to write to a shared page, a protection fault occurs.
4. Only then does the OS make a real copy of that specific page.

So the operation is cheap at first because it mostly copies **metadata/page table entries**, not the actual memory contents.

This is especially useful for things like `fork()`:

- A child process initially shares the parent’s memory.
- If the child soon calls `exec()`, most of the old memory is never modified.
- Therefore, copying all of it would have been wasted work.

In short: copy-on-write is cheap because it turns “copy everything now” into “copy only the parts that are actually changed later.”

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5f2b173f0f6f35a1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `n/a `

```text
Copy-on-write. Copy-on-write allows multiple processes to have logically separate
copies of the same memory region, backed by a single physical copy in memory. Each
page in the region is mapped read-only in each process; the operating system makes a
physical copy only when (and if) a page is modified.
Memory-mapped files. Disk files can be made part of a process’s virtual address
space, allowing the process to access the data in the file using normal processor
instructions. When a page from a memory-mapped file is first accessed, a protection
fault traps to the operating system so that it can bring the page into memory from disk.
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
```

#### Chunk 2

- Chunk ID: `349a1396637e4d07`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `n/a `

```text
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
same memory as the parent. If the child changes some data, it should change only its copy, and not its parent’s data. On the
other hand, most of the time, the child process in UNIX fork simply calls UNIX exec; the shared data is there as a
programming convenience.
We can make this work efficiently by using an idea called copy-on-write. During the fork, all of the segments shared
between the parent and child process are marked “read-only” in both segment tables. If either side modifies data in a
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
```

#### Chunk 3

- Chunk ID: `d5cff6e43b788402`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `n/a `

```text
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
store to one of these pages, we can make a real copy of the underlying page frame before
resuming the process. Likewise, for zero-on-reference, we can set the page table entry at the
top of  the stack to be invalid, causing a trap into the kernel. This allows us to extend the stack
only as needed.
Page tables allow other features to be added. For example, we can start a program running
before all of its code and data are loaded into memory. Initially, the operating system marks
all of the page table entries for a new process as invalid; as pages are brought in from disk, it
marks those pages as read-only (for code pages) or read-write (for data pages). Once the first
```

#### Chunk 4

- Chunk ID: `e8ba6fce0cbe7428`
- Source: `b50cec05e9b147fcbd7e238115487292_OS_Principles_Practice_Vol_1.pdf`
- Page: `144`
- Score: `n/a `

```text
cooperating threads
Threads that read and write shared state.
cooperative caching
Using the memory of nearby nodes over a network as a cache to avoid the latency of
going to disk.
cooperative multi-threading
Each thread runs without interruption until it explicitly relinquishes control of the
processor, e.g., by exiting or calling thread_yield.
copy-on-write
A method of  sharing physical memory between two logically distinct copies (e.g., in
different processes). Each shared page is marked as read-only so that the operating
system kernel is invoked and can make a copy of the page if either process tries to write
it. The process can then modify the copy and resume normal execution.
copy-on-write file system
A file system where an update to the file system is made by writing new versions of
```

#### Chunk 5

- Chunk ID: `0e8e43768bc1162d`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `178`
- Score: `n/a `

```text
cooperating threads
Threads that read and write shared state.
cooperative caching
Using the memory of nearby nodes over a network as a cache to avoid the latency of
going to disk.
cooperative multi-threading
Each thread runs without interruption until it explicitly relinquishes control of the
processor, e.g., by exiting or calling thread_yield.
copy-on-write
A method of  sharing physical memory between two logically distinct copies (e.g., in
different processes). Each shared page is marked as read-only so that the operating
system kernel is invoked and can make a copy of the page if either process tries to write
it. The process can then modify the copy and resume normal execution.
copy-on-write file system
A file system where an update to the file system is made by writing new versions of
```

### Method B

- Retrieval latency: 0.201s
- Generation latency: 9.524s

**Answer:**

Copy-on-write makes these operations cheap because it **does not copy the actual data immediately**.

Instead, it creates a new *logical* copy that initially shares the same underlying physical memory or disk blocks.

For example, with process creation using `fork`:

- The OS gives the child process page table entries pointing to the same physical pages as the parent.
- Those shared pages are marked **read-only**.
- If neither process modifies a page, no real copy is ever made.
- If one process writes to a page, a protection fault occurs, and the OS copies only that page.

So the cost of `fork` is mostly just copying metadata like page table entries, not duplicating the whole address space.

This is especially useful because many child processes quickly call `exec`, replacing their memory anyway. In that common case, copying all memory during `fork` would have been wasted work.

The same idea applies to snapshots:

- A snapshot can initially just reference the same blocks as the original.
- Only when data changes are new copies of the changed blocks written elsewhere.
- Unchanged data remains shared.

So copy-on-write is cheap because it turns a large immediate copy into **small copies only when changes actually happen**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5f2b173f0f6f35a1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `0.760642 vector_distance`

```text
Copy-on-write. Copy-on-write allows multiple processes to have logically separate
copies of the same memory region, backed by a single physical copy in memory. Each
page in the region is mapped read-only in each process; the operating system makes a
physical copy only when (and if) a page is modified.
Memory-mapped files. Disk files can be made part of a process’s virtual address
space, allowing the process to access the data in the file using normal processor
instructions. When a page from a memory-mapped file is first accessed, a protection
fault traps to the operating system so that it can bring the page into memory from disk.
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
```

#### Chunk 2

- Chunk ID: `a998281d9450f7e7`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `0.923572 vector_distance`

```text
UNIX fork and copy-on-write
In Chapter 3, we described the UNIX fork system call. UNIX creates a new process by making a complete copy of the
parent process; the parent process and the child process are identical except for the return value from fork. The child
process can then set up its I/O and eventually use the UNIX exec system call to run a new program. We promised at the
time we would explain how this can be done efficiently.
With segments, this is now possible. To fork a process, we can simply make a copy of the parent’s segment table; we do not
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
```

#### Chunk 3

- Chunk ID: `349a1396637e4d07`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `26`
- Score: `0.945599 vector_distance`

```text
need to copy any of its physical memory. Of course, we want the child to be a copy of the parent, and not just point to the
same memory as the parent. If the child changes some data, it should change only its copy, and not its parent’s data. On the
other hand, most of the time, the child process in UNIX fork simply calls UNIX exec; the shared data is there as a
programming convenience.
We can make this work efficiently by using an idea called copy-on-write. During the fork, all of the segments shared
between the parent and child process are marked “read-only” in both segment tables. If either side modifies data in a
segment, an exception is raised and a full memory copy of that segment is made at that time. In the common case, the child
```

#### Chunk 4

- Chunk ID: `d5cff6e43b788402`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `0.976723 vector_distance`

```text
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
store to one of these pages, we can make a real copy of the underlying page frame before
resuming the process. Likewise, for zero-on-reference, we can set the page table entry at the
top of  the stack to be invalid, causing a trap into the kernel. This allows us to extend the stack
only as needed.
Page tables allow other features to be added. For example, we can start a program running
before all of its code and data are loaded into memory. Initially, the operating system marks
all of the page table entries for a new process as invalid; as pages are brought in from disk, it
marks those pages as read-only (for code pages) or read-write (for data pages). Once the first
```

#### Chunk 5

- Chunk ID: `e46ea0383cfe581b`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `97`
- Score: `0.98246 vector_distance`

```text
13.3.4 Copy-On-Write File Systems
When updating an existing file, copy-on-write (COW) file systems do n ot overwrite the
existing data or metadata; instead, they write new versions to new locations.
```

### Method C

- Retrieval latency: 0.429s
- Generation latency: 6.281s

**Answer:**

Copy-on-write makes operations like **process creation** or **snapshotting** cheaper because the system does **not immediately copy all memory**.

Instead, it does this:

1. The parent/process memory pages are **shared physically**.
2. The OS marks those shared pages as **read-only**.
3. If a process only reads the memory, no copying happens.
4. Only when a process tries to **write** to a shared page does a protection fault occur.
5. The OS then copies just that page, gives the writer its own private copy, and resumes execution.

So an operation that *looks* like it requires copying a whole address space can often be implemented by just copying page table entries and changing permissions.

For example, when creating a process with `fork`, the child can initially share the parent’s pages. If the child soon calls `exec`, most of those pages never need to be copied at all.

Similarly, for a memory snapshot/checkpoint, the OS can mark pages read-only and only copy pages when they are modified, preserving the old version for the snapshot.

In short: **copy-on-write is cheap because it delays copying until it is actually necessary, and often much of the copying never happens.**

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `5f2b173f0f6f35a1`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `107`
- Score: `0.74834 rerank_score`

```text
Copy-on-write. Copy-on-write allows multiple processes to have logically separate
copies of the same memory region, backed by a single physical copy in memory. Each
page in the region is mapped read-only in each process; the operating system makes a
physical copy only when (and if) a page is modified.
Memory-mapped files. Disk files can be made part of a process’s virtual address
space, allowing the process to access the data in the file using normal processor
instructions. When a page from a memory-mapped file is first accessed, a protection
fault traps to the operating system so that it can bring the page into memory from disk.
The first write to a file block can also be caught, marking the block as needing to be
written back to disk.
```

#### Chunk 2

- Chunk ID: `50998cd7caa7a5bd`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `119`
- Score: `-0.546762 rerank_score`

```text
handler, rather than the speed of the processor.
However, we can come close. When we take a checkpoint, we mark all pages as read-only to
ensure that the checkpoint includes a consistent snapshot of the state of the process’s memory.
Then we trap to the kernel on the first store instruction to each page, to allow the kernel to
make a copy-on-write. The kernel resets the page to be read-write so that successive store
instructions to the same page can go at full speed, bu t it can also record the page as having
been modified.
```

#### Chunk 3

- Chunk ID: `d5cff6e43b788402`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `29`
- Score: `-1.03831 rerank_score`

```text
For copy-on-write, we need to copy the page table entries and set them to read-only; on a
store to one of these pages, we can make a real copy of the underlying page frame before
resuming the process. Likewise, for zero-on-reference, we can set the page table entry at the
top of  the stack to be invalid, causing a trap into the kernel. This allows us to extend the stack
only as needed.
Page tables allow other features to be added. For example, we can start a program running
before all of its code and data are loaded into memory. Initially, the operating system marks
all of the page table entries for a new process as invalid; as pages are brought in from disk, it
marks those pages as read-only (for code pages) or read-write (for data pages). Once the first
```

#### Chunk 4

- Chunk ID: `5bf34a6ee82f0acc`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `60`
- Score: `-1.09558 rerank_score`

```text
at today’s computers and wonder how we could have gotten by with as little as a
gigabyte of DRAM! These massive memories will require ever deeper multi-level page
tables. Fortunately, the same trends that make it possible to build gigantic memories also
make it possible to design very large TLBs to hide the increasing depth of the lookup
trees.
Multiprocessors. On the other hand, multiprocessors will mean that maintaining TLB
consistency will become increasingly expensive. A key assumption for using page table
protection hardware for implementing copy-on-write and fill-on-demand is that the cost
of modifying page table entries is modest. One possibility is that hardware will be
added to systems to make TLB shootdown a much cheaper operation, e.g., by making
```

#### Chunk 5

- Chunk ID: `e156650562ebaafd`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `143`
- Score: `-1.85923 rerank_score`

```text
cooperating threads
Threads that read and write shared state.
cooperative caching
Using the memory of nearby nodes over a network as a cache to avoid the latency of
going to disk.
cooperative multi-threading
Each thread runs without interruption until it explicitly relinquishes control of the
processor, e.g., by exiting or calling thread_yield.
copy-on-write
A method of  sharing physical memory between two logically distinct copies (e.g., in
different processes). Each shared page is marked as read-only so that the operating
system kernel is invoked and can make a copy of the page if either process tries to write
it. The process can then modify the copy and resume normal execution.
copy-on-write file system
A file system where an update to the file system is made by writing new versions of
```

## q48

**Question:** If a directory is just a special kind of file, what information does it actually store?

### Method A

- Retrieval latency: 0.816s
- Generation latency: 7.249s

**Answer:**

A directory stores **directory entries**: mappings from human-readable names to the underlying file system objects.

Conceptually, it contains records like:

```text
"hw1.txt"   -> inode/file number 18342
"notes"     -> inode/file number 22010
"."         -> this directory
".."        -> parent directory
```

So it does **not** store the actual contents of `hw1.txt`. Instead, it stores enough information for the OS to find the file’s metadata and data blocks elsewhere.

In many Unix-like systems, a directory entry mainly contains:

- a **name**: e.g. `hw1.txt`
- a **file identifier**: often an inode number
- sometimes extra type info, depending on the file system

The directory itself also has normal file metadata, such as permissions, owner, size, and modification time. Its “data” is the list or structure of name-to-file mappings.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `63d4e8c7367ace8f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `22`
- Score: `n/a `

```text
Files provide a higher-level abstraction than the underlying storage device: they let a single,
meaningful name refer to an (almost) arbitrarily-sized amount of data. For example
/home/Bob/Classes/OS/hw1.txt might be stored on disk in blocks 0x0A713F 28,
0xB3CA349A , and 0x33A229B 8, bu t it is much more convenient to refer to the data by its
name than by this list of disk addresses.
A file’s information has two parts, metadata and data. A file’s metadata is information about
the file that is understood a nd managed by the operating system. For example, a file’s
metadata typically includes the file’s size, its modification time, its owner, and its security
information such as whether it may be read, written, or executed by the owner or by other
users.
```

#### Chunk 2

- Chunk ID: `9306dbe33cefd0ff`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `73`
- Score: `n/a `

```text
Work, and foo.txt, along with . (the current directory) and .. (the parent directory).
Simple lists work fine when the number of directory entries is small, and that was the
expected case for many early file systems, but systems occasionally encounter workloads that
generate thousands of files in a directory. Once a directory has a few thousand entries, simple
list-based directories become sluggish.
To efficiently support directories with many entries, many recent file systems including Linux
XFS, Microsoft NTFS, and Oracle ZFS organize a directory’s contents as a tree. Similarly,
newer versions of ext2 augment the underlying linked list with an additional hash-based
structure to speed searches.
```

#### Chunk 3

- Chunk ID: `0165b2daf02b5038`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `23`
- Score: `n/a `

```text
In these systems, when you open a file to read or write its data, you specify not only the file but also the fork or stream you
want.
Directory. Whereas a file contains system-defined metadata and arbitrary data, directories
provide names for files. In particular, a file directory is a list of human-readable names and a
mapping from each name to a specific underlying file or directory. One common metaphor is
that a directory is a folder that contains documents (files) and other folders (directories).
```

#### Chunk 4

- Chunk ID: `11982d9dae80db6a`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `68`
- Score: `n/a `

```text
13. Files and Directories
What’s in a name? That which we call a rose
By any other name would smell as sweet. —Juliet
Romeo and J uliet (II, ii, 1-2)
(Shak espeare)
Recall from Chapter 11 that file systems use directories to provide hierarchically named
files, and that each file contains metadata and a sequence of data bytes. However, as
Chapter 12 discussed, storage devices provide a much lower-level abstraction — large
arrays of data blocks. Thus, to implement a file system, we must solve a translation problem:
How do w e go from a file name and offset to a block number?
A simple answer is that file systems implement a dictionary that maps keys (file name and
offset) to values (block number on a device). We already have many data structures for
```

#### Chunk 5

- Chunk ID: `6bd5598cfe9e1531`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `106`
- Score: `n/a `

```text
Formatting a file system includes writing a superblock that identifies the file system’s type and its key parameters such as its
type, block size, and inode array or MBR location and size. Again, for reliability, a file system typically stores multiple copies
of its superblock at several predefined locations.
Then, when an operating system boots, it can examine a disk to find its partitions, and it can examine each partition to identify
and configure its file systems.
13.4 Putting It All Together: File and Directory Access
In Section 13.2 we saw that directories are implemented as files, containing file name to file
number mappings, and in Section 13.3 we saw that files are implemented using an index
structure — typically a tree of some sort — to track the file’s blocks.
```

### Method B

- Retrieval latency: 0.179s
- Generation latency: 8.152s

**Answer:**

A directory stores **directory entries**: mappings from human-readable names to the underlying file system objects.

For example, a directory might contain entries like:

```text
foo.txt   -> file number / inode 66212871
notes     -> file number / inode 88420110
Work      -> file number / inode 19283746
.         -> this directory
..        -> parent directory
```

So the directory does **not** store the actual contents of `foo.txt`. Instead, it stores information needed to find it.

In many file systems, each directory entry contains roughly:

- the **name** of a file or subdirectory, e.g. `foo.txt`
- a reference to the underlying file object, often an **inode number** or file number
- sometimes extra type information, such as “file” or “directory”

The file’s actual metadata, like size, owner, permissions, and disk block locations, is usually stored elsewhere, such as in the inode or file record.

So: a directory is a special file whose “data” is basically a table or structure mapping **names → files/directories**.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `63d4e8c7367ace8f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `22`
- Score: `0.792855 vector_distance`

```text
Files provide a higher-level abstraction than the underlying storage device: they let a single,
meaningful name refer to an (almost) arbitrarily-sized amount of data. For example
/home/Bob/Classes/OS/hw1.txt might be stored on disk in blocks 0x0A713F 28,
0xB3CA349A , and 0x33A229B 8, bu t it is much more convenient to refer to the data by its
name than by this list of disk addresses.
A file’s information has two parts, metadata and data. A file’s metadata is information about
the file that is understood a nd managed by the operating system. For example, a file’s
metadata typically includes the file’s size, its modification time, its owner, and its security
information such as whether it may be read, written, or executed by the owner or by other
users.
```

#### Chunk 2

- Chunk ID: `6120e25d0baf7412`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `70`
- Score: `0.835289 vector_distance`

```text
Implementation details. In this chapter, we first discuss how directories are implemented.
Then, we look at the details of how specific file systems handle the details of placing and
finding data in persistent storage by implementing different index structures, free space maps,
and locality heuristics.
13.2 Directories: Naming Data
As Figure 13.1 indicates, to access a file, the file system first translates the file’s name to its
number. For example, the file called /home/tom/foo.txt might internally known as file
66212871. F ile systems use directories to store their mappings from human-readable names
to internal file numbers, and they organize these directories hierarchically so that users can
group related files and directories.
```

#### Chunk 3

- Chunk ID: `0165b2daf02b5038`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `23`
- Score: `0.847503 vector_distance`

```text
In these systems, when you open a file to read or write its data, you specify not only the file but also the fork or stream you
want.
Directory. Whereas a file contains system-defined metadata and arbitrary data, directories
provide names for files. In particular, a file directory is a list of human-readable names and a
mapping from each name to a specific underlying file or directory. One common metaphor is
that a directory is a folder that contains documents (files) and other folders (directories).
```

#### Chunk 4

- Chunk ID: `11982d9dae80db6a`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `68`
- Score: `0.855741 vector_distance`

```text
13. Files and Directories
What’s in a name? That which we call a rose
By any other name would smell as sweet. —Juliet
Romeo and J uliet (II, ii, 1-2)
(Shak espeare)
Recall from Chapter 11 that file systems use directories to provide hierarchically named
files, and that each file contains metadata and a sequence of data bytes. However, as
Chapter 12 discussed, storage devices provide a much lower-level abstraction — large
arrays of data blocks. Thus, to implement a file system, we must solve a translation problem:
How do w e go from a file name and offset to a block number?
A simple answer is that file systems implement a dictionary that maps keys (file name and
offset) to values (block number on a device). We already have many data structures for
```

#### Chunk 5

- Chunk ID: `9306dbe33cefd0ff`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `73`
- Score: `0.875678 vector_distance`

```text
Work, and foo.txt, along with . (the current directory) and .. (the parent directory).
Simple lists work fine when the number of directory entries is small, and that was the
expected case for many early file systems, but systems occasionally encounter workloads that
generate thousands of files in a directory. Once a directory has a few thousand entries, simple
list-based directories become sluggish.
To efficiently support directories with many entries, many recent file systems including Linux
XFS, Microsoft NTFS, and Oracle ZFS organize a directory’s contents as a tree. Similarly,
newer versions of ext2 augment the underlying linked list with an additional hash-based
structure to speed searches.
```

### Method C

- Retrieval latency: 0.409s
- Generation latency: 6.648s

**Answer:**

A directory stores **directory entries**: mappings from a human-readable name to the underlying file-system identifier.

For example, conceptually it contains entries like:

```text
name        → file number / inode
foo.txt     → 66212871
photos      → 91827364
notes.pdf   → 12345678
```

So a directory does **not** mainly store the contents of the files inside it. Instead, it stores information like:

- the **name** of each file or subdirectory
- the corresponding **file number / inode / internal identifier**
- sometimes extra directory-entry metadata, depending on the file system

The actual file data and most file metadata are stored elsewhere. The directory’s job is to let the file system translate a path like:

```text
/home/alex/foo.txt
```

into the internal file number for `foo.txt`.

That is why a directory is “file-like” internally, but normal programs usually cannot freely edit it with ordinary `write()` calls—the file system must preserve valid name → file mappings.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `974bc6297be5fcb9`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `72`
- Score: `4.10064 rerank_score`

```text
be accessed soon), so we expect that caching will reduce the number of disk accesses needed
for most lookups.
Directory API. If file systems use files to store directory information, can we just use the
standard ope n/close/read/write API to access them?
No. Directories use a specialized API because they must control the contents of these files.
For example, file systems must prevent applications from corrupting the list of name →file
number mappings, which could prevent the operating system from performing lookups or
updates. As another example, the file system should enforce the invariant that each file
number in a valid directory entry refers to a file that actually exists.
File systems therefore provide special system calls for modifying directory files. For
```

#### Chunk 2

- Chunk ID: `0165b2daf02b5038`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `23`
- Score: `0.497168 rerank_score`

```text
In these systems, when you open a file to read or write its data, you specify not only the file but also the fork or stream you
want.
Directory. Whereas a file contains system-defined metadata and arbitrary data, directories
provide names for files. In particular, a file directory is a list of human-readable names and a
mapping from each name to a specific underlying file or directory. One common metaphor is
that a directory is a folder that contains documents (files) and other folders (directories).
```

#### Chunk 3

- Chunk ID: `eaed6352098bf7a7`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `96`
- Score: `0.167221 rerank_score`

```text
ordinary files with well-known low-numbered file numbers. For example, file number 5 is
the root directory, file number 6 is the free space bitmap, and file number 8 contains a list of
the volume’s bad blocks.
File number 9, called $Secure, contains security and access control information. NTFS has a
flexible security model in which a file can be associated with a list of users and groups, with
specific access control settings for each listed principal. In early versions of NTFS, such an
access control list was stored with each file, but these lists consumed a nontrivial amount of
space and many lists had identical contents. So, current implementations of NTFS store each
unique access control list once in the special $Secure file, indexed by a fixed-length unique
```

#### Chunk 4

- Chunk ID: `d36cf5581a3f4ba6`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `70`
- Score: `0.0134191 rerank_score`

```text
to internal file numbers, and they organize these directories hierarchically so that users can
group related files and directories.
Figure 13.2: A directory is a file that contains a collection of file name →file number mappings.
Implementing directories in a way that provides hierarchical, name-to-number mappings turns
out to be simple: use files to store directories. So, if the system needs to determine a file’s
number, it can just open up the appropriate directory file and scan through the file name/file
number pairs until it finds the right one.
For example, illustrates Figure 13.2 the contents of a single directory file. To ope n file
foo.txt, the file system would scan this directory file, find the foo.txt entry, and see that file
foo.txt has file number 66212871.
```

#### Chunk 5

- Chunk ID: `fc8f116e62e1a636`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `22`
- Score: `-0.738503 rerank_score`

```text
information such as whether it may be read, written, or executed by the owner or by other
users.
A file’s data can be whatever information a user or application puts in it. From the point of
view of the file system, a file’s data is just an array of untyped bytes. Applications can use
these bytes to store whatever information they want in whatever format they choose. Some
data have a simple structure. For example, an ASCII text file contains a sequence of bytes that
are interpreted as letters in the English alphabet. Conversely, data structures stored by
applications can be arbitrarily complex. For example, a .doc  files can contain text, formatting
information, and embedded obj ects and images, an ELF (Executable and Linkable File) files
```

## q49

**Question:** Why do modern file systems often use extents or tree-based metadata instead of simple linked allocation?

### Method A

- Retrieval latency: 0.499s
- Generation latency: 9.519s

**Answer:**

Modern file systems use **extents** and **tree-based metadata** because simple linked allocation does not scale well for large disks and large files.

### Simple linked allocation
In a linked scheme, each file is stored as a chain of blocks:

```text
block 5 -> block 19 -> block 8 -> block 42 -> ...
```

This is simple, but it has problems:

- **Poor random access**: to reach block 10,000 of a file, the file system may need to follow thousands of links.
- **Bad locality**: file blocks can be scattered across disk, causing many seeks or non-contiguous reads.
- **Large metadata overhead**: tracking every individual block becomes expensive for large files.
- **Fragility**: if one link is damaged, part of the file chain may become hard to recover.

### Extents
An **extent** records a whole contiguous range of blocks:

```text
start block = 1000, length = 500
```

Instead of storing 500 separate block pointers, the file system stores one extent.

Benefits:

- Much less metadata
- Better sequential read/write performance
- Better use of contiguous disk space
- Efficient for large files

This is why systems like **NTFS, ext4, and btrfs** use extents.

### Tree-based metadata
Trees are used to organize file metadata and extents efficiently.

Benefits:

- Fast lookup of file blocks
- Efficient random access
- Works well for very large files
- Handles sparse files better
- More flexible than fixed arrays or linked lists

So the short answer is:

> Modern file systems use extents and tree-based metadata because they provide better performance, scalability, and space efficiency than simple linked allocation, especially for large files and large disks.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `185107a93cfe3d01`
- Source: `22331ca37dd34a3e87cc458b9791c3a4_OS_Principles_Practice_Vol_3.pdf`
- Page: `30`
- Score: `2.24942 rerank_score`

```text
probably would not pick a simple array. A tree or a hash table are more appropriate, and
indeed, modern systems use both. We focus in this subsection on trees; we discuss hash tables
afterwards.
Many systems use tree-based address translation, although the details vary from system to
system, and the terminology can be a bit confusing. Despite the differences, the systems we
are about to describe have similar properties. They support coarse and fine-grained memory
protection and memory sharing, flexible memory placement, efficient memory allocation, and
efficient lookup for sparse address spaces, even for 64-bit machines.
```

#### Chunk 2

- Chunk ID: `2bcc6fa4c5c0b72f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `1.80309 rerank_score`

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

#### Chunk 3

- Chunk ID: `af0617e90c627ff3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `78`
- Score: `1.53447 rerank_score`

```text
Windows 7. In addition, the flexible tree and extent techniques are representative of
several widely used file systems such as the Linux ext4, XFS, and Reiser4 file systems,
the AIX/Linux Journaled File System (JFS), and the Apple Hierarchical File Systems
(HFS and HFS+).
COW/ZFS. Copy-on-write (COW) file systems update existing data and metadata
blocks by writing new versions to free disk blocks. This approach optimizes write
performance: because any data or metadata can be written to any free space on disk, the
file system can group otherwise random writes into large, sequential group writes.
To see how these ideas are implemented, we will examine the open-source ZFS, a
prominent copy-on-write file system that was introduced in the early 2000’ s by Sun
```

#### Chunk 4

- Chunk ID: `c9cf07128969b5de`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `0.871014 rerank_score`

```text
Sectors vs. pages; blocks vs. clusters; extents vs. runs
Although storage hardware arranges data in sectors (for magnetic disk) or pages (for flash), file systems often group
together a fixed number of disk sectors or flash pages into a larger allocation unit called a block. For example, we might
format a file system running on a disk with 512 byte sectors to use 4 KB blocks. Aggregating multiple sectors into a block
can reduce the overheads of allocating, tracking, and de-allocating blocks, but it may increase space overheads slightly.
FAT and NTFS refer to blocks as clusters, but for consistency we will use the term block in our discussions.
Finally, some file systems like NTFS, ext4, and btrfs store data in variable-length arrays of contiguous tracks called extents in
```

#### Chunk 5

- Chunk ID: `fb81bc2a59ae03a8`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `78`
- Score: `0.422457 rerank_score`

```text
random access efficiency, and it uses a collection of locality heuristics to get good
spatial locality for a wide range of workloads.
Today : In Linux, the popu lar ext2 and ext3 file systems are based on the FFS design.
NTFS. The Microsoft New Technology File System (NTFS) was introduced in the early
1990s  as a replacement for the FAT file system.
Techniques: Like FFS, NTFS uses a tree-based index structure, but the tree is more
flexible than FFS’s fixed tree. Additionally, NTFS optimizes its index structure for
sequential file layout by indexing variable-sized extents rather than individual blocks.
Today : NTFS remains the primary file system for Microsoft operating systems such as
Windows 7. In addition, the flexible tree and extent techniques are representative of
```

### Method B

- Retrieval latency: 1.072s
- Generation latency: 9.491s

**Answer:**

Modern file systems use **extents** or **tree-based metadata** instead of simple **linked allocation** because linked allocation performs poorly for many common workloads.

### Simple linked allocation
In linked allocation, each file block points to the next block:

```text
block 1 -> block 2 -> block 3 -> block 4
```

This is simple, but it has problems:

- **Poor random access**: to read block 1000 of a file, the file system may need to follow 999 pointers first.
- **Many disk seeks** if blocks are scattered across the disk.
- **Pointer overhead**: each block needs space for a pointer.
- **Bad locality**: consecutive file blocks may not be physically near each other.

### Tree-based metadata
Tree-based structures let the file system find file blocks efficiently.

For example, FFS-style file systems use a fixed tree with direct, indirect, double-indirect pointers, etc. Because indirect blocks can contain many pointers, the tree has a **high fan-out**. If a block is 4 KB and each block pointer is 4 bytes, one indirect block can point to about **1024 data blocks**.

That means:

- Faster random access
- Fewer metadata reads
- Better support for large files
- Efficient sequential access after an indirect block is loaded

### Extents
An **extent** represents a run of consecutive blocks, for example:

```text
start block = 5000, length = 200
```

Instead of storing metadata for every individual block, the file system stores one record for a whole contiguous region.

This gives:

- Less metadata
- Better sequential read/write performance
- Better spatial locality
- Easier handling of large files

### In short

Modern file systems prefer extents or tree-based metadata because they support:

- efficient random access,
- large files,
- sequential performance,
- reduced metadata overhead,
- and better disk locality.

Linked allocation is simple, but it does not scale well for modern storage systems and workloads.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `6ff332036e3b1db3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `85`
- Score: `n/a `

```text
1. Tree structure. Each file is represented as a tree, which allows the file system to
efficiently find any block of a file.
2. High degree. The FFS tree uses internal nodes with many children compared to the
binary trees often used for in-memory data structures (i.e., internal nodes have high
degree or fan out ). For example, if a file block is 4 KB and a blockID is 4 bytes, then
each indirect block can contain pointers to 1024 bl ocks.
High degree nodes make sense for on-disk data structures where (1) we want to
minimize the number of seeks, (2) the cost of reading several kilobytes of sequential
data is not much higher than the cost of reading the first byte, and (3) data must be read
and written at least a sector at a time.
```

#### Chunk 2

- Chunk ID: `6f4a3eacff4e6fea`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `85`
- Score: `n/a `

```text
data is not much higher than the cost of reading the first byte, and (3) data must be read
and written at least a sector at a time.
High degree nodes also improve efficiency for sequential reads and writes — on ce an
indirect block is read, hundreds of data blocks can be read before the next indirect block
is needed. Runs between reads of double indirect blocks are even larger.
3. Fixed structure. The FFS tree has a fixed structure. For a given configuration of FFS,
the first set of d poi nters always point to the first d blocks of a file; the next pointer is an
indirect pointer that points to an indirect block; etc.
Compared to a dynamic tree that can add layers of indirection above  a block as a file
grows, the main advantage of the fixed structure is implementation simplicity.
```

#### Chunk 3

- Chunk ID: `fb81bc2a59ae03a8`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `78`
- Score: `n/a `

```text
random access efficiency, and it uses a collection of locality heuristics to get good
spatial locality for a wide range of workloads.
Today : In Linux, the popu lar ext2 and ext3 file systems are based on the FFS design.
NTFS. The Microsoft New Technology File System (NTFS) was introduced in the early
1990s  as a replacement for the FAT file system.
Techniques: Like FFS, NTFS uses a tree-based index structure, but the tree is more
flexible than FFS’s fixed tree. Additionally, NTFS optimizes its index structure for
sequential file layout by indexing variable-sized extents rather than individual blocks.
Today : NTFS remains the primary file system for Microsoft operating systems such as
Windows 7. In addition, the flexible tree and extent techniques are representative of
```

#### Chunk 4

- Chunk ID: `342d8843e21e4a76`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `69`
- Score: `n/a `

```text
efficiently support a wide range of file sizes and access patterns, the index structure is some
form of tree.
Free space maps. File systems implement free space maps to track which storage blocks are
free and which are in use as files grow and shrink. At a minimum, a file system’s free space
map must allow the file system to find a free block when a file needs to grow, but because
spatial locality is important, most modern file systems implement free space maps that allow
them to find free blocks near a desired location. For example, many file systems implement
free space maps as bitmaps in persistent storage.
Locality heuristics. Directories and index structures allow file systems to locate desired file
```

#### Chunk 5

- Chunk ID: `514e3ae951b52afa`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `69`
- Score: `n/a `

```text
free space maps as bitmaps in persistent storage.
Locality heuristics. Directories and index structures allow file systems to locate desired file
data and metadata no matter where they are stored, and free space maps allow them to locate
the free space near any location on the persistent storage device. These mechanisms allow
file systems to employ various policies to decide where a given block of a given file should
be stored.
```

### Method C

- Retrieval latency: 0.285s
- Generation latency: 11.593s

**Answer:**

Modern file systems use **extents** and **tree-based metadata** because simple linked allocation does not scale well for performance.

In **linked allocation**—like FAT-style allocation—a file is stored as a chain of blocks. Each block points to the next one. This is simple, but it has problems:

- **Poor random access**: to find block 10,000 of a file, the file system may need to follow thousands of links.
- **Bad locality if fragmented**: consecutive file blocks may be scattered across the disk/SSD.
- **More metadata overhead**: tracking every individual block can be expensive for large files.
- **Harder to optimize layout**: the file system has less structural information about large contiguous regions.

Modern file systems improve this in two main ways.

### 1. Extents

An **extent** represents a contiguous run of blocks, for example:

> “This file uses 500 blocks starting at disk block 20,000.”

Instead of storing pointers for every block, the file system stores one record for a whole range.

This is useful because:

- large sequential files need much less metadata,
- sequential reads/writes are faster,
- spatial locality is better,
- fragmentation can be described more compactly.

This is why systems like **NTFS, ext4, and btrfs** use extents.

### 2. Tree-based metadata

A **tree-based index structure** lets the file system efficiently find the disk location for any part of a file.

Instead of walking a long linked list, the file system can search a tree with high fan-out. For example, one indirect block may contain pointers to many blocks or extents.

This gives:

- faster random access,
- better support for large files,
- fewer disk seeks,
- more flexible file layout.

So the short answer is:

> Linked allocation is simple but inefficient for large files and random access. Extents reduce metadata and improve locality, while tree-based metadata makes lookup fast and scalable.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `342d8843e21e4a76`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `69`
- Score: `0.658765 vector_distance`

```text
efficiently support a wide range of file sizes and access patterns, the index structure is some
form of tree.
Free space maps. File systems implement free space maps to track which storage blocks are
free and which are in use as files grow and shrink. At a minimum, a file system’s free space
map must allow the file system to find a free block when a file needs to grow, but because
spatial locality is important, most modern file systems implement free space maps that allow
them to find free blocks near a desired location. For example, many file systems implement
free space maps as bitmaps in persistent storage.
Locality heuristics. Directories and index structures allow file systems to locate desired file
```

#### Chunk 2

- Chunk ID: `6ff332036e3b1db3`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `85`
- Score: `0.70374 vector_distance`

```text
1. Tree structure. Each file is represented as a tree, which allows the file system to
efficiently find any block of a file.
2. High degree. The FFS tree uses internal nodes with many children compared to the
binary trees often used for in-memory data structures (i.e., internal nodes have high
degree or fan out ). For example, if a file block is 4 KB and a blockID is 4 bytes, then
each indirect block can contain pointers to 1024 bl ocks.
High degree nodes make sense for on-disk data structures where (1) we want to
minimize the number of seeks, (2) the cost of reading several kilobytes of sequential
data is not much higher than the cost of reading the first byte, and (3) data must be read
and written at least a sector at a time.
```

#### Chunk 3

- Chunk ID: `1d2f7bcd4f30e85e`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `92`
- Score: `0.747844 vector_distance`

```text
The Microsoft New Technology File System (NTFS), released in 1993, i mproved on
Microsoft’s FAT file system with many new features including new index structures to
improve performance, more flexible file metadata, improved security, and improved
reliability.
We will discuss some of NTFS’s reliability features in Chapter 14. Here, we will focus on
how NTFS stores data and metadata.
Index structures. Whereas FFS tracks file blocks with a fixed tree, NTFS and many other
recent file systems such as Linux ext4 and btrfs track extents with flexible trees.
Extents. Rather than tracking individual file blocks, NTFS tracks extents, variable-
sized regions of files that are each stored in a contiguous region on the storage device.
```

#### Chunk 4

- Chunk ID: `2bcc6fa4c5c0b72f`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `79`
- Score: `0.754631 vector_distance`

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

#### Chunk 5

- Chunk ID: `fb81bc2a59ae03a8`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `78`
- Score: `0.759311 vector_distance`

```text
random access efficiency, and it uses a collection of locality heuristics to get good
spatial locality for a wide range of workloads.
Today : In Linux, the popu lar ext2 and ext3 file systems are based on the FFS design.
NTFS. The Microsoft New Technology File System (NTFS) was introduced in the early
1990s  as a replacement for the FAT file system.
Techniques: Like FFS, NTFS uses a tree-based index structure, but the tree is more
flexible than FFS’s fixed tree. Additionally, NTFS optimizes its index structure for
sequential file layout by indexing variable-sized extents rather than individual blocks.
Today : NTFS remains the primary file system for Microsoft operating systems such as
Windows 7. In addition, the flexible tree and extent techniques are representative of
```

## q50

**Question:** If journaling makes a file system more reliable, why can a crash still leave recently written user data missing or outdated?

### Method A

- Retrieval latency: 0.862s
- Generation latency: 7.870s

**Answer:**

Because in many journaling file systems, **journaling protects metadata, not necessarily user file contents**.

A journaling file system usually records updates to things like:

- inodes
- directories
- allocation bitmaps
- indirect blocks

So after a crash, the file system can recover to a **structurally consistent state**: no half-created directory entry, no corrupted free-space map, etc.

But regular file data is often written **in place**, not fully journaled. That means if a program writes new contents to a file and the system crashes before those data blocks reach disk, the file system may recover its metadata correctly while the file contents are still:

- old,
- partially updated,
- or missing the most recent writes.

So journaling improves reliability in the sense of **file system consistency**, but it does not automatically guarantee that every recent user data write is durable or atomic.

If an application needs that guarantee, it usually has to use techniques like `fsync()`, write-to-temp-file-and-rename, or its own transaction mechanism.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `e41c96c1a83b7df0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `n/a `

```text
updates. On the other hand, updating file contents in place means that journaling file
systems provide few guarantees when a program updates a file: if a crash occurs in the
middle of the update, the file may end up in an inconsistent state with some blocks but
not others updated. If a program using a journaling file system requires atomic multi-
block updates, it needs to provide them itself.
Logging. Logging file systems simply include all updates to disk — bot h metadata and
data — in transactions.
Today, journaling file systems are common: Microsoft’s NTFS, Apple’s HFS+, and Linux’s
XFS, JFS, and ReiserFS all use journaling; and Linux’s ext3 and ext4 use journaling in their
default configurations.
```

#### Chunk 2

- Chunk ID: `bba69239998e1eb2`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `n/a `

```text
like FFS and NTFS using either journaling or logging .
Journaling. Journaling file systems apply updates to the system’s metadata via
transactions, but they update the contents of users’ files in place.
By protecting metadata updates, these systems ensure consistency of their persistent data
structures (e.g., updates to inodes, bitmaps, directories, and indirect blocks). Journaling
file systems first write metadata updates to a redo log, then commit them, and finally
write them back to their final storage locations.
Updates to the contents of regular (non-directory) files are not logged, they are applied
in place. This avoids writing file updates twice, which can be expensive for large
updates. On the other hand, updating file contents in place means that journaling file
```

#### Chunk 3

- Chunk ID: `d57bd4dc01a36980`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `n/a `

```text
edits if the machine crashes. If the application uses the file system in a straightforward way,
several of unexpected things may happen.
Poor performance. First, although file systems allow existing bytes in a file to be
overwritten with new values, they do n ot allow new bytes to be inserted into the middle
of existing bytes. So, even a small update to the file may require rewriting the entire file
either from beginning to end or at least from the point of the first insertion to the end. For
a multi-megabyte file, each auto-save may end up taking as much as a second.
Corrupt file. Second, if the application simply overwrites the existing file with updated
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
```

#### Chunk 4

- Chunk ID: `12837b37671b64d9`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `n/a `

```text
be left in an inconsistent state with, say, the new file’s inode allocated and initialized but
without an entry in the parent directory.
As discussed in Section 14.1.1 , some early file systems used ad-hoc solutions such as
carefully ordering sequences of writes and scanning the disk to detect and repair
inconsistencies when restarting after a crash. However, these approaches suffered from
complexity, slow updates, and — a s disk capacity grew — u nacceptably slow crash
recovery.
To address these problems, most modern file systems use transactions.
Traditional file systems. Transactions are added to traditional, update-in-place file systems
like FFS and NTFS using either journaling or logging .
Journaling. Journaling file systems apply updates to the system’s metadata via
```

#### Chunk 5

- Chunk ID: `7197cd7f65f98917`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `n/a `

```text
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
of the old and new versions. For example, if a section is cut from one location and
pasted in another, after a crash the saved doc ument may end up with copies of the
section in both locations, one location, or neither location; or it may end up with a
region that is a mix of the old and new text.
Lost file. Third, if instead of overwriting the document file, the application writes
updates to a new file, then deletes the original file, and finally moves the new file to the
original file’s location, an untimely crash can leave the system with no copies of the
document at all.
Programs use a range of techniques to deal with these types of issues. For example, some
```

### Method B

- Retrieval latency: 0.192s
- Generation latency: 7.794s

**Answer:**

Because journaling usually protects the **file system’s metadata**, not necessarily the **contents of regular user files**.

Metadata means things like:

- inodes
- directories
- allocation bitmaps
- indirect blocks

So after a crash, journaling helps ensure the file system is structurally consistent: no half-created inode, broken directory entry, corrupted free-space map, etc.

But in many journaling file systems, user file data is still written **in place**, not fully journaled. That means if a program writes new data to a file and the system crashes before those data blocks are actually written to disk, the file system may recover its metadata correctly while the file contents remain old, missing, or partially updated.

So journaling gives you **file system consistency**, not always **application-level data durability**.

Example:

```text
write("new contents")
crash
reboot
```

After reboot, the file system may be perfectly consistent, but the file may still contain the old contents if the new data had not reached disk.

To force stronger guarantees, programs often need to use mechanisms like `fsync()` or write data using an atomic-update pattern, depending on what guarantee they need.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `e41c96c1a83b7df0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `0.692029 vector_distance`

```text
updates. On the other hand, updating file contents in place means that journaling file
systems provide few guarantees when a program updates a file: if a crash occurs in the
middle of the update, the file may end up in an inconsistent state with some blocks but
not others updated. If a program using a journaling file system requires atomic multi-
block updates, it needs to provide them itself.
Logging. Logging file systems simply include all updates to disk — bot h metadata and
data — in transactions.
Today, journaling file systems are common: Microsoft’s NTFS, Apple’s HFS+, and Linux’s
XFS, JFS, and ReiserFS all use journaling; and Linux’s ext3 and ext4 use journaling in their
default configurations.
```

#### Chunk 2

- Chunk ID: `12837b37671b64d9`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `0.729827 vector_distance`

```text
be left in an inconsistent state with, say, the new file’s inode allocated and initialized but
without an entry in the parent directory.
As discussed in Section 14.1.1 , some early file systems used ad-hoc solutions such as
carefully ordering sequences of writes and scanning the disk to detect and repair
inconsistencies when restarting after a crash. However, these approaches suffered from
complexity, slow updates, and — a s disk capacity grew — u nacceptably slow crash
recovery.
To address these problems, most modern file systems use transactions.
Traditional file systems. Transactions are added to traditional, update-in-place file systems
like FFS and NTFS using either journaling or logging .
Journaling. Journaling file systems apply updates to the system’s metadata via
```

#### Chunk 3

- Chunk ID: `bba69239998e1eb2`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `0.773914 vector_distance`

```text
like FFS and NTFS using either journaling or logging .
Journaling. Journaling file systems apply updates to the system’s metadata via
transactions, but they update the contents of users’ files in place.
By protecting metadata updates, these systems ensure consistency of their persistent data
structures (e.g., updates to inodes, bitmaps, directories, and indirect blocks). Journaling
file systems first write metadata updates to a redo log, then commit them, and finally
write them back to their final storage locations.
Updates to the contents of regular (non-directory) files are not logged, they are applied
in place. This avoids writing file updates twice, which can be expensive for large
updates. On the other hand, updating file contents in place means that journaling file
```

#### Chunk 4

- Chunk ID: `d57bd4dc01a36980`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `0.786033 vector_distance`

```text
edits if the machine crashes. If the application uses the file system in a straightforward way,
several of unexpected things may happen.
Poor performance. First, although file systems allow existing bytes in a file to be
overwritten with new values, they do n ot allow new bytes to be inserted into the middle
of existing bytes. So, even a small update to the file may require rewriting the entire file
either from beginning to end or at least from the point of the first insertion to the end. For
a multi-megabyte file, each auto-save may end up taking as much as a second.
Corrupt file. Second, if the application simply overwrites the existing file with updated
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
```

#### Chunk 5

- Chunk ID: `7197cd7f65f98917`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `0.803373 vector_distance`

```text
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
of the old and new versions. For example, if a section is cut from one location and
pasted in another, after a crash the saved doc ument may end up with copies of the
section in both locations, one location, or neither location; or it may end up with a
region that is a mix of the old and new text.
Lost file. Third, if instead of overwriting the document file, the application writes
updates to a new file, then deletes the original file, and finally moves the new file to the
original file’s location, an untimely crash can leave the system with no copies of the
document at all.
Programs use a range of techniques to deal with these types of issues. For example, some
```

### Method C

- Retrieval latency: 0.383s
- Generation latency: 7.678s

**Answer:**

Because journaling mainly protects the **file system’s consistency**, not necessarily the **latest user data**.

A journaling file system records updates in a journal so that, after a crash, it can avoid broken metadata such as:

- an inode marked allocated but not linked from a directory
- directory entries pointing to invalid blocks
- corrupted allocation structures

But many journaling file systems journal only **metadata**, not the actual file contents. User data may still be written **in place** and may be sitting in memory buffers when the crash happens.

So after a crash:

- the file system structure is usually recoverable and consistent
- but recently written file contents may not have reached disk yet
- or only some data blocks may have been written

That means a file may still exist and look valid, but its contents may be old, missing, or partially updated.

In short:

> Journaling often guarantees that the file system is not structurally corrupted, but it does not always guarantee that recent user writes are durable.

If an application needs that guarantee, it typically must use mechanisms like `fsync()` or atomic write/rename patterns carefully.

**Retrieved chunks:**

#### Chunk 1

- Chunk ID: `e41c96c1a83b7df0`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `2.84779 rerank_score`

```text
updates. On the other hand, updating file contents in place means that journaling file
systems provide few guarantees when a program updates a file: if a crash occurs in the
middle of the update, the file may end up in an inconsistent state with some blocks but
not others updated. If a program using a journaling file system requires atomic multi-
block updates, it needs to provide them itself.
Logging. Logging file systems simply include all updates to disk — bot h metadata and
data — in transactions.
Today, journaling file systems are common: Microsoft’s NTFS, Apple’s HFS+, and Linux’s
XFS, JFS, and ReiserFS all use journaling; and Linux’s ext3 and ext4 use journaling in their
default configurations.
```

#### Chunk 2

- Chunk ID: `7197cd7f65f98917`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `20`
- Score: `2.64751 rerank_score`

```text
data, an untimely crash can leave the file in an inconsistent state, containing a mishmash
of the old and new versions. For example, if a section is cut from one location and
pasted in another, after a crash the saved doc ument may end up with copies of the
section in both locations, one location, or neither location; or it may end up with a
region that is a mix of the old and new text.
Lost file. Third, if instead of overwriting the document file, the application writes
updates to a new file, then deletes the original file, and finally moves the new file to the
original file’s location, an untimely crash can leave the system with no copies of the
document at all.
Programs use a range of techniques to deal with these types of issues. For example, some
```

#### Chunk 3

- Chunk ID: `8922ab78dc7a72b4`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `114`
- Score: `1.57957 rerank_score`

```text
it would not be highly available for writes, since new writes cannot complete if any one of
100 m achines is unavailable.
Two problems. Broadly speaking, storage systems must deal with two threats to reliability.
Operation interruption. A crash or pow er failure in the middle of a series of related
updates may leave the stored data in an inconsistent state.
For example, suppos e that a user has asked an operating system to move a file from one
directory to another: 
> mv drafts/really-important.doc final/really-important.doc
As we discussed in Chapter 13, such a move may entail many low-level operations:
writing the drafts directory file to remove really-important.doc, updating the last-
modified time of the drafts directory, growing the final directory’s file to include another
```

#### Chunk 4

- Chunk ID: `12837b37671b64d9`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `132`
- Score: `1.23394 rerank_score`

```text
be left in an inconsistent state with, say, the new file’s inode allocated and initialized but
without an entry in the parent directory.
As discussed in Section 14.1.1 , some early file systems used ad-hoc solutions such as
carefully ordering sequences of writes and scanning the disk to detect and repair
inconsistencies when restarting after a crash. However, these approaches suffered from
complexity, slow updates, and — a s disk capacity grew — u nacceptably slow crash
recovery.
To address these problems, most modern file systems use transactions.
Traditional file systems. Transactions are added to traditional, update-in-place file systems
like FFS and NTFS using either journaling or logging .
Journaling. Journaling file systems apply updates to the system’s metadata via
```

#### Chunk 5

- Chunk ID: `df4f1478d77c895b`
- Source: `7471777c6ab64544bbe6287888908b95_OS_Principles_Practice_Vol_4.pdf`
- Page: `68`
- Score: `1.0382 rerank_score`

```text
file systems must be jacks-of-all-trades. They would be less useful if we had to use one
file system for large sequentially-read files, another for small seldom-written files,
another for large random-access files, another for short-lived files, and so on.
Persistence. File systems must maintain and update both user data and their internal
data structures on persistent storage devices so that everything survives operating system
crashes and pow er failures.
Reliability. File systems must be able to store important data for long periods of time,
even if machines crash during updates or some of the system’s storage hardware
malfunctions.
```
