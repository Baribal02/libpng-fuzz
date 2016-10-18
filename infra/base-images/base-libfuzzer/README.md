# base-libfuzzer
> Abstract base image for libfuzzer builders.

Supported commands:

* `docker run -ti <image_name> [compile]` - builds fuzzers.
* `docker run -ti <image_name> run <fuzzer_name> <fuzzer_options...>` - build fuzzers and start
  specified one with given options.
* `docker run -ti <image_name> /bin/bash` - drop into shell. Run `compile` script
  to start build.

# Image Files Layout

| Location | Description |
| -------- | ----------  |
| `/out/`                | build artifacts should be copied here  |
| `/src/`                | place to checkout source files |
| `/work/`               | used to store intermediate files |
| `/usr/lib/libfuzzer.a` | libfuzzer static library |

# Provided Environment Variables

You *must* use special compiler flags to build your library and fuzzers.
These flags are provided in following environment variables:

| Env Variable    | Description
| -------------   | --------
| `$CC`           | The C compiler binary.
| `$CXX`, `$CCC`  | The C++ compiler binary.
| `$CFLAGS`       | C compiler flags.
| `$CXXFLAGS`     | C++ compiler flags.
| `$FUZZER_LDFLAGS`      | Linker flags for fuzzer binaries.

Many well-crafted build scripts will automatically use these variables. If not,
passing them manually to a build tool might be required.

# Child Image Interface

## Sources

Child image has to checkout all sources it needs to compile fuzzers into
`/src/` directory. When the image is executed, a directory could be mounted
on top of these with local checkouts using
`docker run -v $HOME/my_library:/src/my_library ...`.

## Other Required Files

Following files have to be added by child images:

| File Location   | Description |
| -------------   | ----------- |
| `/src/build.sh` | build script to build the library and its fuzzers |