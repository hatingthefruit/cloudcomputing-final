#!/usr/bin/env python

#mpiexec -mca btl ^openib --hostfile ../mpihosts -display-map -n 4 python -m mpi4py img_search.py ./all_images/google.png

import os, sys

DEFAULT_THREADS = 4
MCA_ARG = "-mca btl ^openib"
SEARCH_SCRIPT = "img_search.py"
MODULES = "-m mpi4py"
PYTHON_NAME = "python"
OTHER_OPTIONS = "-display-map"


if __name__ == "__main__":
    num_threads = DEFAULT_THREADS
    if len(sys.argv) < 2:
        print("""Usage:\n %s FILENAME [threads] \n\nSearches for the file indicated by FILENAME on all hosts in the MPI cluster, using a parallel lookup. Optionally, you can specify the total number of threads using the optional [threads] argument.""" % sys.argv[0])
        exit(1)
    elif len(sys.argv) >= 3:
        try:
            num_threads = int(sys.argv[2])
        except:
            print("Value for number of threads does not appear to be a valid integer. Defaulting to %d threads" % (DEFAULT_THREADS))

    thread_arg = '-n %d' %(num_threads)
    mpiargs = "mpiexec"

    if os.path.isfile("../mpihosts"):
        hostpath = "--hostfile ../mpihosts"
    elif os.path.isfile("mpihosts"):
        hostpath = '--hostfile mpihosts'
    else:
        hostpath = '--host localhost'

    if not os.path.isfile(sys.argv[1]):
        print("%s is not a valid file to search." % (sys.argv[1]))
        exit(1)

    try:
        import mpi4py
    except:
        print("mpi4py module does not appear to be installed. Please check setup.")
        exit(1)

    command = " ".join([mpiargs, MCA_ARG, hostpath, OTHER_OPTIONS, thread_arg, PYTHON_NAME, MODULES, SEARCH_SCRIPT, sys.argv[1]])
    print("Running command:")
    print(command)
    os.system(command)
    
    
