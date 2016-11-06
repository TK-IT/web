import re
import os
import json
import argparse
import functools
import subprocess

import dukpy
import dukpy.babel


def await_changes(filename, events=()):
    dir, name = os.path.split(filename)
    dir = (dir or '.') + '/'
    cmdline = ['inotifywait', '-m']
    for e in events:
        cmdline.extend(['-e', e])
    cmdline.append(dir)

    p = subprocess.Popen(
        cmdline,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        universal_newlines=True)
    with p:
        try:
            for line in p.stdout:
                n = line.split()[2]
                if n == name:
                    yield
        except KeyboardInterrupt:
            return


compilers = {}


def compiler(src_ext, dest_ext):
    def decorator(fn):
        compilers[src_ext] = (dest_ext, fn)
        return fn
    return decorator


def transform_file(input_filename, output_filename, fn, exn_fn):
    prev_source = None

    def transformer():
        nonlocal prev_source

        with open(input_filename) as fp:
            source = fp.read()
        if source == prev_source:
            return
        prev_source = source
        print("Transform %s to %s" % (input_filename, output_filename))
        try:
            result = fn(source)
        except dukpy.JSRuntimeError as exn:
            if exn_fn:
                exn_fn(exn)
            else:
                print(exn)
        else:
            with open(output_filename, 'w') as fp:
                fp.write(result)

    return transformer


@compiler('.es6', '.js')
def babel_compile(source):
    return dukpy.babel.babel_compile(source)['code']


@compiler('.es6x', '.js')
def babel_jsx_compile(source):
    r = dukpy.babel.babel_compile(source, presets=['es2015', 'stage-0', 'react'])
    return r['code']


def send_message_to_vim(servername, message):
    cmdline = ['vim', '--servername', servername, '--remote-send',
               ':<C-U>echom %s<CR>' % json.dumps(message)]
    subprocess.check_call(cmdline)


def pass_exception_to_vim(servername, filename):
    def handle_exception(exn):
        print(exn)
        mo = re.search(r'^SyntaxError: .*: (.*) \((\d+):(\d+)\)\n', str(exn))
        if mo:
            text = mo.group(1)
            lnum = mo.group(2)
            col = mo.group(3)
            quickfix_entry = {
                "filename": filename,
                "lnum": int(lnum),
                "col": int(col) + 1,
                "text": text,
            }
            cmdline = ['vim', '--servername', servername, '--remote-expr',
                       '[setqflist([%s]), feedkeys(":\<C-U>cc 1\<CR>")]' %
                       json.dumps(quickfix_entry)]
            subprocess.check_call(cmdline)
        else:
            first_line = str(exn).splitlines()[0]
            send_message_to_vim(servername, first_line)

    return handle_exception


def send_messages_to_vim(servername, fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        send_message_to_vim(servername, 'Compiling...')
        res = fn(*args, **kwargs)
        send_message_to_vim(servername, 'OK')
        return res

    return wrapped


#@compiler('.js', '.es6')
#def es5to6(source):
#    jsi = dukpy.JSInterpreter()
#    jsi.loader.register_path('./js_modules')
#    return jsi.evaljs(
#        'var convert = require("5to6"); convert(dukpy.jscode)',
#        jscode=source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--watch', action='store_true')
    parser.add_argument('--vim-servername')
    parser.add_argument('filename')
    args = parser.parse_args()
    base, ext = os.path.splitext(args.filename)
    try:
        dest_ext, fn = compilers[ext]
    except KeyError:
        parser.error("Filename must end with one of: %s" % sorted(compilers))
    output_filename = base + dest_ext
    exn_fn = None
    if args.vim_servername:
        fn = send_messages_to_vim(args.vim_servername, fn)
        exn_fn = pass_exception_to_vim(args.vim_servername, args.filename)
    transformer = transform_file(args.filename, output_filename, fn, exn_fn)
    transformer()
    if args.watch:
        for _ in await_changes(args.filename, ['close_write', 'moved_to']):
            transformer()


if __name__ == "__main__":
    main()
