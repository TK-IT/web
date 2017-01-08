'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

// vim:set ft=javascript sw=4 et:

function prefix_to_age(p) {
    // Assume p matches tk_prefix in get_query_filters.
    var base_value = { 'K': -1, 'G': 1, 'B': 2, 'O': 3, 'T': 1, '': 1 };
    var pattern = /([KGBOT])([0-9]*)|([0-9]+)/g;
    var mo = void 0;
    var age = 0;
    while ((mo = pattern.exec(p)) !== null) {
        var exp_string = (mo[2] || '') + (mo[3] || '') || '1';
        var exp = parseInt(exp_string);
        // If p starts with a digit, assume an initial 'T' is omitted.
        var base = mo[1] || 'T';
        age += exp * base_value[base];
    }
    return age;
}

function age_to_prefix(age) {
    var m = ['K', '', 'G', 'B', 'O', 'TO'];
    if (-1 <= age && age <= 4) return m[age + 1];else if (age < 0) return 'K' + -age;else return 'T' + (age - 3) + 'O';
}

function get_query_filters(query) {
    function all_prefixes(s) {
        // Map e.g. "FORM" to "F|FO|FOR|FORM"
        var p = [];
        for (var i = 1; i <= s.length; ++i) {
            p.push(s.substring(0, i));
        }return p.join('|');
    }

    var tk_prefix = '[KGBOT][KGBOT0-9]*|[0-9]*O';
    // Include EFUIT with BEST for the purpose of searching
    var best_list = 'CERM FORM INKA KASS NF PR SEKR VC EFUIT'.split(' ');
    // best_prefix is a regex that matches any prefix of a BEST title
    var best_prefix = best_list.map(all_prefixes).join('|');
    // Map first letter to BEST title, e.g. best_map['F'] === 'FORM'
    var best_map = {};
    var _iteratorNormalCompletion = true;
    var _didIteratorError = false;
    var _iteratorError = undefined;

    try {
        for (var _iterator = best_list[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
            var t = _step.value;
            best_map[t.charAt(0)] = t;
        } // fu_two_letters is a regex that matches the last two letters of a FU title
    } catch (err) {
        _didIteratorError = true;
        _iteratorError = err;
    } finally {
        try {
            if (!_iteratorNormalCompletion && _iterator.return) {
                _iterator.return();
            }
        } finally {
            if (_didIteratorError) {
                throw _iteratorError;
            }
        }
    }

    var fu_two_letters = '[A-ZÆØÅ]{2}';

    // Regex matching just a prefix or part of a shorthand prefix.
    var re_prefix = new RegExp('^(' + tk_prefix + ')$|^[0-9]$');
    // Regex matching optional TK prefix followed by a prefix of a BEST title.
    var re_best = new RegExp('^(' + tk_prefix + '|)(' + best_prefix + ')$');
    // Regex matching optional TK prefix followed by FU title.
    var re_fu = new RegExp('^(' + tk_prefix + '|)(?:FU)?(' + fu_two_letters + ')$');
    // Regex matching optional TK prefix followed by FUAN.
    var re_fuan = new RegExp('^(' + tk_prefix + '|)AN$');

    // Does the query case insensitively match BEST or FU title?
    var q_upper = query.toUpperCase();
    var mo_prefix = re_prefix.exec(q_upper);
    var mo_best = re_best.exec(q_upper);
    var mo_fu = re_fu.exec(q_upper);
    var mo_fuan = re_fuan.exec(q_upper);

    // `filters` is a list of functions used to determine if query matches title.
    var filters = [];
    // Exact match on title
    filters.push(function (t) {
        return t.toUpperCase() === q_upper;
    });
    if (mo_fuan) {
        (function () {
            var prefix = age_to_prefix(prefix_to_age(mo_fuan[1]));
            filters.push(function (t) {
                return t === prefix + 'FUAN';
            });
        })();
    }
    if (mo_fu) {
        (function () {
            var fu_search = 'FU' + mo_fu[2];
            if (mo_fu[1]) {
                (function () {
                    // Query has a TK prefix => exact match on person
                    var prefix = age_to_prefix(prefix_to_age(mo_fu[1]));
                    filters.push(function (t) {
                        return t === prefix + fu_search;
                    });
                })();
            } else {
                // Query has no TK prefix => suffix search
                filters.push(function (t) {
                    return t.substring(t.length - 4, t.length) === fu_search;
                });
            }
        })();
    }
    if (mo_best) {
        (function () {
            var prefix = age_to_prefix(prefix_to_age(mo_best[1]));
            var best_search = best_map[mo_best[2].charAt(0)];
            filters.push(function (t) {
                return t === prefix + best_search;
            });
        })();
    }
    if (!mo_prefix) {
        // Fallback: case sensitive search in title
        filters.push(function (t) {
            return t.indexOf(query) !== -1;
        });
    }
    return filters;
}

function utility_of_filter(filter, person) {
    var _iteratorNormalCompletion2 = true;
    var _didIteratorError2 = false;
    var _iteratorError2 = undefined;

    try {
        for (var _iterator2 = person.titles[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
            var title = _step2.value;

            if (filter(title)) {
                return title;
            }
        }
    } catch (err) {
        _didIteratorError2 = true;
        _iteratorError2 = err;
    } finally {
        try {
            if (!_iteratorNormalCompletion2 && _iterator2.return) {
                _iterator2.return();
            }
        } finally {
            if (_didIteratorError2) {
                throw _iteratorError2;
            }
        }
    }

    if (filter(person.name)) {
        return '';
    }
    return null;
}

function first_matching_filter(persons, filters) {
    var _iteratorNormalCompletion3 = true;
    var _didIteratorError3 = false;
    var _iteratorError3 = undefined;

    try {
        for (var _iterator3 = filters[Symbol.iterator](), _step3; !(_iteratorNormalCompletion3 = (_step3 = _iterator3.next()).done); _iteratorNormalCompletion3 = true) {
            var f = _step3.value;

            var persons_keyed = [];
            var _iteratorNormalCompletion4 = true;
            var _didIteratorError4 = false;
            var _iteratorError4 = undefined;

            try {
                for (var _iterator4 = persons[Symbol.iterator](), _step4; !(_iteratorNormalCompletion4 = (_step4 = _iterator4.next()).done); _iteratorNormalCompletion4 = true) {
                    var p = _step4.value;

                    var r = utility_of_filter(f, p);
                    if (r !== null) persons_keyed.push([r, p]);
                }
            } catch (err) {
                _didIteratorError4 = true;
                _iteratorError4 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion4 && _iterator4.return) {
                        _iterator4.return();
                    }
                } finally {
                    if (_didIteratorError4) {
                        throw _iteratorError4;
                    }
                }
            }

            if (persons_keyed.length !== 0) return persons_keyed;
        }
    } catch (err) {
        _didIteratorError3 = true;
        _iteratorError3 = err;
    } finally {
        try {
            if (!_iteratorNormalCompletion3 && _iterator3.return) {
                _iterator3.return();
            }
        } finally {
            if (_didIteratorError3) {
                throw _iteratorError3;
            }
        }
    }

    return [];
}

