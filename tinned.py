"""
Tinned configurations
(C) 2012 Jack Lloyd

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import subprocess
import logging
import re
import os
import tempfile
import jinja2
import multiprocessing

class build_environment:
    def __init__(self, ok_with = []):
        self.compiler_name = 'g++'
        self.compiler_version = '4.5.3'

    class compilation_process:
        def __init__(self, cmdline, tmp_input, tmp_output, process):
            self.cmdline = cmdline
            self.tmp_input = tmp_input
            self.tmp_output = tmp_output
            self.proc = process
            self.result = None

        def works(self):
            if self.result is None:
                (stdoutdata, stderrdata) = self.proc.communicate()
                if self.proc.returncode != 0:
                    logging.debug("Compilation failed: " + stderrdata)
                    self.result = False
                else:
                    self.result = True

            return self.result

        def communicate(self):
            (stdout,stderr) = self.proc.communicate()
            self.returncode = self.proc.returncode
            return (stdout, stderr)

        def __del__(self):
            try:
                os.remove(self.tmp_input)
            except OSError, e:
                logging.debug('Removing %s failed - %s' % (self.tmp_input, e))

            try:
                os.remove(self.tmp_output)
            except OSError, e:
                logging.debug('Removing %s failed - %s' % (self.tmp_output, e))

    def begin_test(self, full_link, test_src, libs = None):
        input_file = tempfile.NamedTemporaryFile(prefix='tinned_', suffix='.c', delete=False)
        input_file.write(test_src)

        input_file.close()

        if libs is None:
            libs = []

        link_lines = ['-l%s' % (lib) for lib in libs] if len(libs) > 0 else []

        cmdline = []

        if full_link:
            output_file = input_file.name + '.exe'
            cmdline = [self.compiler_name, input_file.name, '-o', output_file] + link_lines
        else:
            output_file = input_file.name + '.o'
            cmdline = [self.compiler_name, '-c', input_file.name, '-o', output_file]

        logging.debug("Starting command %s" % (' '.join(cmdline)))

        proc = subprocess.Popen(cmdline,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        return self.compilation_process(cmdline, input_file.name, output_file, proc)

def form_test_source(result_type, func_name, func_args, headers):
    s = ''

    if headers:
        for header in headers:
            s += '#include <%s>\n' % (header)
    s += '#include <stddef.h>\n' # for NULL mostly

    s += '\nint main() {\n'

    if func_name != None:
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

class function:
    def __init__(self, env, signature, headers = None, libs = None, maybe_libs = None, tag = None):
        sig_info = self.parse_signature(signature)
        result_type = sig_info[0]
        func_name = sig_info[1]
        args = sig_info[2:]

        if tag:
            self.tag_name = tag
        else:
            self.tag_name = func_name

        if libs is None:
            libs = []
        if maybe_libs is None:
            maybe_libs = []

        self.signature = signature
        self.result = None

        test_src = form_test_source(result_type, func_name, args, headers)

        self.libs_required = libs
        self.libs_maybe = maybe_libs

        self.test = env.begin_test(True, test_src, self.libs_required)

        if len(maybe_libs) > 0:
            self.maybe_libs_test = env.begin_test(True, test_src,
                                                  self.libs_required + self.libs_maybe)
        else:
            self.maybe_libs_test = None

    def works(self):
        if self.test.works():
            return True

        if self.maybe_libs_test is not None:
            return self.maybe_libs_test.works()

        return False

    def tag(self):
        return self.tag_name

    def required_libs(self):
        if self.test.works():
            return self.libs_required

        if self.maybe_libs_test is not None:
            if self.maybe_libs_test.works():
                return self.libs_required + self.libs_maybe

        return []

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
