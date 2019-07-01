import multiprocessing

class rw_lock:
    def __init__(self):
        self.counter = multiprocessing.Value('i', 0)
        self.cond = multiprocessing.Condition(lock=self.counter.get_lock())

    def down_read(self):
        with self.counter.get_lock():
            self.counter.value += 1
            
    def up_read(self):
        with self.counter.get_lock():
            self.counter.value -= 1

            if self.counter.value == 0:
                self.cond.notify()

    def down_write(self):
        lock = self.counter.get_lock()
        lock.acquire()
                
        self.cond.acquire()
        while self.counter.value != 0:
            self.cond.wait()

    def up_write(self):
        lock = self.counter.get_lock()
        self.cond.notify()
        self.cond.release()
        lock.release()

import time
import numpy as np

def writer(lock, value):
    time.sleep(abs(np.random.randn()) / 200)

    lock.down_write()

    print(f"value is {value.value}")

    value.value += 5

    lock.up_write()

def reader(lock, value):
    time.sleep(abs(np.random.randn())/ 200) 
    lock.down_read()
    print(value.value)
    lock.up_read()

if __name__ == "__main__":
    procs = []
    lock = rw_lock()
    i = multiprocessing.Value('i', 0, lock=None)

    for _ in range(20):
        procs.append(multiprocessing.Process(target=reader, args=(lock, i)))
        procs.append(multiprocessing.Process(target=writer, args=(lock, i)))

    for proc in procs:
        proc.start()

    for proc in procs:
        proc.join()