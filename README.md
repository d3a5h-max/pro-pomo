# Pro-Pomodoro — Windows + Android

A shared Kivy implementation based on the supplied Pro-Pomodoro blueprint.

## Included
- Focus, short-break and long-break countdowns
- Long break after configurable number of focus sessions
- Task list, due-date field, planned/completed Pomodoros, active task
- Pause, reset and keyboard Space shortcut on desktop
- Dark/light preference, wallpaper image selection preference
- Alarm sound selection and custom WAV/MP3/OGG selection
- Optional vibration and notifications where supported by the platform
- Session history, streak counter, analytics summary and CSV log
- Local JSON persistence (no account or cloud sync)

## Run on Windows for testing
Install Python 3.11, then double-click `run_windows.bat`.

## Build Windows EXE
On Windows, double-click `build_windows.bat`. The executable is created in:
`dist\\ProPomodoro\\ProPomodoro.exe`

Or push this folder to a GitHub repository and run **Actions → Build Windows EXE**.
Download the `ProPomodoro-Windows-EXE` artifact from the completed workflow.

## Build Android APK
Use Linux (Ubuntu) or GitHub Actions. Push this folder to a GitHub repository and run
**Actions → Build Android APK**. Download `ProPomodoro-Android-APK` from the completed
workflow. The APK is a debug build; Android may ask you to allow installation from
the browser/files app.

## Notes / current implementation limits
- This is a cross-platform implementation, not a native SwiftUI/iOS app.
- Wallpaper selection is stored as a preference; this first build uses its adaptive
  theme background rather than compositing the chosen photo behind the interface.
- Built-in sound names are selectable; custom audio files are played when the platform
  audio backend supports the chosen format. Notification/vibration support depends on
  Android permissions and device behavior.
- CloudKit/iCloud sync, multi-layer AVAudioEngine alarms, polished animated ring,
  chart visualizations, and App Store signing are not implemented in this starter build.
- Android release signing and Google Play publishing require your own signing key and
  developer account.
