#!/usr/bin/python3

#
# A port to Python 3 from Arshad Chummun's license-generator 
# (https://github.com/arshad/license-generator.git)
#


import argparse
import sys
import os
from configparser import ConfigParser
from datetime import date


# the directory where all available license templates and only license 
# templates lie
licensedir = os.path.join(os.path.dirname(__file__), 'licenses')

# license template files
license_templates = os.listdir(licensedir)

# license names
license_names = [os.path.splitext(x)[0] for x in license_templates]


def make_parser():
    # Note that the `dest` values of the parser correspond to field names in 
    # the license template files
    parser = argparse.ArgumentParser(description='Generate a license for '
            'your open surce project. See http://choosealicense.com/.', 
            epilog='Forked from '
            'https://github.com/arshad/license-generator.git', 
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--author-name', dest='fullname', 
            metavar='STRING', help='the author\'s name; if not '
            'specified, the program will attempt to look for it at '
            '$HOME/.gitconfig; if .gitconfig is not found, and if interactive '
            'prompt is disabled, and a name is required by the license to '
            'generate, an error will be raised')
    parser.add_argument('-p', '--project-name', dest='project', 
            metavar='STRING', help='the project name; if not specified and if '
            'and the field is required by the license to generate while the '
            'interactive prompt is disabled, an error will be raised')
    parser.add_argument('-o', '--outfile', dest='output_path', metavar='PATH', 
            default='-', help='the name of the output license file; '
            'if not specified or specified as "-", write to stdout')
    parser.add_argument('-y', '--year', help='year to distribute the '
            'underlying piece of software', default=date.today().year, 
            type=int, metavar='INTEGER', dest='year')
    parser.add_argument('-I', dest='interactive_enabled', action='store_false',
            help='disbale any interactive prompts; otherwise interactive '
            'prompt pops up when there is any fields not specified but '
            'required by the specified license')
    parser.add_argument('--prompt-retry', metavar='INTEGER', type=int, 
            dest='prompt_retry', default=3, help='the time to re-prompt after '
            'typing invalid values, after which an error will be raised')
    parser.add_argument('license', choices=license_names, 
            help='the license to generate')
    return parser

def parse_name_from_gitconfig():
    """
    Attempt to parse author name from ~/.gitconfig.

    :return: the name if the name is found; otherwise `None`
    """
    gitconfigfile = os.path.expanduser(os.path.sep.join(['~', 'gitconfig']))
    gitconfig = ConfigParser()
    if gitconfigfile not in gitconfig.read(gitconfigfile):
        return None
    if 'user' not in gitconfig or 'name' not in gitconfig['user']:
        return None
    return gitconfig['user']['name']

def parse_reqfields_licenses():
    """
    Parse the licenses available and find the required fields for each 
    license.

    :return: a dictionary { license: [ ... fields_required ... ] ... }
    """
    license_reqfields = dict()
    for lid, filename in enumerate(map(lambda x: os.path.join(licensedir, x), 
                                       license_templates)):
        with open(filename) as infile:
            content = infile.read()
        fields = set(map(lambda x: x[1:-1],
                         re.findall(r'\[[^\]]+\]', content)))
        license_reqfields[license_names[lid]] = fields
    return license_reqfields

def is_author_valid(author_name):
    return True if len(author_name.strip()) else False

def is_project_valid(project_name):
    return True if len(project_name.strip()) else False

def is_year_valid(year_string):
    try:                                                                    
        year = int(year_string)  # may raise ValueError: not an integer          
        date(year, 1, 1)         # may raise ValueError: `year` out of range     
        return True                                                         
    except ValueError:                                                      
        return False

def show_fullname_prompt(prompt_retry):
    """
    :return: the author's name, or None if the name is empty or comprised of 
             only whitespace characters for more than `prompt_retry` times
    """
    for i in range(prompt_retry):
        answer = input('Author name (non-empty string): ').strip()
        if is_author_valid(answer):
            return answer
    return None

def show_project_prompt(prompt_retry):
    """
    :return: the project's name, or None if the name is empty or comprised of 
             only whitespace characters for more than `prompt_retry` times
    """
    for i in range(prompt_retry):
        answer = input('Project name (non-empty string)? ').strip()
        if is_project_valid(answer):
            return answer
    return None

def show_year_prompt(prompt_retry):
    """
    :return: the distribution year, or None if the year cannot be interpreted 
             as a year for more than `prompt_retry` times
    """
    for i in range(prompt_retry):
        answer = input('Distribution year (%d-%d integer)? ' % 
                (date.min.year, date.max.year)).strip()
        if is_year_valid(answer):
            return int(answer)
    return None

def show_license_prompt(prompt_retry):
    """
    :return: the index of license in `license_templates` to generate, or None 
             if a valid answer is not given within `prompt_retyr` times
    """
    license_name_list = license_names[:]
    for i in range(len(license_name_list)):
        license_name_list[i] = '%d) %s' % (i + 1, license_name_list[i])
    for i in range(prompt_retry):
        print('\n'.join(license_name_list))
        answer = input('Which license (%d-%d integer)? ')
        try:
            option = int(answer)
            if option < 1 or option > len(license_name_list):
                raise ValueError('invalid license option')
            lid = option - 1
            return lid
        except ValueError:
            pass
    return None

def main():
    reqfields = parse_reqfields_licenses()
    args = make_parser().parse_args(sys.argv[1:])
    if args.license is None:
        if args.interactive_enabled:
            lid = show_license_prompt(args.prompt_retry)
            if lid is None:
                sys.stderr.write('No license provided!\n')
                sys.exit(1)
            args.license = license_names[lid]
        sys.stderr.write('No license provided!\n')
        sys.exit(1)
    fields_not_specified = []
    fields_needed = sorted(list(reqfields[args.license]))
    for field_name in fields_needed:
        if field_name not in args:
            if args.interactive_enabled:
                show_prompt = eval('show_%s_prompt' % field_name)
                value = show_prompt(args.prompt_retry)
                if value is None:
                    sys.stderr.write('%s is required by the license!\n'
                            % field_name)
                    sys.exit(1)
                # TODO re-assign unspecified value in args as per prompt
                # continue here ...
            fields_not_specified.append(field_name)
    if len(fields_not_specified):
        sys.stderr.write(', '.join(fields_not_specified)
                + 'is/are required by license `'
                + args.license + '\'!\n')
        sys.exit(1)

