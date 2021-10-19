import os
import json
import shutil
import difflib
import functools

@functools.lru_cache(maxsize = None)
def load_public_sources():
    """Loads the public data sources JSON file."""
    with open(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '_assets/public_datasources.json')) as f:
        return json.load(f)

@functools.lru_cache(maxsize = None)
def load_citation_sources():
    """Loads the citation sources JSON file."""
    with open(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '_assets/source_citations.json')) as f:
        return json.load(f)

def maybe_you_meant(name, msg, source = None):
    """Suggests potential correct spellings for an invalid name."""
    source = source if source is not None \
                    else load_public_sources().keys()
    suggestion = difflib.get_close_matches(name, source)
    if len(suggestion) == 0:
        return msg
    return msg + f" Maybe you meant: '{suggestion[0]}'?"

def copyright_print(name, location = None):
    """Prints out license/copyright info after a dataset download."""
    content = load_citation_sources()[name]
    license = content['license'] # noqa
    citation = content['citation']

    def _bold(msg): # noqa
        return '\033[1m' + msg + '\033[0m'
    def _bold_yaml(msg):  # noqa
        return '<|>' + msg + '<|>'

    if location is None:
        first_msg = "Citation information for " + _bold(name) + ".\n"
    else:
        first_msg = "You have just downloaded " + _bold(name) + ".\n"

    _LICENSE_TO_URL = {
        'CC BY SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'MIT': 'https://opensource.org/licenses/MIT',
        'GPL-3.0': 'https://opensource.org/licenses/GPL-3.0'}
    if license == '':
        license_msg = "This dataset has " \
                      + _bold("no license") + ".\n"
    else:
        license_msg = "This dataset is licensed under the " \
                      + _bold(license) + " license.\n"
        license_msg += "To learn more, visit: " \
                       + _LICENSE_TO_URL[license] + "\n"

    if citation == '':
        citation_msg = "This dataset has no associated citation."
    else:
        citation_msg = "When using this dataset, please cite the following:\n\n"
        citation_msg += citation

    columns = shutil.get_terminal_size((80, 24)).columns
    max_print_length = max(min(
        columns, max([len(i) for i in [
            *citation_msg.split('\n'), *license_msg.split('\n')]])), columns)
    print('\n' + '=' * max_print_length)
    print(first_msg)
    print(license_msg)
    print(citation_msg)
    print("\nThis message will " + _bold("not") + " be automatically shown\n" 
          "again. To view this message again, in an AgMLDataLoader\n" +
          "run `loader.info.citation_summary()`. Otherwise, you\n" +
          "can use `agml.data.source(<name>).citation_summary().`\n")

    if location is not None:
        print(f"You can find your dataset at {location}.")
    print('=' * max_print_length)





