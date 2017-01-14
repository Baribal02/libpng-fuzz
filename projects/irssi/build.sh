#!/bin/bash -eu
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

# configure script doesn't like the oss-fuzz CFLAGS
./autogen.sh CFLAGS=
export LIB_FUZZING_ENGINE=/usr/lib/libFuzzingEngine.a
./configure --without-textui --with-fuzzer --with-fuzzer-lib=$LIB_FUZZING_ENGINE CC=$CC CXX=$CXX CFLAGS= CXXFLAGS="$CXXFLAGS"
make "-j$(nproc)" CFLAGS="$CFLAGS"

cp $SRC/irssi/src/fe-fuzz/irssi-fuzz $OUT/
