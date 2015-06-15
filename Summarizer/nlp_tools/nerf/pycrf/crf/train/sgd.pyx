# encoding: utf-8

import random
from math import ceil
from threading import Thread
from Queue import Queue

from crf.array cimport DArray

from crf.model cimport Model
from crf.data.connsbuf cimport ConnsBuf
from crf.data.auxdata cimport AuxData
from crf.data.dataset import obtypes as number_of_obtypes
# from crf.train.gradient cimport GradientWrapper
# from crf.train.gradient import count_gradient
from crf.train.gradient import add_expected_numbers

GLOBAL_NUMS = False

class Worker(Thread):

    """Thread executing tasks from a given tasks queue"""
    
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: 
                func(*args, **kargs)
            except Exception, e:
                print e
            self.tasks.task_done()

class ThreadPool:

    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

#def update_model(Model model, gradients, double scale, int p, int q):
#    cdef GradientWrapper gwrapper
#    cdef double* gradient
#    cdef int k
#    for gwrapper in gradients:
#        gradient = gwrapper.gradient
#        with nogil:
#            # for k from 0 <= k < model.pn:
#            for k from p <= k < q:
#                model.model.values[k] -= gradient[k] * scale

def clear_numbers(DArray numbers_wrapper):
    cdef int k
    with nogil:
        for k from 0 <= k < numbers_wrapper.size:
            numbers_wrapper.array[k] = 0.0

def do_add_expected_numbers(sent, model, nums_queue):
    numbers, connsbuf = nums_queue.get()
    add_expected_numbers(sent, numbers, model, connsbuf)
    nums_queue.put((numbers, connsbuf))

def collect_part(DArray numbers_wrapper, arrays, int p, int q):
    cdef int k
    cdef double* add_num
    cdef double* numbers = numbers_wrapper.array
    for array in arrays:
        add_num = (<DArray>array).array
        with nogil:
            for k from p <= k < q:
                numbers[k] += add_num[k]

def update_part(Model model, DArray numbers_wrapper, AuxData auxdata,
        double i_var2, double coef, double scale, int p, int q):
    cdef int i, fn
    cdef double val, partial_deriv
    cdef double* num
    cdef double* values = model.model.values
    cdef double* numbers = numbers_wrapper.array
    cdef bint global_nums = GLOBAL_NUMS
    with nogil:
        for i from p <= i < q:
            val = values[i]
            fn = auxdata.fnum[i]
            if global_nums:
                partial_deriv = numbers[i] - (fn + val*i_var2)*coef
            else:
                partial_deriv = numbers[i] - fn - val*i_var2*coef
            values[i] -= partial_deriv * scale

#def run_parallel(fun, workers, model, args):
#    wlist = []
#    for j in range(workers):
#        p = int((float(j) / workers) * model.pn)
#        q = int((float(j + 1) / workers) * model.pn)
#        worker = Thread(target=fun,
#                args=args + (p, q))
#        worker.start()
#        wlist.append(worker)
#    for j in range(workers):
#        wlist[j].join()
#
#def expected_numbers_and_cll(batch, DArray gradient_wrapper, Model model,
#        AuxData auxdata, ConnsBuf connsbuf, double i_var2, double coef):
#    z_stats = expected_numbers(batch, gradient_wrapper, model, connsbuf)
#    print "cll:", model.cll(batch, z_stats, coef, i_var2)

def _true(x):
    return True

