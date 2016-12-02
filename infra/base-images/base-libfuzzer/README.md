# base-libfuzzer
> Abstract base image for libfuzzer builders.

Every project image supports multiple commands that can be invoked through docker after building the image:

<pre>
docker run --rm -ti ossfuzz/<b><i>$project</i></b> <i>&lt;command&gt;</i> <i>&lt;arguments...&gt;</i>
</pre>

# Supported Commands

| Command | Description |
|---------|-------------|
| `compile` (default) | build all fuzzers
| `reproduce <fuzzer_name> <fuzzer_options>` | build all fuzzers and run specified one with `/testcase` content.
| `run <fuzzer_name> <fuzzer_options...>` | build all fuzzers and run specified one with given options.
| `/bin/bash` | drop into shell, execute `compile` script to start build.

# Examples

- *reproduce an issue using the latest OSS-Fuzz build:*

   <pre>
docker run --rm -ti -v <b><i>$testcase_file</i></b>:/testcase ossfuzz/<b><i>$project</i></b> reproduce <b><i>$fuzzer</i></b>
   </pre>

- *reproduce using the local source code:*

    <pre>
    docker run --rm -ti -v <b><i>$project_checkout_dir</i></b>:/src/<b><i>$project</i></b> \
                        -v <b><i>$testcase_file</i></b>:/testcase ossfuzz/<b><i>$project</i></b> reproduce <b><i>$fuzzer</i></b>
    </pre>


# Build Configuration

Build configuration is performed through following environment variables:

| Env Variable     | Description
| -------------    | --------
| `SANITIZER` (`"address"`) | Specifies sanitizer configuration to use. `address` or `undefined`.
| `SANITIZER_FLAGS` | Specify compiler sanitizer flags directly. Overrides `SANITIZER`.

# Examples

- *building sqlite3 fuzzer with UBSan (`SANITIZER=undefined`):*

   <pre>
docker run --rm -ti -e <i>SANITIZER</i>=<i>undefined</i> ossfuzz/sqlite3
   </pre>



# Image Files Layout


| Location | Description |
| -------- | ----------  |
| `/out/` (`$OUT`)       | build artifacts should be copied here  |
| `/src/` (`$SRC`)       | place to checkout source files |
| `/work/`(`$WORK`)      | used to store intermediate files |
| `/usr/lib/libfuzzer.a` | libfuzzer static library |

While files layout is fixed within a container, `$SRC`, `$OUT`, `$WORK` are
provided to be able to write retargetable scripts.


## Compiler Flags

You *must* use special compiler flags to build your project and fuzzers.
These flags are provided in following environment variables:

| Env Variable    | Description
| -------------   | --------
| `$CC`           | The C compiler binary.
| `$CXX`, `$CCC`  | The C++ compiler binary.
| `$CFLAGS`       | C compiler flags.
| `$CXXFLAGS`     | C++ compiler flags.

Many well-crafted build scripts will automatically use these variables. If not,
passing them manually to a build tool might be required.


# Child Image Interface

## Sources

Child image has to checkout all sources it needs to compile fuzzers into
`$SRC` directory. When the image is executed, a directory could be mounted
on top of these with local checkouts using
`docker run -v $HOME/my_project:/src/my_project ...`.

## Other Required Files

Following files have to be added by child images:

| File Location   | Description |
| -------------   | ----------- |
| `$SRC/build.sh` | build script to build the project and its fuzzers |
