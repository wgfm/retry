# Retry

This is a simple Python library for retries on failure.

## Usage

Retry is built with flexibility and simplicity in mind. Different retry
strategies can be used, as shown below.

`retry` decorates a function that may fail. If decorated, the function will be
rerun until the maximum number of attempts is reached (10 by default). When out
of attempts, an `OperationFailed` will be raised, with all thrown exceptions
attached as `reasons`:

```python
from retry import retry, OperationFailed

try:
    @retry()
    def always_errors():
        raise Exception('Uh oh...')
except OperationFailed as e:
    print(e.reasons)
```

### Linear retry interval

By default, retry uses a linear strategy: The code that threw the error is
retried at a fixed interval.

```python
import random
from retry import retry

@retry()
def error_prone():
    if random.random() > 0.7:
        raise Exception('I don't work very well')

error_prone()
```

### Exponential backoff retry

```python
import random
from retry import retry, Backoff

@retry(strategy=Backoff)
def error_prone():
    if random.random() > 0.7:
        raise Exception('I don't work very well')

error_prone()
```

## Catching specific exceptions

By default, all exceptions will be caught. You can choose to only catch
exceptions by using the `exception` kwarg:

```python
from retry import retry

class Unrepairable(Exception):
    pass

class Repairable(Exception):
    pass

@retry(exception=Repairable)
def error_prone():
    raise Unrepairable() # Will not be caught by retry
```


## Strategies

`retry()` can take an optional `strategy` kwarg. This is a class that determines
the retry intervals. Apart from the `exception` kwarg, any additional args and
kwargs are arguments to the strategy constructor.

All strategies should be subclasses of `retry.Strategy`, which enables the
following options:

- `max_attempts`: The number of attempts the function needs to be retried.
  Defaults to 10.
- `jitter_spread`: See Jitter for more details.

### Linear

The linear strategy is the simplest. It can take one option:

- `interval`: The retry interval in seconds. This interval is fixed. Default: 1

### Backoff

The exponential backoff strategy is often useful for retrying connectivity
problems. It will double its interval with every try, until a set (or default)
maximum is reached. `retry.Backoff` takes several options:

- `start_interval`: The interval to begin with. Default: 1
- `max_interval`: The maximum interval length. Default: 1

### Roll your own stragegy

If the supplied strategies don't suffice, you can define your own strategy by
subclassing `retry.Strategy`. You need to define the `next(self)` method, which
will give the next interval in seconds.

The subclass should also pass `*args` and `**kwargs` to the superclass in
`__init__`.

## Jitter

If several processes failing at the same time, it is sometimes helpful to
introduce a little bit of randomness. Otherwise, systems can be flooded with
a lot of simultanous requests, which may result in unstable situations.

This randomness is called 'jitter'. By default, jitter is disabled, but it's
simple to enable through the `jitter_spread` option. Turning on jitter will
cause the interval to be calculated as:

```python
jittered_interval = interval + interval * spread * random_number
```

This random number is a number between -1 and 1.

A jitter_spread between 0 and 1 is enforced.
