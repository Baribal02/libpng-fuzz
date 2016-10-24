# Oss-fuzz Overview
> Applying fuzzing on a scale to common open source software.

> *Warning: This document is a work in progress.*

## Background

[Fuzz testing](https://en.wikipedia.org/wiki/Fuzz_testing) is a well-known
technique for uncovering certain types of programming errors in software.
Many detectable errors (e.g. buffer overruns) have real security
implications.

Our previous experience applying [libFuzzer](http://llvm.org/docs/LibFuzzer.html)
to do [guided in-process fuzzing of Chrome components](https://security.googleblog.com/2016/08/guided-in-process-fuzzing-of-chrome.html)
has proved very successful.


## Goals

Oss-fuzz aims to make common open source software more secure by
combining modern white-box fuzzing techniques together with scalable
distributed running.

At the first stage of the project we plan to combine
[libFuzzer](http://llvm.org/docs/LibFuzzer.html) with various `clang`
[sanitizers](https://github.com/google/sanitizers).
[ClusterFuzz](https://blog.chromium.org/2012/04/fuzzing-for-security.html)
provides distributed fuzzer execution environment and reporting.

## Process Overview

The following process is used for targets in oss-fuzz:

- a target is accepted to oss-fuzz.
- oss-fuzz build server build target fuzzers  regularly and submits them to
  ClusterFuzz for execution.
- ClusterFuzz continuously executes target fuzzers
- when fuzzing uncovers an issue, ClusterFuzz creates an internal testcase.
- issues are automatically triaged and filed in the oss-fuzz [testcase issue
  tracker](https://bugs.chromium.org/p/oss-fuzz/issues/list).
  The issue is visible to *oss-fuzz engineers only*.
  ([Example issue](https://bugs.chromium.org/p/oss-fuzz/issues/detail?id=9).)
- if the target project has a defined process for reporting security issues,
  we will follow it, otherwise we will cc library contact engineers on an issue.
  The issue becomes visible to *CCed people*.
- library engineers fix the issue and land the fix upstream.
- fuzzing infrastructure automatically verifies the fix, adds a comment and
  closes the issue.
- after the issue is fixed or after 90 days since reporting has passed the issue
  becomes *public*.

See [Life of a Bug](life_of_a_bug.md) for more information about handling bugs.

## Accepting New Targets

To be accepted to oss-fuzz, a target must be an open-source project with either
a significant user base or it has to be critical to a global IT infrastructure.

To submit a new target to oss-fuzz:
- create a pull request and provide the following information:
  * project site and details
  * source code repository location
  * a link to the project security issue reporting process *OR*
  * an e-mail of the engineering contact person to be CCed on issue. This
    has to be an established project committer e-mail (present in VCS logs)
    If this is not you, the committer has to acknowledge theirself.
    This e-mail will also be publicly listed in our [Projects](projects.md)
    page.
- once accepted by an oss-fuzz project member, follow the [New Library Guide](new_library.md)
  to write the code.


## Disclosure Guidelines

Following Google's standard [disclosure policy](https://googleprojectzero.blogspot.com/2015/02/feedback-and-data-driven-updates-to.html)
oss-fuzz will adhere to following disclosure principles:
  - **90-day deadline**. After notifying library authors, we will open reported
    issues in 90 days, or sooner if the fix is released.
  - **Weekends and holidays**. If a deadline is due to expire on a weekend or
    US public holiday, the deadline will be moved to the next normal work day.
  - **Grace period**. We will have a 14-day grace period. If a 90-day deadline
    will expire but library engineers let us know before the deadline that a
    patch is scheduled for release on a specific day within 14 days following
    the deadline, the public disclosure will be delayed until the availability
    of the patch.
