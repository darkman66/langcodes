from util import data_filename

LIST_KEYS = {'Description', 'Prefix'}


def parse_file(file):
    """
    Take an open file containing the IANA subtag registry, and yield a
    dictionary of information for each subtag it describes.
    """
    lines = []
    for line in file:
        line = line.rstrip('\n')
        if line == '%%':
            # This is a separator between items. Parse the data we've
            # collected and yield the result.
            for parsed in parse_item(lines):
                yield parsed
            lines = []
        elif line.startswith('  '):
            # This is a continuation line. Concatenate it to the previous
            # line, including one of the spaces.
            lines[-1] += line[1:]
        else:
            lines.append(line)
    for parsed in parse_item(lines):
        yield parsed


def parse_item(lines):
    """
    Given the lines that form a subtag entry (after joining wrapped lines
    back together), parse the data they contain.

    Returns a generator that yields once if there was any data there
    (and an empty generator if this was just the header).
    """
    info = {}
    for line in lines:
        key, value = line.split(': ', 1)
        if key in LIST_KEYS:
            info.setdefault(key, []).append(value)
        else:
            assert key not in info
            info[key] = value

    if 'Subtag' in info or 'Tag' in info:
        yield info


def parse_registry():
    """
    Yield a sequence of dictionaries, containing the info in the included
    IANA subtag registry file.
    """
    with open(data_filename('language-subtag-registry.txt')) as data_file:
        # yield instead of returning, so that we only close the file
        # when finished.
        for parsed in parse_file(data_file):
            yield parsed
