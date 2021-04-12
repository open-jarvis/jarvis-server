"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
import time
import shutil


FILENAME = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/../logs/trace.log"   # specify trace file
FILE = open(FILENAME, "a+")   # open trace file
MAX_ALLOWED_FILE_SIZE = 1024 * 1024 * 100   # in bytes, so 100 MB
ONLY_JARVIS = True   # only trace jarvis functions and files


def tracer(frame, event, arg):
    global ONLY_JARVIS
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    line_no = frame.f_lineno
    filename = co.co_filename
    if ONLY_JARVIS and "jarvis" not in filename:
        return tracer
    if event == 'call':
        fn_args = []
        for i in range(frame.f_code.co_argcount):
            name = frame.f_code.co_varnames[i]
            fn_args.append(f"{name}={frame.f_locals[name]}")
        insert_trace("call", filename, f"{func_name}({', '.join(fn_args)})", line_no)
        return tracer
    elif event == 'return':
        insert_trace("return", filename, func_name, arg)
    elif event == 'exception':
        co = frame.f_code
        func_name = co.co_name
        line_no = frame.f_lineno
        filename = co.co_filename
        exc_type, exc_value, exc_traceback = arg
        insert_trace("exception", exc_type.__name__, exc_value, filename, func_name, line_no, exc_traceback)
    return

def insert_trace(*args):
    global FILE, FILENAME, MAX_ALLOWED_FILE_SIZE
    FILE.write(f"{int(time.time())}::{'::'.join([str(i) for i in args])}\n")
    if os.path.getsize(FILENAME) > MAX_ALLOWED_FILE_SIZE:
        shutil.make_archive(FILENAME + "." + str(int(time.time())), "gztar", FILENAME, ".")
