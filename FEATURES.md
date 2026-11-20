# Specification mapping

Derived from the supplied Pro-Pomodoro blueprint:
- Single-screen timer and task preview
- Focus/short break/long break cadence; long break after four focus sessions by default
- Add/select/delete tasks; due date and planned Pomodoro count
- Start, pause, reset controls
- Focus/break completion notifications and sound hooks
- Theme preference and wallpaper/audio file pickers
- Local session analytics and CSV export

Platform adaptation:
- Kivy provides a shared Python UI for Windows and Android.
- PyInstaller workflow builds Windows executable.
- Buildozer workflow builds Android APK.
- iOS-specific SwiftUI/UIKit/CoreData/CloudKit APIs are not used in this cross-platform build.
