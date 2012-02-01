#!/usr/bin/python

import tinned
import sys

env = tinned.build_environment()

dlopen = tinned.function(env, 'void* dlopen(const char* filename, int flag = RTLD_LAZY)',
                         headers=['dlfcn.h'], libs=['dl'])

if dlopen.works():
    print "dlopen works"

headers = tinned.headers('sys/time.h', 'time.h', 'asio.hpp')

#print headers['sys/time.h']

gettimeofday = tinned.function(env,
    'int gettimeofday(struct timeval* tv = NULL, struct timezone* tz = NULL)',
    headers=['sys/time.h'])

if gettimeofday.works():
    print "yay!"
else:
    print "sad"

#if __name__ == '__main__':
#    sys.exit(main())
