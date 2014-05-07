'''
There are a lot of fancier things we can do here.
A good thing to do would be to keep similar function calls
and use multiprocessing.Queues for the backend.
This way we can print out progress.
'''
from __future__ import absolute_import, division, print_function
import multiprocessing
import atexit
import sys
import signal
from .util_progress import progress_func
from .util_time import tic, toc
from . import util_arg


QUIET   = util_arg.QUIET
VERBOSE = util_arg.VERBOSE
__POOL__ = None
__TIME__ = '--time' in sys.argv


def get_default_numprocs():
    num_procs = max(multiprocessing.cpu_count() - 2, 1)
    #num_procs = 1
    return num_procs


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def init_pool(num_procs=None, maxtasksperchild=None):
    global __POOL__
    if num_procs is None:
        # Get number of cpu cores
        num_procs = get_default_numprocs()
    if not QUIET and VERBOSE:
        print('[parallel] initializing pool with %d processes' % num_procs)
    if num_procs == 1:
        if VERBOSE:
            print('[parallel] num_procs=1, Will process in serial')
        __POOL__ = 1
        return
    if '--strict' in sys.argv:
        #assert __POOL__ is None, 'pool is a singleton. can only initialize once'
        assert multiprocessing.current_process().name, 'can only initialize from main process'
    if __POOL__ is not None:
        print('close pool before reinitializing')
        return
    # Create the pool of processes
    __POOL__ = multiprocessing.Pool(processes=num_procs, initializer=init_worker,
                                    maxtasksperchild=maxtasksperchild)
    #for key, val in __POOL__.__dict__.iteritems():
        #print('%s = %r' % (key, val))


def close_pool():
    global __POOL__
    if __POOL__ is not None:
        if not QUIET and VERBOSE:
            print('[parallel] closing pool')
        if not isinstance(__POOL__, int):
            # Must join after close to avoid runtime errors
            __POOL__.close()
            __POOL__.join()
        __POOL__ = None


def _process_serial(func, args_list, args_dict={}):
    num_tasks = len(args_list)
    result_list = []
    mark_prog, end_prog = progress_func(max_val=num_tasks,
                                        lbl=func.func_name + ': ')
    mark_prog(0)
    # Execute each task sequentially
    for count, args in enumerate(args_list):
        result = func(*args, **args_dict)
        result_list.append(result)
        mark_prog(count)
    end_prog()
    return result_list


def _process_parallel(func, args_list, args_dict={}):
    # Define progress observers
    num_tasks = len(args_list)
    num_tasks_returned_ptr = [0]
    mark_prog, end_prog = progress_func(max_val=num_tasks,
                                        lbl=func.func_name + ': ')
    def _callback(result):
        mark_prog(num_tasks_returned_ptr[0])
        sys.stdout.flush()
        num_tasks_returned_ptr[0] += 1
    # Send all tasks to be executed asynconously
    apply_results = [__POOL__.apply_async(func, args, args_dict, _callback)
                     for args in args_list]
    # Wait until all tasks have been processed
    while num_tasks_returned_ptr[0] < num_tasks:
        #print('Waiting: ' + str(num_tasks_returned_ptr[0]) + '/' + str(num_tasks))
        pass
    end_prog()
    # Get the results
    result_list = [ap.get() for ap in apply_results]
    return result_list


def generate(func, args_list, force_serial=False):
    try:
        assert __POOL__ is not None, 'must init_pool() first'
    except AssertionError:
        init_pool()
    num_tasks = len(args_list)
    mark_prog, end_prog = progress_func(max_val=num_tasks, lbl=func.func_name + ': ')
    args_list
    if __TIME__:
        tt = tic(func.func_name)
    if isinstance(__POOL__, int) or force_serial:
        print('[parallel] executing %d %s tasks in serial' %
              (len(args_list), func.func_name))
        for count, args in enumerate(args_list):
            mark_prog(count)
            result = func(args)
            yield result
    else:
        print('[parallel] executing %d %s tasks using %d processes' %
              (len(args_list), func.func_name, __POOL__._processes))
        for count, result in enumerate(__POOL__.imap_unordered(func, args_list)):
            mark_prog(count)
            yield result
    if __TIME__:
        toc(tt)
    end_prog()


def process(func, args_list, args_dict={}, force_serial=False):
    assert __POOL__ is not None, 'must init_pool() first'
    if __POOL__ == 1 or force_serial:
        if not QUIET:
            print('[parallel] executing %d %s tasks in serial' %
                  (len(args_list), func.func_name))
        result_list = _process_serial(func, args_list, args_dict)
    else:
        print('[parallel] executing %d %s tasks using %d processes' %
              (len(args_list), func.func_name, __POOL__._processes))
        result_list = _process_parallel(func, args_list, args_dict)
    return result_list

atexit.register(close_pool)
