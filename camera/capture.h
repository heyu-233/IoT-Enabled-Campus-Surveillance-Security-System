#ifndef CAPTURE_H
#define CAPTURE_H

#include <libavutil/frame.h>
#include <stddef.h>

struct capture_buffer {
    void *start;
    size_t length;
};

struct capture_context {
    int fd;
    char device[256];
    unsigned int width;
    unsigned int height;
    unsigned int fps;
    struct capture_buffer *buffers;
    unsigned int buffer_count;
};

int capture_init(struct capture_context *cap, const char *device,
                 unsigned int width, unsigned int height, unsigned int fps);

void capture_close(struct capture_context *cap);

int capture_dequeue(struct capture_context *cap, unsigned int *index,
                    unsigned int *bytesused, long *tv_sec, long *tv_usec);

int capture_requeue(struct capture_context *cap, unsigned int index);

void capture_yuyv_to_yuv420p(const unsigned char *src, AVFrame *frame,
                             unsigned int width, unsigned int height);

#endif
