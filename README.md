PID Cat
=======

>A fork of JakeWharton/pidcat, with the following PRs merged:
>
>* [#189: New -m REGEX to filter by message](https://github.com/JakeWharton/pidcat/pull/189) (by [johnnylambada](https://github.com/johnnylambada))
>* [#188: fix print encode non utf 8 strings ](https://github.com/JakeWharton/pidcat/pull/188) (by [michael2to3](https://github.com/michael2to3))
>* [#179: Fix Issue #178 and bump version to 2.1.1](https://github.com/JakeWharton/pidcat/pull/179) (by [ozziefallick](https://github.com/ozziefallick))
>* [#174: Fixes #165](https://github.com/JakeWharton/pidcat/pull/174) (by [ramanr1](https://github.com/ramanr1))
>* [#166: Add alternate buffer argument, fixes (#128)](https://github.com/JakeWharton/pidcat/pull/166) (by [michalkielan](https://github.com/michalkielan))
>* [#152: Handle processes with <package>:<process> format](https://github.com/JakeWharton/pidcat/pull/152) (by [nickpalmer](https://github.com/nickpalmer))
>* [#145: Fix blank line cause silent quit.](https://github.com/JakeWharton/pidcat/pull/145) (by [nomadalex](https://github.com/nomadalex))
>* [#135: Add option --proguard-mapping to interpret class names correctly when using proguard](https://github.com/JakeWharton/pidcat/pull/135) (by [fcamel](https://github.com/fcamel))
>* [#133: Set terminal title to current device/emulator name.](https://github.com/JakeWharton/pidcat/pull/133) (by [colriot](https://github.com/colriot))
>* [#131: --colorized argument added for colorized log messages](https://github.com/JakeWharton/pidcat/pull/131) (by [faruktoptas](https://github.com/faruktoptas))
>* [#121: Handle case when passing --current with no running application](https://github.com/JakeWharton/pidcat/pull/121) (by [tokou](https://github.com/tokou))
>* [#119: fix bash completion of package names for the filter arg](https://github.com/JakeWharton/pidcat/pull/119) (by [eighthave](https://github.com/eighthave))
>* [#118: Add timestamps to each message](https://github.com/JakeWharton/pidcat/pull/118) (by [vibhavsinha](https://github.com/vibhavsinha))
>* [#115: Feature : Global ignore list (Issue #79)](https://github.com/JakeWharton/pidcat/pull/115) (by [xgouchet](https://github.com/xgouchet))
>* [#108: Colorization on Windows using colorama](https://github.com/JakeWharton/pidcat/pull/108) (by [oakkitten](https://github.com/oakkitten))
>* [#100: add support for reading arguments from config files](https://github.com/JakeWharton/pidcat/pull/100) (by [ayvazjmm](https://github.com/ayvazjmm))


An update to Jeff Sharkey's excellent [logcat color script][1] which only shows
log entries for processes from a specific application package.

During application development you often want to only display log messages
coming from your app. Unfortunately, because the process ID changes every time
you deploy to the phone it becomes a challenge to grep for the right thing.

This script solves that problem by filtering by application package. Supply the
target package as the sole argument to the python script and enjoy a more
convenient development process.

    pidcat com.oprah.bees.android


Here is an example of the output when running for the Google Plus app:

![Example screen](screen.png)




Install
-------

Get the script:

 *  OS X: Use [Homebrew][2].

         brew install pidcat

    If you need to install the latest development version

        brew unlink pidcat
        brew install --HEAD pidcat

 * Arch Linux : Install the package called `pidcat-git` from the [AUR][4].

 * Others: Download the `pidcat.py` and place it on your PATH.


Make sure that `adb` from the [Android SDK][3] is on your PATH. This script will
not work unless this is that case. That means, when you type `adb` and press
enter into your terminal something actually happens.

On Windows, you can do `pip install colorama` if you see weird arrows instead of
colors. In case that does not help, try using option `-f`.

To include `adb` and other android tools on your path:

    export PATH=$PATH:<path to Android SDK>/platform-tools
    export PATH=$PATH:<path to Android SDK>/tools

Include these lines in your `.bashrc` or `.zshrc`.

*Note:* `<path to Android SDK>` should be absolute and not relative.

Configuration
-------------

Arguments can be specified at the command line or in one of the following config files: ~/.pidcat.conf or ./.pidcat.conf

         cat ~/.pidcat.conf
         --min-level=D

Dependencies
------------

`pidcat` requires at least version 8.30 of `coreutils`. Ubuntu 20.04 LTS already ships
with it, for 18.04 and below, `coreutils` can be upgraded from the `focal` repo by running
the following:

```shell
sudo add-apt-repository 'deb http://archive.ubuntu.com/ubuntu focal main restricted universe multiverse'
sudo apt-get update
sudo apt-get -t focal install coreutils
```

 [1]: http://jsharkey.org/blog/2009/04/22/modifying-the-android-logcat-stream-for-full-color-debugging/
 [2]: http://brew.sh
 [3]: http://developer.android.com/sdk/
 [4]: https://aur.archlinux.org/packages/pidcat-git/