def sgd(Model model, data, iter_num, regvar=4.0, batch_size=30,
        scale0=0.01, tau=10.0, workers=1, callback=_true,
        verbose=False):
    """
    Run Stochastic Gradient Descent method with given model on given data.

    :params:
    --------
    iter_num : int
        Number of iterations to perform (on the entire data set).
    callback : () -> bool function
        Callback function to run after each iteration. Stop training process,
        if callback returns False.
    workers : int
        Number of used additional threads.
    """
    i_var2 = 1.0 / (regvar ** 2)

    if verbose:
        print ""
        print " *** Start SGD method ***"
        print ""
        print "Regularization variance:", regvar
        print "Iterations:", iter_num
        print "Batch size:", batch_size
        print "Scale0:", scale0
        print "Tau:", tau
        print ""

    cdef AuxData auxdata = AuxData(data, model)
    coef = float(batch_size) / len(data)

    # obtypes = max([len(word) for sent, _ in data for word in sent])
    obtypes = number_of_obtypes(data)
    numbers = [DArray(model.pn) for i in range(workers)]
    connsbufs = [ConnsBuf(model.yn, obtypes) for i in range(workers)]
    nums_queue = Queue()
    for elem in zip(numbers, connsbufs):
        nums_queue.put(elem)

    pool = ThreadPool(workers)

    iter_done = 0.0
    while iter_done < iter_num: 
        wlist = []

        # Setting values in numbers to 0
        for i in range(workers):
            pool.add_task(clear_numbers, numbers[i])
        pool.wait_completion()

        batch = [random.choice(data) for _ in range(batch_size)]

        # Count real number of features
        if not GLOBAL_NUMS:
            auxdata = AuxData(batch, model)

        # Count expected numbers of features
        for sent, _ in batch:
            pool.add_task(do_add_expected_numbers, sent, model, nums_queue)
        pool.wait_completion()

        # NOTE: changed scale behaviour to expotential with respect
        # to the number of iterations.
        scale = (scale0 * tau) / (tau + iter_done)
        # scale = scale0 * (2.0 ** (-iter_done / tau))
        # print scale

        # Collecting expected numbers in num1 array
        for i in range(workers):
            p = int((float(i) / workers) * model.pn)
            q = int((float(i + 1) / workers) * model.pn)
            pool.add_task(collect_part, numbers[0], numbers[1:], p, q)
        pool.wait_completion()

        # Update model with respect to expected numbers
        for i in range(workers):
            p = int((float(i) / workers) * model.pn)
            q = int((float(i + 1) / workers) * model.pn)
            pool.add_task(update_part, model, numbers[0],
                    auxdata, i_var2, coef, scale, p, q)
        pool.wait_completion()

        iter_done += float(batch_size) / len(data)
        callback(iter_done)

    if verbose:
        print ""
        print " *** End SGD method ***"
        print ""

#def sgd(Model model, data, iter_num, regvar=4.0, batch_size=30,
#        scale0=0.01, tau=None, workers=1, callback=lambda _: True,
#        verbose=False):
#    """
#    Run Stochastic Gradient Descent method with given model on given data.
#
#    :params:
#    --------
#    iter_num : int
#        Number of iterations to perform (on the entire data set).
#    callback : () -> bool function
#        Callback function to run after each iteration. Stop training process,
#        if callback returns False.
#    workers : int
#        Number of used additional threads.
#    """
#    if tau is None:
#        # setting tau to default value
#        tau = 10.0
#    i_var2 = 1.0 / (regvar ** 2)
#
#    # Rounding batch_size
#    package_size = int(ceil(float(batch_size) / workers))
#    batch_size = package_size * workers
#
#    if verbose:
#        print ""
#        print " *** Start SGD method ***"
#        print ""
#        print "Regularization variance:", regvar
#        print "Iterations:", iter_num
#        print "Batch size:", batch_size
#        print "Scale0:", scale0
#        print "Tau:", tau
#        print ""
#    
#    cdef AuxData auxdata = AuxData(data, model)
#
#    coef = float(batch_size) / len(data)
#    obtypes = max([len(word) for sent, _ in data for word in sent])
#    numbers = [DArray(model.pn) for i in range(workers)]
#    connsbufs = [ConnsBuf(model.yn, obtypes) for i in range(workers)]
#
#    iter_done = 0.0
#    while iter_done < iter_num: 
#        wlist = []
#
#        # Main worker, which prints conditional log likelihood (if verbose)
#        package = [random.choice(data) for i in range(package_size)]
#        if verbose:
#            main_worker = Thread(target=expected_numbers_and_cll,
#                    args=(package, numbers[0], model, auxdata, connsbufs[0],
#                        i_var2, coef))
#        else:
#            main_worker = Thread(target=expected_numbers,
#                    args=(package, numbers[0], model, connsbufs[0]))
#        main_worker.start()
#
#        # Other workers, counting only expected numbers of features
#        for j in range(1, workers):
#            package = [random.choice(data) for i in range(package_size)]
#            worker = Thread(target=expected_numbers,
#                    args=(package, numbers[j], model, connsbufs[j]))
#            worker.start()
#            wlist.append(worker)
#
#        # Joining workers
#        for worker in wlist:
#            worker.join()
#        main_worker.join()
#
#        scale = (scale0 * tau) / (tau + iter_done)
#
#        # Collecting expected numbers in num1 array
#        run_parallel(collect_part, workers, model, 
#                args=(numbers[0], numbers[1:]))
#
#        # Update model with respect to expected numbers
#        run_parallel(update_part, workers, model,
#                args=(model, numbers[0], auxdata, i_var2, coef, scale))
#
#        # prev_iter_done = iter_done
#        iter_done += float(batch_size) / len(data)
#        # if int(iter_done) > int(prev_iter_done):
#        #     callback(int(iter_done))
#        callback(iter_done)
#
#    if verbose:
#        print ""
#        print " *** End SGD method ***"
#        print ""
#    # return model
