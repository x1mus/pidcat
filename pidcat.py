#!/usr/bin/env -S python -u

"""
Copyright 2009, The Android Open Source Project

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Script to highlight adb logcat output for console
# Originally written by Jeff Sharkey, http://jsharkey.org/
# Piping detection and popen() added by other Android team members
# Package filtering and output improvements by Jake Wharton, http://jakewharton.com

import argparse
import os
import re
import subprocess
import sys
from subprocess import PIPE
from collections import deque

__version__ = '2.2.0-unofficial'

from typing import Pattern, List, Optional

FROMFILE_PREFIX = '@'
CONF_FILES = [os.path.expanduser('~/.pidcat.conf'), './.pidcat.conf']

LOG_LEVELS = 'VDIWEF'
LOG_LEVELS_MAP = dict([(LOG_LEVELS[i], i) for i in range(len(LOG_LEVELS))])
PROGUARD_MAPPING = re.compile(r'^([\w$\.]+)\s->\s*([\w$\.]+)')

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET = '\033[0m'

IS_TTY = sys.stdout.isatty()


def split_or_empty(to_split: Optional[str], sep: str) -> list[str]:
    if to_split is None:
        return []

    return to_split.split(sep)


ENV_IGNORED_TAGS = split_or_empty(os.getenv("PIDCAT_IGNORED_TAGS"), ";")

PID_LINE = re.compile(r'^\w+\s+(\w+)\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w\s([\w|\.|:|\/]+)$')
PID_START = re.compile(r'^.*: Start proc ([a-zA-Z0-9._:]+) for ([a-z]+ [^:]+): pid=(\d+) uid=(\d+) gids=(.*)$')
PID_START_5_1 = re.compile(r'^.*: Start proc (\d+):([a-zA-Z0-9._:]+)/[a-z0-9]+ for (.*)$')
PID_START_DALVIK = re.compile(r'^E/dalvikvm\(\s*(\d+)\): >>>>> ([a-zA-Z0-9._:]+) \[ userId:0 \| appId:(\d+) \]$')
PID_KILL = re.compile(r'^Killing (\d+):([a-zA-Z0-9._:]+)/[^:]+: (.*)$')
PID_LEAVE = re.compile(r'^No longer want ([a-zA-Z0-9._:]+) \(pid (\d+)\): .*$')
PID_DEATH = re.compile(r'^Process ([a-zA-Z0-9._:]+) \(pid (\d+)\) has died.?$')
LOG_LINE = re.compile(r'^[0-9-]+ ([0-9:.]+) ([A-Z])/(.+?)\( *(\d+)\): (.*?)$')
BUG_LINE = re.compile(r'.*nativeGetEnabledTags.*')
BACKTRACE_LINE = re.compile(r'^#(.*?)pc\s(.*?)$')


def parse_regex_input(input_str: str) -> Pattern:
    input_str = input_str.strip()

    if len(input_str) == 0:
        raise argparse.ArgumentTypeError("Regex must not be empty!")

    if input_str[0] != "^":
        input_str = "^" + input_str

    if input_str[-1] != "$":
        input_str += "$"

    try:
        return re.compile(input_str)
    except Exception as e:
        raise e


def parse_regex_inputs(input_strs: list[str]) -> list[Pattern]:
    return [parse_regex_input(_str) for _str in input_strs]


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Filter logcat by package name', fromfile_prefix_chars=FROMFILE_PREFIX)
    parser.add_argument('package', nargs='*', help='Application package name(s)')
    parser.add_argument('-W', '--width', metavar='N', dest='width', type=int, default=-1,
                        help='Override word wrap width.')
    parser.add_argument('-w', '--tag-width', metavar='N', dest='tag_width', type=int, default=23,
                        help='Width of log tag')
    parser.add_argument('-l', '--min-level', dest='min_level', type=str, choices=LOG_LEVELS + LOG_LEVELS.lower(),
                        default='V', help='Minimum level to be displayed')
    parser.add_argument('--color-gc', dest='color_gc', action='store_true', help='Color garbage collection')
    parser.add_argument('--always-display-tags', dest='always_tags', action='store_true',
                        help='Always display the tag name')
    parser.add_argument('--current', dest='current_app', action='store_true',
                        help='Filter logcat by current running app')
    parser.add_argument('-s', '--serial', dest='device_serial', help='Device serial number (adb -s option)')
    parser.add_argument('-d', '--device', dest='use_device', action='store_true',
                        help='Use first device for log input (adb -d option)')
    parser.add_argument('-e', '--emulator', dest='use_emulator', action='store_true',
                        help='Use first emulator for log input (adb -e option)')
    parser.add_argument('-b', '--buffer', dest='alternate_buffer', nargs='+', help='Request alternate ring buffer')
    parser.add_argument('-c', '--clear', dest='clear_logcat', action='store_true',
                        help='Clear the entire log before running')
    parser.add_argument('-t', '--tag', dest='tag', action='append', help='Filter output by specified tag(s)')
    parser.add_argument('-i', '--ignore-tag', dest='ignored_tag', type=parse_regex_input, action='extend', nargs='+',
                        help='Filter output by ignoring tag(s) matching the given regex')
    parser.add_argument('--proguard-mapping', dest='proguard_mapping', action='store',
                        help='Use proguard mapping to translate the input tag names')

    # TODO: Add simple contains filter, make --filter and --contains mutually exclusive
    parser.add_argument('--filter', dest='filter', type=parse_regex_input, action='extend', nargs='+',
                        help='Only output messages matching the given regex; Input will be wrapped in ^$; Regex is '
                             'case-sensitive')
    # parser.add_argument('--contains', dest='filter', action='store',
    #                     help='Only output messages matching the given regex')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__,
                        help='Print the version number and exit')
    parser.add_argument('-a', '--all', dest='all', action='store_true', default=False, help='Print all log messages')
    parser.add_argument('--colorized', '--colorized', dest='colorized', action='store_true', default=False,
                        help='Colorize log messages as well')
    parser.add_argument('--timestamp', dest='add_timestamp', action='store_true',
                        help='Prepend each line of output with the current time.')
    parser.add_argument('--force-windows-colors', dest='force_windows_colors', action='store_true', default=False,
                        help='Force converting colors to Windows format')

    return parser.parse_args(argv)


def print_line(line: str):
    # Make development more straightforward by allowing all prints to be commented out in a single place
    print(line)
    pass


def check_match_any_pattern(input_str: str, patterns: List[Pattern]):
    return any(pattern.match(input_str) for pattern in patterns)


TERM_CACHE: dict[(Optional[int], Optional[int]), str] = {}


def termcolor(fg: Optional[int] = None, bg: Optional[int] = None):
    key = (fg, bg)
    cached = TERM_CACHE.get(key, None)
    if cached is not None:
        return cached

    codes = []
    if fg is not None:
        codes.append('3%d' % fg)

    if bg is not None:
        codes.append('10%d' % bg)

    color = '\033[%sm' % ';'.join(codes) if codes else ''
    TERM_CACHE[(fg, bg)] = color

    return color


def colorize(message, fg=None, bg=None):
    return termcolor(fg, bg) + message + RESET if IS_TTY else message


RULES: dict[Pattern, str] = {
    # StrictMode policy violation; ~duration=319 ms: android.os.StrictMode$StrictModeDiskWriteViolation: policy=31
    # violation=1
    re.compile(r'^(StrictMode policy violation)(; ~duration=)(\d+ ms)'): (
            r'%s\1%s\2%s\3%s' % (termcolor(RED), RESET, termcolor(YELLOW), RESET))
}

TAG_TYPES = {
    'V': colorize(' V ', fg=WHITE, bg=BLACK),
    'D': colorize(' D ', fg=BLACK, bg=BLUE),
    'I': colorize(' I ', fg=BLACK, bg=GREEN),
    'W': colorize(' W ', fg=BLACK, bg=YELLOW),
    'E': colorize(' E ', fg=BLACK, bg=RED),
    'F': colorize(' F ', fg=BLACK, bg=RED),
}

LAST_USED: deque[int] = deque([RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN])
KNOWN_TAGS: dict[str, str] = {
    'dalvikvm': WHITE,
    'Process': WHITE,
    'ActivityManager': WHITE,
    'ActivityThread': WHITE,
    'AndroidRuntime': CYAN,
    'jdwp': WHITE,
    'StrictMode': WHITE,
    'DEBUG': YELLOW,
}


def allocate_color(tag: str) -> str:
    # this will allocate a unique format for the given tag
    # since we don't have very many colors, we always keep track of the LRU
    color = KNOWN_TAGS.get(tag, LAST_USED.popleft())
    LAST_USED.append(color)
    return color


def init_colorama(force_windows_colors: bool):
    try:
        import colorama
        colorama.init(convert=force_windows_colors)
    except ImportError:
        if force_windows_colors:
            raise


def setup_terminal_width(width: int) -> (any, int):
    if width < 0:
        try:
            # Get the current terminal width
            import fcntl, termios, struct
            h, width = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('hh', 0, 0)))
            return h, width
        except:
            pass


def indent_wrap(width: int, header_size: int, message: str):
    if width == -1:
        return message

    message = message.replace('\t', '    ')
    wrap_area = width - header_size
    message_buf = ''
    current = 0

    while current < len(message):
        _next = min(current + wrap_area, len(message))
        message_buf += message[current:_next]
        if _next < len(message):
            message_buf += '\n'
            message_buf += ' ' * header_size
        current = _next

    return message_buf


def match_packages(package: str, named_processes: set[str], catchall_package: set[str], token: str):
    if len(package) == 0:
        return True

    if token in named_processes:
        return True

    index = token.find(':')
    return (token in catchall_package) if index == -1 else (token[:index] in catchall_package)


def try_parse_death(pattern: Pattern, message: str, pid_group: int = 2, package_line_group: int = 1) -> Optional[tuple[str, str]]:
    match = pattern.match(message)
    if match:
        pid = match.group(pid_group)
        package_line = match.group(package_line_group)
        return pid, package_line

    return None


def parse_death(package: str, named_processes: str, catchall_package: set[str], pids: set[str], tag: str,
                message: str) -> tuple[str, str]:
    if tag != 'ActivityManager':
        return None, None

    killed = try_parse_death(PID_KILL, message, 1, 2)
    if killed and match_packages(package, named_processes, catchall_package, killed[1]) and killed[0] in pids:
        return killed

    left = try_parse_death(PID_LEAVE, message)
    if left and match_packages(package, named_processes, catchall_package, left[1]) and left[0] in pids:
        return left

    died = try_parse_death(PID_LEAVE, message)
    if died and match_packages(package, named_processes, catchall_package, died[1]) and died[0] in pids:
        return died

    return None, None


def parse_start_process(line: str):
    start = PID_START_5_1.match(line)
    if start:
        line_pid, line_package, target = start.groups()
        return line_package, target, line_pid, '', ''

    start = PID_START.match(line)
    if start:
        line_package, target, line_pid, line_uid, line_gids = start.groups()
        return line_package, target, line_pid, line_uid, line_gids

    start = PID_START_DALVIK.match(line)
    if start:
        line_pid, line_package, line_uid = start.groups()
        return line_package, '', line_pid, line_uid, ''

    return None


def set_term_title(title):
    sys.stdout.write("\033]0;%s\a" % title)


def clear_term_title():
    set_term_title("")


# This is a ducktype of the subprocess.Popen object
class FakeStdInProcess:
    def __init__(self):
        self.stdout = sys.stdin

    def poll(self):
        return None


def main():
    argv = ['%s%s' % (FROMFILE_PREFIX, conf) for conf in CONF_FILES if os.path.isfile(conf)]
    argv.extend(sys.argv[1:])
    args = parse_args(argv)
    min_level = LOG_LEVELS_MAP[args.min_level.upper()]

    package = args.package

    base_adb_command = ['adb']
    if args.device_serial:
        base_adb_command.extend(['-s', args.device_serial])
    if args.use_device:
        base_adb_command.append('-d')
    if args.use_emulator:
        base_adb_command.append('-e')

    android_version_command = base_adb_command + ["shell", "getprop", "ro.build.version.sdk"]
    android_sdk = subprocess.Popen(android_version_command, stdout=PIPE, stderr=PIPE).communicate()[0]

    if args.current_app:
        system_dump_command = base_adb_command + ["shell", "dumpsys", "activity", "activities"]
        system_dump = subprocess.Popen(system_dump_command, stdout=PIPE, stderr=PIPE).communicate()[0]
        try:
            if int(android_sdk) >= 30:
                running_package_name = re.search(".*Task.*A[= ][0-9]+:([^ ^}]*)", str(system_dump)).group(1)
            else:
                running_package_name = re.search(".*TaskRecord.*A[= ]([^ ^}]*)", str(system_dump)).group(1)

            package.append(running_package_name)
        except:
            pass

    proguard_mapping = {}
    if args.proguard_mapping:
        with open(args.proguard_mapping) as fr:
            for line in fr:
                mapping_match = PROGUARD_MAPPING.match(line.strip())
                if mapping_match is not None:
                    from_ = mapping_match.group(1)
                    to = mapping_match.group(2)
                    proguard_mapping[to] = from_

    if len(package) == 0:
        args.all = True

    # Store the names of packages for which to match all processes.
    catchall_package = set(filter(lambda pkg: pkg.find(":") == -1, package))

    # Store the name of processes to match exactly.
    named_processes = set(filter(lambda pkg: pkg.find(":") != -1, package))

    # Convert default process names from <package>: (cli notation) to <package> (android notation) in the exact names
    # match group.
    named_processes = set([pkg if pkg.find(":") != len(pkg) - 1 else pkg[:-1] for pkg in named_processes])

    header_size = args.tag_width + 1 + 3 + 1  # space, level, space
    if args.add_timestamp:
        header_size += 12 + 1  # time, space

    width = args.width
    new_size = setup_terminal_width(width)
    if new_size:
        h, width = new_size

    init_colorama(args.force_windows_colors)

    # Only enable GC coloring if the user opted-in
    if args.color_gc:
        # GC_CONCURRENT freed 3617K, 29% free 20525K/28648K, paused 4ms+5ms, total 85ms
        key = re.compile(
            r'^(GC_(?:CONCURRENT|FOR_M?ALLOC|EXTERNAL_ALLOC|EXPLICIT) )(freed <?\d+.)(, \d+\% free \d+./\d+., )(paused \d+ms(?:\+\d+ms)?)')
        val = r'\1%s\2%s\3%s\4%s' % (termcolor(GREEN), RESET, termcolor(YELLOW), RESET)

        RULES[key] = val

    device_name_command = base_adb_command + ["shell", "getprop", "ro.product.model"]
    device_name = subprocess.Popen(device_name_command, stdout=PIPE, stderr=PIPE).communicate()[0]
    set_term_title(device_name)

    adb_command = base_adb_command[:]
    adb_command.append('logcat')
    adb_command.extend(['-v', 'time'])

    if args.alternate_buffer:
        for buffer in args.alternate_buffer:
            adb_command.extend(['-b', buffer])

    # Clear log before starting logcat
    if args.clear_logcat:
        adb_clear_command = list(adb_command)
        adb_clear_command.append('-c')
        adb_clear = subprocess.Popen(adb_clear_command)

        while adb_clear.poll() is None:
            pass

    if sys.stdin.isatty():
        adb = subprocess.Popen(adb_command, stdin=PIPE, stdout=PIPE)
    else:
        adb = FakeStdInProcess()

    pids: set[str] = set()
    last_tag = None
    app_pid = None

    ps_command = base_adb_command + ['shell', 'ps']
    ps_pid = subprocess.Popen(ps_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    while True:
        try:
            line = ps_pid.stdout.readline().decode('utf-8', 'replace').strip()
        except KeyboardInterrupt:
            break
        if len(line) == 0:
            break

        pid_match = PID_LINE.match(line)
        if pid_match is not None:
            pid = pid_match.group(1)
            proc = pid_match.group(2)
            index = proc.find(':')
            keep = (proc in catchall_package) if index == -1 else (proc[:index] in catchall_package)
            if keep:
                seen_pids = True
                pids.add(pid)

    compiled_env_ignore_tags = parse_regex_inputs(ENV_IGNORED_TAGS)
    while adb.poll() is None:
        try:
            line = adb.stdout.readline()
        except KeyboardInterrupt:
            break
        if len(line) == 0:
            break

        line = line.decode('utf-8', 'replace').strip()
        if len(line) == 0:
            continue

        bug_line = BUG_LINE.match(line)
        if bug_line is not None:
            continue

        log_line = LOG_LINE.match(line)
        if log_line is None:
            continue

        time, level, tag, owner, message = log_line.groups()
        tag = tag.strip()
        tag = proguard_mapping.get(tag, tag)
        start = parse_start_process(line)
        if start:
            line_package, target, line_pid, line_uid, line_gids = start
            if match_packages(package, named_processes, catchall_package, line_package):
                pids.add(line_pid)

                app_pid = line_pid

                line_buffer = '\n'
                line_buffer += colorize(' ' * (header_size - 1), bg=WHITE)
                line_buffer += indent_wrap(width, header_size, ' Process %s created for %s\n' % (line_package, target))
                line_buffer += colorize(' ' * (header_size - 1), bg=WHITE)
                line_buffer += ' PID: %s   UID: %s   GIDs: %s' % (line_pid, line_uid, line_gids)
                line_buffer += '\n'
                print_line(line_buffer)
                last_tag = None  # Ensure next log gets a tag printed

        dead_pid, dead_pname = parse_death(package, named_processes, catchall_package, pids, tag, message)
        if dead_pid:
            pids.remove(dead_pid)
            line_buffer = '\n'
            line_buffer += colorize(' ' * (header_size - 1), bg=RED)
            line_buffer += ' Process %s (PID: %s) ended' % (dead_pname, dead_pid)
            line_buffer += '\n'
            print_line(line_buffer)
            last_tag = None  # Ensure next log gets a tag printed

        # Make sure the backtrace is printed after a native crash
        if tag == 'DEBUG':
            bt_line = BACKTRACE_LINE.match(message.lstrip())
            if bt_line is not None:
                message = message.lstrip()
                owner = app_pid

        if not args.all and owner not in pids:
            continue
        if level in LOG_LEVELS_MAP and LOG_LEVELS_MAP[level] < min_level:
            continue
        if args.ignored_tag and check_match_any_pattern(tag, args.ignored_tag):
            continue
        if args.tag and not check_match_any_pattern(tag, args.tag):
            continue
        if args.filter and not check_match_any_pattern(message, args.filter):
            continue
        if len(compiled_env_ignore_tags) > 0 and check_match_any_pattern(tag, compiled_env_ignore_tags):
            continue

        line_buffer = ''

        if args.tag_width > 0:
            # right-align tag title and allocate color if needed
            if tag != last_tag or args.always_tags:
                last_tag = tag
                color = allocate_color(tag)
                tag = tag[-args.tag_width:].rjust(args.tag_width)
                line_buffer += colorize(tag, fg=color)
            else:
                line_buffer += ' ' * args.tag_width
            line_buffer += ' '

        # write out level colored edge
        if level in TAG_TYPES:
            line_buffer += TAG_TYPES[level]
        else:
            line_buffer += ' ' + level + ' '
        line_buffer += ' '
        if args.add_timestamp:
            line_buffer = time + ' ' + line_buffer

        # format tag message using rules
        for matcher in RULES:
            replace = RULES[matcher]
            message = matcher.sub(replace, message)

        line_foreground = color if args.colorized else WHITE
        line_buffer += indent_wrap(width, header_size, colorize(message, fg=line_foreground))
        if sys.stdout.encoding.upper() not in ['UTF-8', 'UTF8']:
            print_line(line_buffer.encode('utf-8'))
        else:
            print_line(line_buffer)

    clear_term_title()


if __name__ == "__main__":
    main()
