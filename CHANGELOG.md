Change Log
==========

Version 2.2.0-unofficial *(2024-04-07)*
----------------------------

* New: Allow installation via pipx by adding setup.py (#187, @JamesConlan96).
* New: Allow filtering by Regex via `-m` flag (#189, @johnnylambada).
* New: Add alternate buffer support via `-b` flag (#166, @michaelkielan).
* New: Add support for `<package>:<process>` format (#152, @nickpalmer).
* New: Add support for Proguard class name interpretation via `--proguard-mapping` (#135, @fcamel).
* New: Set terminal title to device/emulator name (#133, @colriot).
* New: Add `--colorized` to colorize the log messages as well (#131, @faruktoptas).
* New: Add support for reading arguments from a config file called `.pidcat.conf` (located in either `./` or `~/`) (#100, @ayvazjmm).
* New: Added `--force-windows-colors` to force Windows color output (e.g. when the Terminal is TTY but expects Windows colors) (#108, #oakkitten).
* New: Added global tag ignore list via semicolon separated tag list in environment variable `PIDCAT_IGNORED_TAGS` (#115, @xgouchet).
* New: Added `--timestamp` to prepend timestamp to log lines (#118, @vibhavsinha).
* Fix: Bash package-name autocompletion for devices which can't run `ls /data/data` (#119, @eighthave).
* Fix: Correctly handle blank lines instead of silently quitting (#145, @nomadalex).
* Fix: Fallback to showing the full log when `--curent` is present but no application is running instead of crashing (#121, @tokou).
* Fix: Avoid crashing when an API >30 (Android Q+) is used (#164, @ramanr1).
* Fix: Don't encode output with UTF-8 if terminal already uses UTF-8 encoding (#188, @michael2to3).

Version 2.1.1 *(2022-03-08)*
----------------------------

* Fix: Iteration calls are now compatible with Python 3.
* Fix: Color encoding is now compatible with Python 3.


Version 2.1.0 *(2016-09-07)*
----------------------------

 * New: Explicitly run `adb` in 'brief' mode to ensure proper parsing.
 * New: `-a` / `--all` flag shows all logs.
 * Fix: Setting a tag width to 0 now correctly removes tags.

Version 2.0.1 *(2015-09-15)*
----------------------------
* New: Fix colors on Windows. Use options `-f` / `--force-windows-colors` to force conversion
  in case a terminal appears to be a tty. Requires module `colorama`

Version 2.0.0 *(2015-05-25)*
----------------------------

 * New: Display package and process name in birth & death messages.
 * New: Process can be matched in addition to package. For example `com.android.chrome` will match
   all of Chrome's processes, `com.android.chrome:` will match only its main process, and
   `com.android.chrome:sandboxed_process1` will match that specific process name.
 * New: `-c` option clears log before reading logs.
 * New: If data is piped to `pidcat` it will be used as the log source instead of `adb`.
 * New: `-t` / `--tag` option allows filtering by tag name (regex supported).
 * New: `-i` / `--ignore-tag` option allows filtering out tags from the logs by name (regex supported).
 * New: `--version` option reports Pidcat's version.
 * New: Obtain unknown process IDs of currently-running apps.
 * New: `--current` option uses the package of the currently visible app for filtering.
 * New: Bash completion support for package names and device names. Requires manual installation of
   file in `bash_completion.d/`.
 * Fix: Properly match process birth & death from secondary processes.
 * Fix: Support leading spaces in PID numbers.
 * Fix: Default maximum tag length is now 23 (Android's maximum length).
 * Fix: Properly parse Android 5.1+ birth & death messages.


Version 1.4.1 *(2014-01-09)*
----------------------------

 * Fix: Ignore manufacturer-added invalid tag levels.


Version 1.4.0 *(2013-10-12)*
----------------------------

 * Add '--always-display-tags' argument for improved grepping.
 * Ignore bad UTF-8 data.
 * Replace tab characters in log message with four spaces.
 * Package name is now optional.


Version 1.3.1 *(2013-07-12)*
----------------------------

 * Add fatal to log level filtering.
 * Add '-e' and '-d' arguments for quickly selecting the emulator or device.
 * Improve removal of 'nativeGetEnabledTags' log spam.


Version 1.3.0 *(2013-06-19)*
----------------------------

 * Add support for Python 3.
 * Add '-s' argument for specifying device serial.
 * UTF-8 decode log messages.


Version 1.2.1 *(2013-06-14)*
----------------------------

 * Add support for 'fatal' log level.


Version 1.2.0 *(2013-06-13)*
----------------------------

 * Allow multiple packages to be specified.
 * Add argument to filter output based on log level.


Version 1.1.0 *(2013-06-12)*
----------------------------

 * De-duplicate tag name in output.
 * Color strict mode violations and optionally GC messages.
 * Support multiple processes for a package.


Version 1.0.0 *(2013-06-11)*
----------------------------

Initial version.
