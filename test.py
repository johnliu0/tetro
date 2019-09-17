from time import perf_counter
from math import sqrt
from random import random
from multiprocessing import Pool

def f(x):
    return sqrt(x / random())

if __name__ == '__main__':
    start_time = perf_counter()
    with Pool(2) as p:
        p.map(f, [i for i in range(10000000)])
    print(perf_counter() - start_time)

    start_time = perf_counter()
    with Pool(3) as p:
        p.map(f, [i for i in range(10000000)])
    print(perf_counter() - start_time)

    start_time = perf_counter()
    with Pool(4) as p:
        p.map(f, [i for i in range(10000000)])
    print(perf_counter() - start_time)

    start_time = perf_counter()
    with Pool(5) as p:
        p.map(f, [i for i in range(10000000)])
    print(perf_counter() - start_time)

    start_time = perf_counter()
    with Pool(6) as p:
        p.map(f, [i for i in range(10000000)])
    print(perf_counter() - start_time)
