#!/usr/bin/env python
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

from __future__ import print_function
import argparse
import os
import pipes
import re
import shutil
import subprocess
import sys
import tempfile
import templates
import time

OSSFUZZ_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BUILD_DIR = os.path.join(OSSFUZZ_DIR, 'build')


def main():
  os.chdir(OSSFUZZ_DIR)
  if not os.path.exists(BUILD_DIR):
    os.mkdir(BUILD_DIR)

  parser = argparse.ArgumentParser('helper.py', description='oss-fuzz helpers')
  parser.add_argument(
      'command',
      help='One of: generate, build_image, build_fuzzers, run_fuzzer, coverage, shell',
      nargs=argparse.REMAINDER)
  args = parser.parse_args()

  if not args.command:
    parser.print_help()
    return 1

  if args.command[0] == 'generate':
    return generate(args.command[1:])
  elif args.command[0] == 'build_image':
    return build_image(args.command[1:])
  elif args.command[0] == 'build_fuzzers':
    return build_fuzzers(args.command[1:])
  elif args.command[0] == 'run_fuzzer':
    return run_fuzzer(args.command[1:])
  elif args.command[0] == 'coverage':
    return coverage(args.command[1:])
  elif args.command[0] == 'shell':
    return shell(args.command[1:])
  else:
    print('Unrecognised command!', file=sys.stderr)
    return 1

  return 0


def _check_library_exists(library_name):
  """Checks if a library exists."""
  if not os.path.exists(os.path.join(OSSFUZZ_DIR, library_name)):
    print(library_name, 'does not exist', file=sys.stderr)
    return False

  return True


def _get_command_string(command):
  """Returns a shell escaped command string."""
  return ' '.join(pipes.quote(part) for part in command)


def _get_version_control_url(library_name):
  """Returns (url, type) for the library."""
  git_regex = re.compile(r'.*git\s*=\s*"(.*?)"\s*')

  with open(os.path.join(OSSFUZZ_DIR, library_name, 'Jenkinsfile')) as f:
    for line in f:
      match = git_regex.match(line)
      if match:
        return match.group(1), 'git'

  return None, None


def build_image(build_args):
  """Build docker image."""
  parser = argparse.ArgumentParser('helper.py build_image')
  parser.add_argument('library_name')
  args = parser.parse_args(build_args)

  if not _check_library_exists(args.library_name):
    return 1

  command = [
        'docker', 'build', '--pull', '-t', 'ossfuzz/' + args.library_name,
        args.library_name
  ]
  print('Running:', _get_command_string(command))

  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    print('docker build failed.', file=sys.stderr)
    return 1

  return 0


def build_fuzzers(build_args):
  """Build fuzzers."""
  parser = argparse.ArgumentParser('helper.py build_fuzzers')
  parser.add_argument('library_name')
  args = parser.parse_args(build_args)

  if build_image(build_args):
    return 1

  command = [
        'docker', 'run', '-i',
        '-v', '%s:/out' % os.path.join(BUILD_DIR, 'out', args.library_name),
        '-t', 'ossfuzz/' + args.library_name,
  ]

  print('Running:', _get_command_string(command))

  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    print('fuzzers build failed.', file=sys.stderr)
    return 1

  return 0


def run_fuzzer(run_args):
  """Runs a fuzzer in the container."""
  parser = argparse.ArgumentParser('helper.py run_fuzzer')
  parser.add_argument('library_name', help='name of the library')
  parser.add_argument('fuzzer_name', help='name of the fuzzer')
  parser.add_argument('fuzzer_args', help='arguments to pass to the fuzzer',
                      nargs=argparse.REMAINDER)
  args = parser.parse_args(run_args)

  if not _check_library_exists(args.library_name):
    return 1

  if not os.path.exists(os.path.join(BUILD_DIR, 'out', args.library_name,
                                     args.fuzzer_name)):
    print(args.fuzzer_name,
          'does not seem to exist. Please run build_fuzzers first.',
          file=sys.stderr)
    return 1

  command = [
      'docker', 'run', '-i',
      '-v', '%s:/out' % os.path.join(BUILD_DIR, 'out'),
      '-t', 'ossfuzz/libfuzzer-runner',
      '/out/%s/%s' %(args.library_name, args.fuzzer_name)
  ] + args.fuzzer_args

  print('Running:', _get_command_string(command))
  pipe = subprocess.Popen(command)
  pipe.communicate()

