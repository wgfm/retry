'''
Module for easy retries in Python.

All intervals are in milliseconds
'''
import abc
import math
import random
import time


MILLIS_PER_SEC = 1000
MAX_ATTEMPTS = 10


def make_jitterer(spread=0.01, rng=random):
    def jitter(interval):
        '''Applies some random jitter'''
        if not 0 < spread < 1:
            raise ArgumentError('Jitter spread should be between 0 and 1')

        # Skip random number generation when there's no spread
        if spread == 0:
            return interval
        rand_number = rng.random()*2 - 1
        return interval + rand_number * interval * spread

    def no_jitter(interval):
        return interval

    if spread == 0:
        return no_jitter
    else:
        return jitter


class OperationFailed(Exception):
    '''Thrown if all retries failed.

    Will carry a list of all the caught exceptions
    '''

    def __init__(self, reasons=None, *args, **kwargs):
        self.reasons = reasons
        super().__init__(*args, **kwargs)


class Strategy(abc.ABC):

    def __init__(self, max_attempts=MAX_ATTEMPTS, jitter_spread=None):
        if jitter_spread is None:
          jitter_spread = 0
        self.max_attempts = max_attempts
        self.attempt = 0
        self.jitter = make_jitterer(jitter_spread)
        self.exceptions = []

    @abc.abstractmethod
    def next():
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.attempt < self.max_attempts:
            self.attempt += 1
            interval = self.next()
            return interval + self.jitter(interval)
        else:
            raise StopIteration()


class Backoff(Strategy):
    '''Implements an exponential backoff strategy'''

    def __init__(self,
                 start_interval=1,
                 max_interval=60,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.start_interval = start_interval
        self.max_interval = float(max_interval)
        self.next_interval = self.start_interval

    def next(self):
        if self.next_interval < self.max_interval:
            self.next_interval = math.pow(2, self.attempt) * self.start_interval
        return min([self.next_interval, self.max_interval])


class Linear(Strategy):
    def __init__(self, interval=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = interval

    def next(self):
        return self.interval


def retry(strategy=Linear, exception=Exception, *retry_args, **retry_kwargs):
    def decorate(func):
        def func_wrapper(*func_args, **func_kwargs):
            strat = strategy(*retry_args, **retry_kwargs)
            exceptions = []
            successful = False
            for interval in strat:
                try:
                    func(*func_args, **func_kwargs)
                except exception:
                    strat.exceptions.append(exception)
                    time.sleep(interval)
                    continue
                else:
                    successful = True
                    break
            if not successful:
                raise OperationFailed(reasons=strategy.exceptions)
        return func_wrapper
    return decorate
