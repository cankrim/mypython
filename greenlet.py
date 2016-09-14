import gevent.monkey
gevent.monkey.patch_all(thread=False, select=False, aggressive=False)
from gevent.pool import Pool as gPool

def wrap_func(map_func, x):
    return (x, map_func(x))


def multigreenlet_map(func, *args, **kwargs):
    """
    A method to parallelize mappable, IO-bound functions
    """
    num_greenlets = kwargs.pop('num_greenlets', 10)

    pool = gPool(num_greenlets)

    result = pool.map(func, *args)

    return result