function filter_persons(persons, query) {
    if (query === '') {
        return [];
    } else if (query === '*') {
        return persons.map(function (p) {
            return { 'display': p.title_name + ' ' + p.titles.join(' '), 'person': p };
        });
    }
    var filters = get_query_filters(query);

    var persons_current_keyed = first_matching_filter(persons.filter(function (p) {
        return p.in_current;
    }), filters);
    var persons_keyed = persons_current_keyed.length ? persons_current_keyed : first_matching_filter(persons, filters);

    persons_keyed.sort(function (a, b) {
        return a[1].sort_key - b[1].sort_key;
    });
    var r = persons_keyed.map(function (x) {
        return { 'display': (x[0] + ' ' + x[1].name).trim(),
            'person': x[1] };
    });
    return r;
}

var filter_persons_cached = function () {
    var cached_persons = null;
    var results = null;
    return function filter_persons_cached(persons, query) {
        if (persons !== cached_persons) {
            cached_persons = persons;
            results = {};
        }
        if (!(query in results)) results[query] = filter_persons(persons, query);
        return results[query];
    };
}();

var Cross = function (_React$PureComponent) {
    _inherits(Cross, _React$PureComponent);

    function Cross() {
        _classCallCheck(this, Cross);

        return _possibleConstructorReturn(this, (Cross.__proto__ || Object.getPrototypeOf(Cross)).apply(this, arguments));
    }

    _createClass(Cross, [{
        key: 'render',
        value: function render() {
            return React.createElement(
                'div',
                { className: 'cross' },
                '×'
            );
        }
    }]);

    return Cross;
}(React.PureComponent);

