[app]
title = Pro-Pomodoro
package.name = propomodoro
package.domain = com.krishna
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,wav,mp3,ogg
version = 1.0.0
requirements = python3,kivy,plyer
orientation = portrait
fullscreen = 0
android.permissions = VIBRATE,POST_NOTIFICATIONS,READ_MEDIA_IMAGES,READ_MEDIA_AUDIO
android.api = 35
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

