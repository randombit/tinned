#!/usr/bin/python

import tinned
import sys

env = tinned.build_environment()

"""
dlopen = tinned.function('void* dlopen(const char* filename, int flag = RTLD_LAZY)',
                         headers='dlcfn.h', possible_libs='dl')

if dlopen.works():
    print dlopen.needed_libs
"""

gettimeofday = tinned.function(env,
    'int gettimeofday(struct timeval* tv = NULL, struct timezone* tz = NULL)',
    headers=['sys/time.h'])

if gettimeofday.works():
    print "yay!"
else:
    print "sad"

#if __name__ == '__main__':
#    sys.exit(main())
