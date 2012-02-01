"""
Tinned configurations
"""

import subprocess
import logging
import re
import os
import tempfile
import jinja2

class build_environment:
    def __init__(self, ok_with = []):
        self.compiler_name = 'g++'
        self.compiler_version = '4.5.3'

    def spawn_compile(self, input_file, output_file, libs = None):
        if libs is None:
            libs = []

        link_lines = ['-l%s' % (lib) for lib in libs] if len(libs) > 0 else []

        return subprocess.Popen([self.compiler_name, input_file, '-o', output_file] + link_lines,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)


class headers:
    def __init__(self, *args):
        self.results = {}
        for arg in args:
            self.results[arg] = False

    def __getitem__(self, name):
        try:
            return self.results[name]
        except KeyError:
            raise KeyError('Header ' + name + ' not tested')

class function:
    def __init__(self, cc, signature, headers = None, libs = None):
        sig_info = self.parse_signature(signature)
        result_type = sig_info[0]
        func_name = sig_info[1]
        args = sig_info[2:]

        self.signature = signature
        self.result = None

        self.test_src = self.form_test_source(result_type, func_name, args, headers)

        tmpfile = tempfile.NamedTemporaryFile(prefix='tinned_', suffix='.c', delete=False)

        tmpfile.write(self.test_src)
        tmpfile.close()

        self.tmpfile_name = tmpfile.name
        self.tmpexe_name = self.tmpfile_name + '.exe'

        self.proc = cc.spawn_compile(self.tmpfile_name, self.tmpexe_name, libs)

    def __del__(self):
        try:
            os.remove(self.tmpfile_name)
        except OSError:
            pass

        try:
            os.remove(self.tmpexe_name)
        except OSError:
            pass

    def works(self):
        if self.result is None:
            (stdoutdata, stderrdata) = self.proc.communicate()
            if self.proc.returncode != 0:
                print stderrdata
                #logging.debug("Testing %s failed - %s" % (self.signature, stderrdata))
                self.result = False
            else:
                self.result = True

        return self.result

    def form_test_source(self, result_type, func_name, func_args, headers):
        s = ''

        for header in headers:
            s += '#include <%s>\n' % (header)
        s += '#include <stddef.h>\n' # for NULL mostly

        s += '\nint main() {\n'

        for (arg_type,arg_name,arg_default) in func_args:
            if arg_default != None:
                s += '   %s %s = %s;\n' % (arg_type, arg_name, arg_default)
            else:
                s += '   %s %s;\n' % (arg_type, arg_name)

        if result_type != 'void':
            s += '   ' + result_type + ' result = ';
        s += func_name + '(' + ', '.join([a[1] for a in func_args]) + ');\n'

        s += '   return 0;\n'
        s += '}\n'

        return s

    def parse_signature(self, signature):

        def c_lex(signature):

            accum = ''

            for c in signature:

                if c in ('(', ')', ',', ' '):
                    if accum != '':
                        yield accum
                        accum = ''
                    if c != ' ':
                        yield c
                else:
                    accum += c

            if c != ' ':
                yield accum

        tok_gen = c_lex(signature)

        # return type and signature
        results = [tok_gen.next(), tok_gen.next()]

        assert tok_gen.next() == '('

        accum = []
        for tok in tok_gen:
            if tok in (',', ')'):

                def_value = None

                if '=' in accum:
                    eq = accum.index('=')
                    def_value = ' '.join(accum[eq+1:])
                    accum = accum[:eq]

                assert len(accum) >= 2
                results.append((' '.join(accum[:-1]), accum[-1], def_value))
                accum = []
            else:
                accum.append(tok)

        return results
