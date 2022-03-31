#
# Most of this code is from clang_complete:
# https://github.com/xavierd/clang_complete/blob/master/plugin/libclang.py
#
import os
import sys
from clang.cindex import *

# Check if libclang is able to find the builtin include files.
#
# libclang sometimes fails to correctly locate its builtin include files. This
# happens especially if libclang is not installed at a standard location. This
# function checks if the builtin includes are available.
def canFindBuiltinHeaders(index, args = []):
    flags = 0
    currentFile = ("test.c", '#include "stddef.h"')
    try:
        tu = index.parse("test.c", args, [currentFile], flags)
    except TranslationUnitLoadError as e:
        return 0

    return len(tu.diagnostics) == 0

# Derive path to clang builtin headers.
#
# This function tries to derive a path to clang's builtin header files. We are
# just guessing, but the guess is very educated. In fact, we should be right
# for all manual installations (the ones where the builtin header path problem
# is very common) as well as a set of very common distributions.
def getBuiltinHeaderPath(library_path):
    if os.path.isfile(library_path):
        library_path = os.path.dirname(library_path)

    knownPaths = [
        library_path + "/../lib/clang",  # default value
        library_path + "/../clang",      # gentoo
        library_path + "/clang",         # opensuse
        library_path + "/",              # Google
        "/usr/lib64/clang",              # x86_64 (openSUSE, Fedora)
        "/usr/lib/clang"
    ]

    for path in knownPaths:
        try:
            subDirs = [f for f in os.listdir(path) if os.path.isdir(path + "/" + f)]
            subDirs = sorted(subDirs) or ['.']
            path = path + "/" + subDirs[-1] + "/include"
            print("searching builtins in " + path)
            if canFindBuiltinHeaders(index, ["-I" + path]):
                return path
        except:
            pass

    return None

def findLibClang():
    if sys.platform == "darwin":
        knownPaths = [
            "/usr/local/Cellar/llvm/6.0.0/lib",
            "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib",
            "/Library/Developer/CommandLineTools/usr/lib"
        ]
        libSuffix = ".dylib"
    elif sys.platform.startswith("linux"):
        knownPaths = [
            "/usr/lib/llvm-7/lib",
            "/usr/lib/llvm-6.0/lib",
            "/usr/lib/llvm-3.8/lib",
            "/usr/local/lib",
            "/usr/lib"
        ]
        libSuffix = ".so"
    elif sys.platform == "win32" or sys.platform == "msys":
        knownPaths = os.environ.get("PATH").split(':')
        libSuffix = ".dll"
    else:
        # Unsupported platform
        return None
        
    for path in knownPaths:
        # print("trying " + path)
        if os.path.exists(path + "/libclang" + libSuffix):
            return path

    return None

def initLibClang():
    global index

    library_path = findLibClang()
    if library_path:
        print("libclang found: " + library_path)
        if os.path.isdir(library_path):
            Config.set_library_path(library_path)
        else:
            Config.set_library_file(library_path)
    else:
        print("ERROR: libclang not found!")
        return False

    Config.set_compatibility_check(False)
    
    try:
        index = Index.create()
    except Exception as e:
        print("ERROR: could not load libclang from '%s'." % library_path)
        return False

    global builtin_hdr_path
    builtin_hdr_path = getBuiltinHeaderPath(library_path)
    if not builtin_hdr_path:
        print("ERROR: builtin header path not found")
        return False

    # Everything is OK, libclang can be used
    return True
