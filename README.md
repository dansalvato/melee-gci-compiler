# Melee GCI Compiler

Melee GCI Compiler is an application and scripting language that makes it easy
for Super Smash Bros. Melee mod developers to inject custom code and data into
Melee save files.

## Background

Melee contains a buffer overflow exploit that can be used to trigger ACE
(Arbitrary Code Execution). Developers can package their own custom code into a
Melee save file, and then trigger the exploit in-game to run their code. This
enables Melee mods to run natively on unmodified consoles using nothing more
than a memory card and a special save file.

The exploit was originally discovered by wParam
([website](http://wparam.com/ssbm/)) in 2008 but went largely unnoticed by the
competitive Melee community, as mods at the time were focused more on wacky fun
than on competitive play.

Starting around 2013, training-focused AR/Gecko codes started to appear, with
complete mod packs soon following, such as the 20XX Training Hack Pack
([Smashboards](https://smashboards.com/threads/the-20xx-melee-training-hack-pack-v4-07-7-04-17.351221/)).

When the save file exploit was rediscovered in 2014, 20XX Tournament Edition
([website](http://www.20xx.me/)) became the second memory card mod and focused
on the competitive Melee community by encouraging tournament organizers to use
it.

In 2018, 20XXTE was used as a base to deliver UCF (Universal Controller Fix) as
a memory card mod ([website](http://www.20xx.me/ucf.html)).

In 2019, UnclePunch's Training Mode
([GitHub](https://github.com/UnclePunch/Training-Mode)) built upon old
knowledge with modern programming tools to deliver a refined and powerful
training toolkit in memory card form.

During Melee's peak competitive years, mod developers were concerned that
memory card mods could be used to easily cheat at major tournaments. So, they
opted for "security by obscurity" and chose not to share the knowledge and
tools they developed to create memory card mods. However, both the modding and
competitive communities have evolved since then. I believe the time has come to
preserve developer knowledge and ensure that this formerly enigmatic capability
becomes accessible to future enthusiasts and competitive players. Preservation
of the past and accessibility for the future are the core reasons I decided to
make Melee GCI Compiler.

## Requirements

Melee GCI Compiler requires Python 3.6 or higher. It also uses pre-compiled GNU
GCC binaries `powerpc-eabi-as`, `powerpc-eabi-ld`, and `powerpc-eabi-objcopy`.
For convenience, x86 binaries for Windows, macOS, and Linux are already
included and will be called with no user configuration needed. ARM binaries are
included for macOS (Apple Silicon) and Linux (Raspberry Pi, etc.).

### macOS

You may get some permission-related errors on macOS. If you get a `Permission
denied` error during ASM compilation, you will need to run `chmod +x` on the
binary files in `mgc/pyiiasmh/bin/darwin_xxxx` (`i386` or `arm64` depending on
your architecture).

It is also likely that macOS will block these binaries from being run due to
being from an unidentified developer. If so, the system will tell you in a
pop-up dialog. To get around this, go to Settings > Security & Privacy >
General, where at the bottom you will find a "Run Anyway" button. You will need
to do this three times, one for each binary. After doing so, run Melee GCI
Compiler again, and the ASM compilation should succeed.

## Documentation

Please see the `doc` folder for basic usage and an overview of the MGC
scripting language features. The `example` folder contains example MGC script
files with plenty of explanation text inside. Please feel free to examine the
example script and try compiling it yourself.

## Bugs

The most obvious sign of bugs is if you receive a Python stack trace - that
means some case has been unhandled. If you want to hunt for bugs, try to cause
stack traces and report them in the issue tracker!

If you believe MGC is mistakenly logging an error or some data is not being
compiled correctly, please feel free to submit those issues as well, and they
will be reviewed.

## Attributions

Thanks to wParam for discovering and documenting the Melee save file exploit.

Thanks to metaconstruct for doing some incredible work to reverse engineer the
encoding/decoding routines Melee uses to obfuscate its save files. Melee GCI
Compiler is possible thanks to that. `meleegci.py` was written by
metaconstruct, and `gci_encode.py`, the GCI encoding/decoding routine, is a
Python re-implementation of his C program.

Thanks to Sean Power for PyiiASMH ([Google
Code](https://code.google.com/archive/p/pyiiasmh/)), a Python wrapper for the
PPC toolchain with a focus on generating Gecko codes, which is used (and
thoroughly butchered) in Melee GCI Compiler.

Thanks to JoshuaMKW for updating and maintaining PyiiASMH
([GitHub](https://github.com/JoshuaMKW/pyiiasmh)) with Python 3 support, even
though I somehow didn't know about it until I started writing this readme, and
therefore didn't use it.

Thanks to all my friends in the Melee modding community. I'm sorry I peaced out
to go make an anime dating sim. Everyone is doing all these incredible things
that I never dreamed would be possible with Melee.
