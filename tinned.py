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


class header:
    def __init__(self, header_name):
        pass

class function:
    def __init__(self, cc, signature, headers = None, libs = None):
        (result_type, func_name, args) = self.parse_signature(signature)

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

        print s
        return s

    def parse_signature(self, signature):
        type_and_name = re.compile('([A-Za-z_][A-Za-z_0-9]*\*?)\s([A-Za-z_][A-Za-z_0-9]*)\((.*)\)')

        match = type_and_name.match(signature)

        if match:
            print match.group(1)
            print match.group(2)
            print [s.strip() for s in match.group(3).split(',')]

        return ('int', 'gettimeofday',
                [('struct timeval*', 'tv', 'NULL'), ('struct timezone*', 'tz', 'NULL')])