def coverage(run_args):
  """Runs a fuzzer in the container."""
  parser = argparse.ArgumentParser('helper.py coverage')
  parser.add_argument('--run_time', default=60, help='time in seconds to run fuzzer')
  parser.add_argument('library_name', help='name of the library')
  parser.add_argument('fuzzer_name', help='name of the fuzzer')
  parser.add_argument('fuzzer_args', help='arguments to pass to the fuzzer',
                      nargs=argparse.REMAINDER)
  args = parser.parse_args(run_args)

  if not _check_library_exists(args.library_name):
    return 1

  if not os.path.exists(os.path.join(BUILD_DIR, 'out', args.library_name,
                                     args.fuzzer_name)):
    print(args.fuzzer_name,
          'does not seem to exist. Please run build_fuzzers first.',
          file=sys.stderr)
    return 1

  temp_dir = tempfile.mkdtemp()
  print (args.fuzzer_args)

  command = [
      'docker', 'run', '-i',
      '-v', '%s:/out' % os.path.join(BUILD_DIR, 'out'),
      '-v', '%s:/cov' % temp_dir,
      '-w', '/cov',
      '-e', 'ASAN_OPTIONS=coverage=1,detect_leaks=0',
      '-t', 'ossfuzz/libfuzzer-runner',
      '/out/%s/%s' % (args.library_name, args.fuzzer_name),
      '-max_total_time=%s' % args.run_time
  ] + args.fuzzer_args

  print('Running:', _get_command_string(command))
  pipe = subprocess.Popen(command)
  pipe.communicate()

  command = [
        'docker', 'run', '-i',
        '-v', '%s:/out' % os.path.join(BUILD_DIR, 'out', args.library_name),
        '-v', '%s:/cov' % temp_dir,
        '-v', '%s:/scripts' % os.path.join(OSSFUZZ_DIR, 'scripts'),
        '-w', '/cov',
        '-p', '8001:8001',
        '-t', 'ossfuzz/coverage',
        '/src/coverage/coverage', '/out/%s' % args.fuzzer_name,
  ]

  print('Running:', _get_command_string(command))
  pipe = subprocess.Popen(command)
  pipe.communicate()


def generate(generate_args):
  """Generate empty library files."""
  parser = argparse.ArgumentParser('helper.py generate')
  parser.add_argument('library_name')
  args = parser.parse_args(generate_args)

  try:
    os.mkdir(args.library_name)
  except OSError:
    print(args.library_name, 'already exists.', file=sys.stderr)
    return 1

  with open(os.path.join(args.library_name, 'Jenkinsfile'), 'w') as f:
    f.write(templates.JENKINS_TEMPLATE)

  with open(os.path.join(args.library_name, 'Dockerfile'), 'w') as f:
    f.write(templates.DOCKER_TEMPLATE)

  build_sh_path = os.path.join(args.library_name, 'build.sh')
  with open(build_sh_path, 'w') as f:
    f.write(templates.BUILD_TEMPLATE % args.library_name)

  os.chmod(build_sh_path, 0755)
  return 0


def shell(shell_args):
  """Runs a shell within a docker image."""
  parser = argparse.ArgumentParser('helper.py shell')
  parser.add_argument('library_name', help='name of the library')
  args = parser.parse_args(shell_args)

  if build_image(shell_args):
    return 1

  command = [
        'docker', 'run', '-i',
        '-v', '%s:/out' % os.path.join(BUILD_DIR, 'out', args.library_name),
        '-t', 'ossfuzz/' + args.library_name,
        '/bin/bash'
  ]
  print('Running:', _get_command_string(command))
  pipe = subprocess.Popen(command)
  pipe.communicate()


if __name__ == '__main__':
  sys.exit(main())
