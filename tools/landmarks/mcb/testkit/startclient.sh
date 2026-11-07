#!/bin/bash
# start the test client (connects to the local test server)
cd /root/optest && (SDL_VIDEO_FORCE_EGL=1 DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe JAVA_HOME=/root/jdk/jdk-25.0.5+8 PATH=/root/jdk/jdk-25.0.5+8/bin:$PATH setsid nohup sh ./gradlew runClient --no-daemon > /root/client.log 2>&1 &)