var Crosses = function (_React$PureComponent2) {
    _inherits(Crosses, _React$PureComponent2);

    function Crosses() {
        _classCallCheck(this, Crosses);

        return _possibleConstructorReturn(this, (Crosses.__proto__ || Object.getPrototypeOf(Crosses)).apply(this, arguments));
    }

    _createClass(Crosses, [{
        key: 'render',
        value: function render() {
            var crosses = [];
            for (var i = 0; i < Math.min(this.props.count, this.props.maxCount); ++i) {
                crosses.push(React.createElement(Cross, { key: i }));
            }return React.createElement(
                'div',
                { className: 'crosses' },
                crosses
            );
        }
    }]);

    return Crosses;
}(React.PureComponent);

var ColumnEntry = function (_React$Component) {
    _inherits(ColumnEntry, _React$Component);

    function ColumnEntry() {
        var _ref;

        var _temp, _this3, _ret5;

        _classCallCheck(this, ColumnEntry);

        for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) {
            args[_key] = arguments[_key];
        }

        return _ret5 = (_temp = (_this3 = _possibleConstructorReturn(this, (_ref = ColumnEntry.__proto__ || Object.getPrototypeOf(ColumnEntry)).call.apply(_ref, [this].concat(args))), _this3), _this3.state = {
            inputValue: ''
        }, _temp), _possibleConstructorReturn(_this3, _ret5);
    }

    _createClass(ColumnEntry, [{
        key: 'shouldComponentUpdate',
        value: function shouldComponentUpdate(nextProps, nextState) {
            return this.props.value !== nextProps.value || this.state.inputValue !== nextState.inputValue || this.props.columnKind !== nextProps.columnKind;
        }
    }, {
        key: 'getInputValue',
        value: function getInputValue() {
            var v = this.props.value;
            if (v === null) return '';
            var st = this.state.inputValue.replace(/,/g, '.');
            if (parseFloat(st) === v) {
                return this.state.inputValue;
            } else {
                return '' + v;
            }
        }
    }, {
        key: 'handleKeyDown',
        value: function handleKeyDown(ev) {
            if (ev.key === 'ArrowDown') this.props.onArrowDown();else if (ev.key === 'ArrowUp') this.props.onArrowUp();
        }
    }, {
        key: 'onChange',
        value: function onChange(s) {
            if (s === '') {
                this.setState({ inputValue: '' });
                this.props.onChange(null);
            }
            var st = s.replace(/,/g, '.');
            if (!/\d+\.?\d*/.exec(st)) return;
            var v = parseFloat(st);
            this.setState({ inputValue: s });
            this.props.onChange(v);
        }
    }, {
        key: 'render',
        value: function render() {
            var _this4 = this;

            return React.createElement(
                'div',
                { className: 'column column-' + this.props.columnKind },
                React.createElement(Crosses, { count: this.props.value, maxCount: 30 }),
                React.createElement('input', { className: 'column-entry', value: this.getInputValue(),
                    onFocus: this.props.onFocus,
                    onChange: function onChange(e) {
                        return _this4.onChange(e.target.value);
                    },
                    onKeyDown: this.handleKeyDown.bind(this) })
            );
        }
    }]);

    return ColumnEntry;
}(React.Component);

