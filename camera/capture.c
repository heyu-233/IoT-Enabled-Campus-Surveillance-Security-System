#include "capture.h"

#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#define BUFFER_COUNT 4

static int xioctl(int fd, unsigned long request, void *arg)
{
    int ret;

    do {
        ret = ioctl(fd, request, arg);
    } while (ret == -1 && errno == EINTR);

    return ret;
}

int capture_init(struct capture_context *cap, const char *device,
                 unsigned int width, unsigned int height, unsigned int fps)
{
    struct v4l2_capability caps;
    struct v4l2_format fmt;
    struct v4l2_streamparm parm;
    struct v4l2_requestbuffers req;
    unsigned int i;

    memset(cap, 0, sizeof(*cap));
    cap->fd = -1;
    snprintf(cap->device, sizeof(cap->device), "%s", device);
    cap->width = width;
    cap->height = height;
    cap->fps = fps;

    cap->fd = open(cap->device, O_RDWR | O_NONBLOCK, 0);
    if (cap->fd < 0) {
        perror("open video device");
        return -1;
    }

    memset(&caps, 0, sizeof(caps));
    if (xioctl(cap->fd, VIDIOC_QUERYCAP, &caps) < 0) {
        perror("VIDIOC_QUERYCAP");
        return -1;
    }

    if (!(caps.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
        !(caps.capabilities & V4L2_CAP_STREAMING)) {
        fprintf(stderr, "device does not support capture/streaming\n");
        return -1;
    }

    memset(&fmt, 0, sizeof(fmt));
    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.width = cap->width;
    fmt.fmt.pix.height = cap->height;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    fmt.fmt.pix.field = V4L2_FIELD_NONE;

    if (xioctl(cap->fd, VIDIOC_S_FMT, &fmt) < 0) {
        perror("VIDIOC_S_FMT");
        return -1;
    }

    cap->width = fmt.fmt.pix.width;
    cap->height = fmt.fmt.pix.height;

    memset(&parm, 0, sizeof(parm));
    parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    parm.parm.capture.timeperframe.numerator = 1;
    parm.parm.capture.timeperframe.denominator = cap->fps;
    xioctl(cap->fd, VIDIOC_S_PARM, &parm);

    memset(&req, 0, sizeof(req));
    req.count = BUFFER_COUNT;
    req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;

    if (xioctl(cap->fd, VIDIOC_REQBUFS, &req) < 0) {
        perror("VIDIOC_REQBUFS");
        return -1;
    }

    cap->buffers = calloc(req.count, sizeof(*cap->buffers));
    if (!cap->buffers) {
        perror("calloc");
        return -1;
    }
    cap->buffer_count = req.count;

    for (i = 0; i < cap->buffer_count; ++i) {
        struct v4l2_buffer buf;

        memset(&buf, 0, sizeof(buf));
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index = i;

        if (xioctl(cap->fd, VIDIOC_QUERYBUF, &buf) < 0) {
            perror("VIDIOC_QUERYBUF");
            return -1;
        }

        cap->buffers[i].length = buf.length;
        cap->buffers[i].start = mmap(NULL, buf.length, PROT_READ | PROT_WRITE,
                                     MAP_SHARED, cap->fd, buf.m.offset);
        if (cap->buffers[i].start == MAP_FAILED) {
            perror("mmap");
            cap->buffers[i].start = NULL;
            return -1;
        }

        if (xioctl(cap->fd, VIDIOC_QBUF, &buf) < 0) {
            perror("VIDIOC_QBUF");
            return -1;
        }
    }

    {
        enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        if (xioctl(cap->fd, VIDIOC_STREAMON, &type) < 0) {
            perror("VIDIOC_STREAMON");
            return -1;
        }
    }

    return 0;
}

void capture_close(struct capture_context *cap)
{
    unsigned int i;
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (!cap) {
        return;
    }

    if (cap->fd >= 0) {
        xioctl(cap->fd, VIDIOC_STREAMOFF, &type);
    }

    if (cap->buffers) {
        for (i = 0; i < cap->buffer_count; ++i) {
            if (cap->buffers[i].start) {
                munmap(cap->buffers[i].start, cap->buffers[i].length);
            }
        }
        free(cap->buffers);
    }

    if (cap->fd >= 0) {
        close(cap->fd);
    }
}

int capture_dequeue(struct capture_context *cap, unsigned int *index,
                    unsigned int *bytesused, long *tv_sec, long *tv_usec)
{
    fd_set fds;
    struct timeval tv;
    struct v4l2_buffer buf;
    int ret;

    FD_ZERO(&fds);
    FD_SET(cap->fd, &fds);
    tv.tv_sec = 2;
    tv.tv_usec = 0;

    ret = select(cap->fd + 1, &fds, NULL, NULL, &tv);
    if (ret <= 0) {
        if (ret == 0) {
            fprintf(stderr, "select timeout\n");
        } else {
            perror("select");
        }
        return -1;
    }

    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;

    if (xioctl(cap->fd, VIDIOC_DQBUF, &buf) < 0) {
        if (errno == EAGAIN) {
            return 1;
        }
        perror("VIDIOC_DQBUF");
        return -1;
    }

    *index = buf.index;
    *bytesused = buf.bytesused;
    *tv_sec = (long)buf.timestamp.tv_sec;
    *tv_usec = (long)buf.timestamp.tv_usec;
    return 0;
}

int capture_requeue(struct capture_context *cap, unsigned int index)
{
    struct v4l2_buffer buf;

    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = index;

    if (xioctl(cap->fd, VIDIOC_QBUF, &buf) < 0) {
        perror("VIDIOC_QBUF");
        return -1;
    }
    return 0;
}

void capture_yuyv_to_yuv420p(const unsigned char *src, AVFrame *frame,
                             unsigned int width, unsigned int height)
{
    unsigned int x;
    unsigned int y;
    unsigned char *dst_y = frame->data[0];
    unsigned char *dst_u = frame->data[1];
    unsigned char *dst_v = frame->data[2];
    int stride_y = frame->linesize[0];
    int stride_u = frame->linesize[1];
    int stride_v = frame->linesize[2];

    for (y = 0; y < height; y += 2) {
        const unsigned char *line0 = src + y * width * 2;
        const unsigned char *line1 = src + (y + 1) * width * 2;
        unsigned char *out_y0 = dst_y + y * stride_y;
        unsigned char *out_y1 = dst_y + (y + 1) * stride_y;
        unsigned char *out_u = dst_u + (y / 2) * stride_u;
        unsigned char *out_v = dst_v + (y / 2) * stride_v;

        for (x = 0; x < width; x += 2) {
            unsigned int off = x * 2;

            out_y0[x] = line0[off];
            out_y0[x + 1] = line0[off + 2];
            out_y1[x] = line1[off];
            out_y1[x + 1] = line1[off + 2];

            out_u[x / 2] = line0[off + 1];
            out_v[x / 2] = line0[off + 3];
        }
    }
}

