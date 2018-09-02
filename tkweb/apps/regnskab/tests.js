// vim:set ft=javascript sw=4 et:
// This file is run by tkweb/apps/regnskab/tests.py.
// It must define a map named "tests" containing functions
// that throw an error if and only if the test fails.

function assertEquals(expected, actual) {
    // Helper function for tests.
    if (expected !== actual) {
        throw new Error('Expected "' + expected + '", got "' + actual + '"');
    }
}

var tests = {
    case_test: function() {
        // Searching should ignore case.
        assertEquals(case_smash('Foo'), case_smash('foo'));
    },
    prefix_first: function () {
        // When searching for a name, turn up people with the first name
        // before people with the middle name.
        var not_expected_name = "Robin James Smith";
        var expected_name = "James Smith";
        var query = "James";
        var persons = [
            {
                "id": 1,
                "in_current": true,
                "sort_key": 10,
                "name": not_expected_name,
                "titles": [],
                "title": null,
                "title_name": not_expected_name
            },
            {
                "id": 2,
                "in_current": true,
                "sort_key": 20,
                "name": expected_name,
                "titles": [],
                "title": null,
                "title_name": expected_name
            }
        ];
        var result = filter_persons(persons, query);
        assertEquals(expected_name, result[0].display);
    }
};