var PersonChoice = function (_React$Component2) {
    _inherits(PersonChoice, _React$Component2);

    function PersonChoice() {
        _classCallCheck(this, PersonChoice);

        return _possibleConstructorReturn(this, (PersonChoice.__proto__ || Object.getPrototypeOf(PersonChoice)).apply(this, arguments));
    }

    _createClass(PersonChoice, [{
        key: 'shouldComponentUpdate',
        value: function shouldComponentUpdate(nextProps, nextState) {
            if (this.props.value !== nextProps.value) return true;
            if (this.props.choices.length !== nextProps.choices.length) return true;
            for (var i = 0; i < nextProps.choices.length; ++i) {
                if (this.props.choices[i].display !== nextProps.choices[i].display || this.props.choices[i].id !== nextProps.choices[i].id) return true;
            }return false;
        }
    }, {
        key: 'onChange',
        value: function onChange(i) {
            var _props$choices$i = this.props.choices[i];
            var display = _props$choices$i.display;
            var person = _props$choices$i.person;

            this.props.onChange(person.id);
        }
    }, {
        key: 'render',
        value: function render() {
            var _this6 = this;

            if (this.props.choices.length === 0) {
                return null;
            }
            var options = this.props.choices.map(function (_ref2) {
                var display = _ref2.display;
                var person = _ref2.person;
                return React.createElement(
                    'option',
                    { value: person.id, key: person.id },
                    display
                );
            });
            var value = this.props.value;
            if (value === null) value = this.props.choices[0].id;
            return React.createElement(
                'select',
                { className: 'person-choice', value: value,
                    onChange: function onChange(e) {
                        return _this6.onChange(e.target.selectedIndex);
                    } },
                options
            );
        }
    }]);

    return PersonChoice;
}(React.Component);

var Name = function (_React$Component3) {
    _inherits(Name, _React$Component3);

    function Name() {
        _classCallCheck(this, Name);

        return _possibleConstructorReturn(this, (Name.__proto__ || Object.getPrototypeOf(Name)).apply(this, arguments));
    }

    _createClass(Name, [{
        key: 'onPersonChange',
        value: function onPersonChange(v) {
            this.props.onChange(v, this.props.nameValue);
        }
    }, {
        key: 'onNameChange',
        value: function onNameChange(v) {
            var p = void 0;
            if (v.trim() === '') {
                p = null;
            } else if (this.props.personValue === null || this.props.personValue === this.getChoices()[0].person.id) {
                var newChoices = this.getChoices(v);
                if (newChoices.length === 0) p = null;else p = newChoices[0].person.id;
            } else {
                p = this.props.personValue;
            }
            this.props.onChange(p, v);
        }
    }, {
        key: 'getChoices',
        value: function getChoices(query) {
            if (typeof query === 'undefined') query = this.props.nameValue;
            return filter_persons_cached(this.props.persons, query);
        }
    }, {
        key: 'handleKeyDown',
        value: function handleKeyDown(ev) {
            if (ev.key === 'ArrowDown') this.props.onArrowDown();else if (ev.key === 'ArrowUp') this.props.onArrowUp();
        }
    }, {
        key: 'setNameEntry',
        value: function setNameEntry(o) {
            this.nameInputDOMNode = o;
        }
    }, {
        key: 'render',
        value: function render() {
            var _this8 = this;

            return React.createElement(
                'div',
                { className: 'name' },
                React.createElement('input', { className: 'name-entry',
                    value: this.props.nameValue,
                    ref: this.setNameEntry.bind(this),
                    onFocus: this.props.onFocus,
                    onKeyDown: this.handleKeyDown.bind(this),
                    onChange: function onChange(e) {
                        return _this8.onNameChange(e.target.value);
                    } }),
                React.createElement(PersonChoice, { choices: this.getChoices(),
                    value: this.props.personValue,
                    onChange: function onChange(v) {
                        return _this8.onPersonChange(v);
                    } })
            );
        }
    }]);

    return Name;
}(React.Component);

