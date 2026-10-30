# Third-party notices

The Android app (`android/`) bundles the following third-party components in `android/app/src/main/assets/`. The web version (`app.py`) loads the same libraries from CDNs.

## Chess piece images (`img/pieces/`)

The piece images are the "Wikipedia" piece set by Colin M.L. Burnett (Cburnett), as distributed with Chessboard.js. They are licensed under [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (CC BY-SA 3.0). Source: <https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces>. The images are used unmodified. The CC BY-SA license applies to these images only, not to the rest of this project.

## Chess.js 0.10.3 (`lib/chess.min.js`)

<https://github.com/jhlywa/chess.js> - BSD 2-Clause License

```
Copyright (c) 2020, Jeff Hlywa (jhlywa@gmail.com)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

## Chessboard.js 1.0.0 (`lib/chessboard.min.js`, `lib/chessboard.min.css`)

<https://github.com/oakmac/chessboardjs> - MIT License. Copyright 2019 Chris Oakman. License: <https://chessboardjs.com/license>

## jQuery 3.6.0 (`lib/jquery.min.js`)

<https://jquery.com> - MIT License. Copyright OpenJS Foundation and other contributors. License: <https://jquery.org/license>

## Android libraries and Gradle

The APK also contains AndroidX, AndroidX WebKit, Kotlin and kotlinx.coroutines libraries, all licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). The Gradle wrapper (`android/gradle/wrapper/gradle-wrapper.jar`) is also Apache 2.0.
