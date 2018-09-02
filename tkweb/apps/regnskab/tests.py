"""
Run the tests defined in the accompanying tests.js file.

Requires dukpy to be installed.
"""

import json
import unittest

try:
    import dukpy
except ImportError:
    dukpy = None


LIB_FILES = [
    "tkweb/apps/regnskab/static/polyfill/polyfill.min.js",
    "tkweb/apps/regnskab/static/react/react.js",
]
PREAMBLE = """
require("babel-polyfill");
var window = {addEventListener: function (a, b, c) {}, TK_PROFILES: []};
"""  # JavaScript that runs after LIB_FILES and before CODE_FILES
CODE_FILES = ["tkweb/apps/regnskab/static/regnskab/regnskab.js"]
TEST_FILE = "tkweb/apps/regnskab/tests.js"

ENUMERATE_TESTS = """
var test_names = [];
for (var k in tests) {
    test_names.push(k);
}
test_names
"""  # JavaScript fragment to enumerate the tests


def ScriptTestCase(scripts, test_name):
    # Defining this class inside a function serves two purposes:
    # 1. unittest runs all module members that are subclasses of TestCase,
    #    but we don't want to run this class by itself.
    # 2. unittest removes multiple instances of the same TestCase subclass
    #    in a suite, so we need to redefine the class for each test case.
    class ScriptTestCase(unittest.TestCase):
        def runTest(self):
            # If the JavaScript function throws an error,
            # it is wrapped in a dukpy.JSRuntimeError exception,
            # which then causes this test case to fail.
            dukpy.evaljs(scripts + ("tests.%s()\n" % test_name,))

        def __str__(self):
            return "%s:%s" % (TEST_FILE, test_name)

    return ScriptTestCase()


def load_tests(test_loader, test_suite, pattern):
    # Special function invoked by unittest.loader.TestLoader to perform special
    # test suite initialization.
    # Load the JavaScript files and get the test list using dukpy.
    # TODO: Limit tests according to the given pattern.

    if dukpy is None:
        # Add special test case indicating the dukpy is not installed.
        class SkipTestCase(unittest.TestCase):
            def runTest(self):
                self.skipTest("dukpy not installed")

            def __str__(self):
                return "Skip tests because dukpy not installed"

        test_suite.addTest(SkipTestCase())
        return test_suite

    scripts = []
    for filename in LIB_FILES:
        with open(filename) as fp:
            scripts.append(fp.read())
    scripts.append(PREAMBLE)
    for filename in CODE_FILES:
        with open(filename) as fp:
            scripts.append(fp.read())
    with open(TEST_FILE) as fp:
        scripts.append(fp.read())
    scripts = tuple(scripts)

    test_names = dukpy.evaljs(scripts + (ENUMERATE_TESTS,))

    for test_name in test_names:
        test_suite.addTest(ScriptTestCase(scripts, test_name))
    return test_suite