var SheetRow = function (_React$Component4) {
    _inherits(SheetRow, _React$Component4);

    function SheetRow() {
        _classCallCheck(this, SheetRow);

        return _possibleConstructorReturn(this, (SheetRow.__proto__ || Object.getPrototypeOf(SheetRow)).apply(this, arguments));
    }

    _createClass(SheetRow, [{
        key: 'shouldComponentUpdate',
        value: function shouldComponentUpdate(nextProps, nextState) {
            if (this.props.nameValue !== nextProps.nameValue || this.props.personValue !== nextProps.personValue) return true;
            for (var i = 0; i < nextProps.columns.length; ++i) {
                if (nextProps.columns[i] !== this.props.columns[i]) return true;
            }return false;
        }
    }, {
        key: 'render',
        value: function render() {
            var _this10 = this;

            var columnKind = ['1', '1ks', '2', '2ks', '3', '3ks'];
            var columns = this.props.columns.map(function (v, i) {
                return React.createElement(ColumnEntry, { columnKind: columnKind[i],
                    value: v, key: columnKind[i],
                    onFocus: _this10.props.onFocus,
                    onArrowDown: _this10.props.onArrowDown,
                    onArrowUp: _this10.props.onArrowUp,
                    onChange: function onChange(v) {
                        return _this10.props.onChange(i, v);
                    } });
            });
            return React.createElement(
                'div',
                { className: 'sheetrow' },
                React.createElement(Name, { persons: this.props.persons, nameValue: this.props.nameValue,
                    ref: function ref(o) {
                        return _this10.nameInputDOMNode = o && o.nameInputDOMNode;
                    },
                    personValue: this.props.personValue,
                    onFocus: this.props.onFocus,
                    onArrowDown: this.props.onArrowDown,
                    onArrowUp: this.props.onArrowUp,
                    onChange: this.props.onChangeName }),
                columns
            );
        }
    }]);

    return SheetRow;
}(React.Component);

function load_form_state() {
    var field = document.getElementById('tk_rows');
    if (field.value === '') return [];
    var o = JSON.parse(field.value);
    return o;
}

function save_form_state(o) {
    var field = document.getElementById('tk_rows');
    field.value = JSON.stringify(o);
}

