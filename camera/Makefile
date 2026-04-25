CC ?= gcc
CFLAGS ?= -O2 -Wall
LDFLAGS ?=

FFMPEG_PREFIX ?= /usr
X264_PREFIX ?= /usr

INC := -I$(FFMPEG_PREFIX)/include -I$(X264_PREFIX)/include
LIB := -L$(FFMPEG_PREFIX)/lib -L$(X264_PREFIX)/lib

COMMON_LIBS := -lavcodec -lavutil -lm -lpthread
RTMP_LIBS := -lavformat -lavcodec -lavutil -lx264 -lm -lpthread

.PHONY: all clean

all: v4l2_rtmp_push v4l2_h264_capture

v4l2_rtmp_push: v4l2_rtmp_push.c capture.c encoder.c rtmp.c
	$(CC) $(CFLAGS) $(INC) -o $@ v4l2_rtmp_push.c capture.c encoder.c rtmp.c $(LIB) $(RTMP_LIBS) $(LDFLAGS)

v4l2_h264_capture: v4l2_h264_capture.c
	$(CC) $(CFLAGS) $(INC) -o $@ v4l2_h264_capture.c $(LIB) $(COMMON_LIBS) -lx264 $(LDFLAGS)

clean:
	rm -f v4l2_rtmp_push v4l2_h264_capture
