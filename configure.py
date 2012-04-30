#!/usr/bin/python

import tinned
import sys
import logging

logging.basicConfig(stream = sys.stdout,
                    format = '%(levelname) 7s: %(message)s')

#logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)


env = tinned.build_environment()

dlopen = tinned.function(env, 'void* dlopen(const char* filename, int flag = RTLD_LAZY)',
                         headers=['dlfcn.h'], maybe_libs=['dl'])

if dlopen.works():
    print dlopen.tag()
    logging.info("Dlopen works, required libs: " + ' '.join(dlopen.required_libs()))

zlib = tinned.function(env, 'int deflateInit(z_streamp stream, int level)',
                       headers=['zlib.h'], libs=['z'], tag='zlib')
if zlib.works():
    print zlib.tag()
    logging.info('zlib exists')

gmp = tinned.function(env,
       'void* mpz_export(void* rop, size_t* countp, int order, size_t size, int endian, size_t nails, mpz_t op)',
                      headers=['gmp.h'], libs=['gmp'], tag='gmp')
if gmp.works():
    print gmp.tag()
    logging.info('gmp mpz_export exists')

gettimeofday = tinned.function(env,
    'int gettimeofday(struct timeval* tv = NULL, struct timezone* tz = NULL)',
    headers=['sys/time.h'])

if gettimeofday.works():
    print gettimeofday.tag()
    logging.info('have gettimeofday')

#if __name__ == '__main__':
#    sys.exit(main())