var Sheet = function (_React$Component5) {
    _inherits(Sheet, _React$Component5);

    function Sheet() {
        var _ref3;

        var _temp2, _this11, _ret6;

        _classCallCheck(this, Sheet);

        for (var _len2 = arguments.length, args = Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
            args[_key2] = arguments[_key2];
        }

        return _ret6 = (_temp2 = (_this11 = _possibleConstructorReturn(this, (_ref3 = Sheet.__proto__ || Object.getPrototypeOf(Sheet)).call.apply(_ref3, [this].concat(args))), _this11), _this11.state = {
            rows: _this11.get_initial_rows(),
            currentRow: null
        }, _temp2), _possibleConstructorReturn(_this11, _ret6);
    }

    _createClass(Sheet, [{
        key: 'get_initial_rows',
        value: function get_initial_rows() {
            var rows = load_form_state();
            if (rows.length === 0 || rows[rows.length - 1].name !== '') rows.push(this.empty_row());
            return rows;
        }
    }, {
        key: 'empty_row',
        value: function empty_row() {
            return { name: '', profile_id: null,
                image: null,
                counts: [null, null, null, null, null, null] };
        }
    }, {
        key: 'onChangeCell',
        value: function onChangeCell(i, j, v) {
            this.state.rows[i].counts = [].slice.call(this.state.rows[i].counts);
            this.state.rows[i].counts[j] = v;
            if (i === this.state.rows.length - 1) this.state.rows.push(this.empty_row());
            save_form_state(this.state.rows);
            this.setState({});
        }
    }, {
        key: 'onChangeName',
        value: function onChangeName(i, p, n) {
            this.state.rows[i].name = n;
            this.state.rows[i].profile_id = p;
            if (i === this.state.rows.length - 1) this.state.rows.push(this.empty_row());
            save_form_state(this.state.rows);
            this.setState({});
        }
    }, {
        key: 'setRowElement',
        value: function setRowElement(i, o) {
            this.rowElements[i] = o;
        }
    }, {
        key: 'focusRow',
        value: function focusRow(i) {
            if (0 <= i && i < this.rowElements.length && this.rowElements[i]) {
                this.rowElements[i].nameInputDOMNode.focus();
                this.scrollIntoView(i);
            }
        }
    }, {
        key: 'scrollIntoView',
        value: function scrollIntoView(i) {
            if (!this.rowElements[i]) return;
            var o = this.rowElements[i].nameInputDOMNode;
            if (!o) return;
            var y1 = document.documentElement.scrollTop;
            var y2 = y1 + document.documentElement.clientHeight;
            var y = o.offsetTop;
            var y_rel = (y - y1) / (y2 - y1);
            if (y_rel < 0 || y_rel > 2 / 3) document.documentElement.scrollTop = y;
        }
    }, {
        key: 'onFocus',
        value: function onFocus(i) {
            if (this.currentRow === null || this.currentRow < i) {
                this.scrollIntoView(i);
            }
            this.currentRow = i;
        }
    }, {
        key: 'render',
        value: function render() {
            var rows = [];
            if (typeof this.rowElements === 'undefined') this.rowElements = [];
            var counts = [0, 0, 0, 0, 0, 0];
            for (var i = 0; i < this.state.rows.length; ++i) {
                var data = this.state.rows[i];
                for (var j = 0; j < counts.length; ++j) {
                    counts[j] += data.counts[j] || 0;
                }if (this.rowElements.length < i) this.rowElements.push(null);
                rows.push(React.createElement(SheetRow, { key: i + 'row',
                    ref: this.setRowElement.bind(this, i),
                    onArrowDown: this.focusRow.bind(this, i + 1),
                    onArrowUp: this.focusRow.bind(this, i - 1),
                    persons: this.props.persons,
                    columns: data.counts,
                    nameValue: data.name,
                    personValue: data.profile_id,
                    onFocus: this.onFocus.bind(this, i),
                    onChange: this.onChangeCell.bind(this, i),
                    onChangeName: this.onChangeName.bind(this, i) }));
                if (data.image !== null) {
                    rows.push(React.createElement(
                        'div',
                        { key: i + 'img', className: 'image', style: {
                                'width': data.image.width + 'px',
                                'height': data.image.stop - data.image.start + 'px',
                                'position': 'relative',
                                'overflow': 'hidden' } },
                        React.createElement('img', { src: data.image.url, style: {
                                'top': -data.image.start + 'px',
                                'position': 'absolute' } })
                    ));
                }
            }
            return React.createElement(
                'div',
                { className: 'sheet' },
                React.createElement(
                    'div',
                    { className: 'sheetrow sheetrow-header' },
                    React.createElement('div', { className: 'name' }),
                    React.createElement(
                        'div',
                        { className: 'column column-1' },
                        'øl',
                        React.createElement('br', null),
                        '(',
                        counts[0],
                        ')'
                    ),
                    React.createElement(
                        'div',
                        { className: 'column column-1ks' },
                        'ks',
                        React.createElement('br', null),
                        '(',
                        counts[1],
                        ')'
                    ),
                    React.createElement(
                        'div',
                        { className: 'column column-2' },
                        'guldøl',
                        React.createElement('br', null),
                        '(',
                        counts[2],
                        ')'
                    ),
                    React.createElement(
                        'div',
                        { className: 'column column-2ks' },
                        'ks',
                        React.createElement('br', null),
                        '(',
                        counts[3],
                        ')'
                    ),
                    React.createElement(
                        'div',
                        { className: 'column column-3' },
                        'sodavand',
                        React.createElement('br', null),
                        '(',
                        counts[4],
                        ')'
                    ),
                    React.createElement(
                        'div',
                        { className: 'column column-3ks' },
                        'ks',
                        React.createElement('br', null),
                        '(',
                        counts[5],
                        ')'
                    )
                ),
                rows
            );
        }
    }]);

    return Sheet;
}(React.Component);

var Main = function (_React$Component6) {
    _inherits(Main, _React$Component6);

    function Main() {
        _classCallCheck(this, Main);

        return _possibleConstructorReturn(this, (Main.__proto__ || Object.getPrototypeOf(Main)).apply(this, arguments));
    }

    _createClass(Main, [{
        key: 'render',
        value: function render() {
            var persons = window.TK_PROFILES;
            return React.createElement(Sheet, { persons: persons });
        }
    }]);

    return Main;
}(React.Component);

function init_react() {
    var container = document.getElementById('sheet-container');
    ReactDOM.render(React.createElement(Main, null), container);
}

window.addEventListener('load', init_react, false);/*# sourceMappingURL=regnskab.js.map*/
