#include <errno.h>
#include <fcntl.h>
#include <libavcodec/avcodec.h>
#include <libavutil/avutil.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <linux/videodev2.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#define DEFAULT_DEVICE "/dev/video0"
#define DEFAULT_OUTPUT "out.h264"
#define DEFAULT_WIDTH 320
#define DEFAULT_HEIGHT 240
#define DEFAULT_FPS 15
#define DEFAULT_FRAMES 150
#define BUFFER_COUNT 4

struct buffer {
    void *start;
    size_t length;
};

struct capture_context {
    int fd;
    char device[256];
    unsigned int width;
    unsigned int height;
    unsigned int fps;
    struct buffer *buffers;
    unsigned int buffer_count;
};

struct encode_context {
    const AVCodec *codec;
    AVCodecContext *codec_ctx;
    AVFrame *frame;
    AVPacket *pkt;
    FILE *outfile;
    int64_t next_pts;
};

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [device] [output.h264] [width] [height] [fps] [frames]\n"
            "Example: %s /dev/video0 out.h264 320 240 15 150\n",
            prog, prog);
}

static int xioctl(int fd, unsigned long request, void *arg)
{
    int ret;

    do {
        ret = ioctl(fd, request, arg);
    } while (ret == -1 && errno == EINTR);

    return ret;
}

static void close_capture(struct capture_context *cap)
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
            if (cap->buffers[i].start && cap->buffers[i].length > 0) {
                munmap(cap->buffers[i].start, cap->buffers[i].length);
            }
        }
        free(cap->buffers);
        cap->buffers = NULL;
    }

    if (cap->fd >= 0) {
        close(cap->fd);
        cap->fd = -1;
    }
}

static void close_encoder(struct encode_context *enc)
{
    if (!enc) {
        return;
    }

    if (enc->outfile) {
        fclose(enc->outfile);
        enc->outfile = NULL;
    }

    if (enc->pkt) {
        av_packet_free(&enc->pkt);
    }

    if (enc->frame) {
        av_frame_free(&enc->frame);
    }

    if (enc->codec_ctx) {
        avcodec_free_context(&enc->codec_ctx);
    }
}

static int init_capture(struct capture_context *cap)
{
    struct v4l2_capability caps;
    struct v4l2_format fmt;
    struct v4l2_streamparm parm;
    struct v4l2_requestbuffers req;
    unsigned int i;

    memset(&caps, 0, sizeof(caps));
    memset(&fmt, 0, sizeof(fmt));
    memset(&parm, 0, sizeof(parm));
    memset(&req, 0, sizeof(req));

    cap->fd = open(cap->device, O_RDWR | O_NONBLOCK, 0);
    if (cap->fd < 0) {
        perror("open video device");
        return -1;
    }

    if (xioctl(cap->fd, VIDIOC_QUERYCAP, &caps) < 0) {
        perror("VIDIOC_QUERYCAP");
        return -1;
    }

    if (!(caps.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
        fprintf(stderr, "Device does not support video capture\n");
        return -1;
    }

    if (!(caps.capabilities & V4L2_CAP_STREAMING)) {
        fprintf(stderr, "Device does not support streaming I/O\n");
        return -1;
    }

    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.width = cap->width;
    fmt.fmt.pix.height = cap->height;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    fmt.fmt.pix.field = V4L2_FIELD_NONE;

    if (xioctl(cap->fd, VIDIOC_S_FMT, &fmt) < 0) {
        perror("VIDIOC_S_FMT");
        return -1;
    }

    if (fmt.fmt.pix.pixelformat != V4L2_PIX_FMT_YUYV) {
        fprintf(stderr, "Driver did not accept YUYV format\n");
        return -1;
    }

    cap->width = fmt.fmt.pix.width;
    cap->height = fmt.fmt.pix.height;

    parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    parm.parm.capture.timeperframe.numerator = 1;
    parm.parm.capture.timeperframe.denominator = cap->fps;
    xioctl(cap->fd, VIDIOC_S_PARM, &parm);

    req.count = BUFFER_COUNT;
    req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;

    if (xioctl(cap->fd, VIDIOC_REQBUFS, &req) < 0) {
        perror("VIDIOC_REQBUFS");
        return -1;
    }

    if (req.count < 2) {
        fprintf(stderr, "Insufficient V4L2 buffers: %u\n", req.count);
        return -1;
    }

    cap->buffers = calloc(req.count, sizeof(*cap->buffers));
    if (!cap->buffers) {
        perror("calloc buffers");
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

    printf("Capture initialized: %s %ux%u YUYV fps=%u buffers=%u\n",
           cap->device, cap->width, cap->height, cap->fps, cap->buffer_count);
    return 0;
}

static void yuyv_to_yuv420p(const uint8_t *src, AVFrame *frame,
                            unsigned int width, unsigned int height)
{
    unsigned int x;
    unsigned int y;
    uint8_t *dst_y = frame->data[0];
    uint8_t *dst_u = frame->data[1];
    uint8_t *dst_v = frame->data[2];
    int stride_y = frame->linesize[0];
    int stride_u = frame->linesize[1];
    int stride_v = frame->linesize[2];

    for (y = 0; y < height; ++y) {
        const uint8_t *line = src + y * width * 2;
        uint8_t *out_y = dst_y + y * stride_y;

        for (x = 0; x < width; x += 2) {
            out_y[x] = line[x * 2];
            out_y[x + 1] = line[x * 2 + 2];
        }
    }

    for (y = 0; y < height; y += 2) {
        const uint8_t *line = src + y * width * 2;
        uint8_t *out_u = dst_u + (y / 2) * stride_u;
        uint8_t *out_v = dst_v + (y / 2) * stride_v;

        for (x = 0; x < width; x += 2) {
            out_u[x / 2] = line[x * 2 + 1];
            out_v[x / 2] = line[x * 2 + 3];
        }
    }
}

static int write_encoded_packets(struct encode_context *enc)
{
    int ret;

    while (1) {
        ret = avcodec_receive_packet(enc->codec_ctx, enc->pkt);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return 0;
        }
        if (ret < 0) {
            fprintf(stderr, "avcodec_receive_packet failed: %s\n",
                    av_err2str(ret));
            return -1;
        }

        if (fwrite(enc->pkt->data, 1, enc->pkt->size, enc->outfile) !=
            (size_t)enc->pkt->size) {
            perror("fwrite packet");
            av_packet_unref(enc->pkt);
            return -1;
        }

        printf("encoded packet: pts=%lld dts=%lld size=%d flags=0x%x\n",
               (long long)enc->pkt->pts,
               (long long)enc->pkt->dts,
               enc->pkt->size,
               enc->pkt->flags);

        av_packet_unref(enc->pkt);
    }
}

static int init_encoder(struct encode_context *enc,
                        unsigned int width, unsigned int height,
                        unsigned int fps, const char *output_path)
{
    int ret;

    memset(enc, 0, sizeof(*enc));

    enc->codec = avcodec_find_encoder_by_name("libx264");
    if (!enc->codec) {
        enc->codec = avcodec_find_encoder(AV_CODEC_ID_H264);
    }
    if (!enc->codec) {
        fprintf(stderr, "No H.264 encoder found in current FFmpeg build\n");
        return -1;
    }

    enc->codec_ctx = avcodec_alloc_context3(enc->codec);
    if (!enc->codec_ctx) {
        fprintf(stderr, "avcodec_alloc_context3 failed\n");
        return -1;
    }

    enc->codec_ctx->codec_type = AVMEDIA_TYPE_VIDEO;
    enc->codec_ctx->codec_id = enc->codec->id;
    enc->codec_ctx->width = (int)width;
    enc->codec_ctx->height = (int)height;
    enc->codec_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    enc->codec_ctx->time_base = (AVRational){1, (int)fps};
    enc->codec_ctx->framerate = (AVRational){(int)fps, 1};
    enc->codec_ctx->bit_rate = 400000;
    enc->codec_ctx->gop_size = (int)fps * 2;
    enc->codec_ctx->max_b_frames = 0;

    if (strcmp(enc->codec->name, "libx264") == 0) {
        av_opt_set(enc->codec_ctx->priv_data, "preset", "ultrafast", 0);
        av_opt_set(enc->codec_ctx->priv_data, "tune", "zerolatency", 0);
    }

    ret = avcodec_open2(enc->codec_ctx, enc->codec, NULL);
    if (ret < 0) {
        fprintf(stderr, "avcodec_open2 failed: %s\n", av_err2str(ret));
        return -1;
    }

    enc->frame = av_frame_alloc();
    if (!enc->frame) {
        fprintf(stderr, "av_frame_alloc failed\n");
        return -1;
    }

    enc->frame->format = enc->codec_ctx->pix_fmt;
    enc->frame->width = enc->codec_ctx->width;
    enc->frame->height = enc->codec_ctx->height;

    ret = av_frame_get_buffer(enc->frame, 32);
    if (ret < 0) {
        fprintf(stderr, "av_frame_get_buffer failed: %s\n", av_err2str(ret));
        return -1;
    }

    enc->pkt = av_packet_alloc();
    if (!enc->pkt) {
        fprintf(stderr, "av_packet_alloc failed\n");
        return -1;
    }

    enc->outfile = fopen(output_path, "wb");
    if (!enc->outfile) {
        perror("fopen output");
        return -1;
    }

    printf("Encoder initialized: codec=%s output=%s %ux%u fps=%u bitrate=%lld\n",
           enc->codec->name, output_path, width, height, fps,
           (long long)enc->codec_ctx->bit_rate);
    return 0;
}

static int encode_one_frame(struct encode_context *enc, const uint8_t *yuyv,
                            unsigned int width, unsigned int height)
{
    int ret;

    ret = av_frame_make_writable(enc->frame);
    if (ret < 0) {
        fprintf(stderr, "av_frame_make_writable failed: %s\n", av_err2str(ret));
        return -1;
    }

    yuyv_to_yuv420p(yuyv, enc->frame, width, height);
    enc->frame->pts = enc->next_pts++;

    ret = avcodec_send_frame(enc->codec_ctx, enc->frame);
    if (ret < 0) {
        fprintf(stderr, "avcodec_send_frame failed: %s\n", av_err2str(ret));
        return -1;
    }

    return write_encoded_packets(enc);
}

static int flush_encoder(struct encode_context *enc)
{
    int ret;

    ret = avcodec_send_frame(enc->codec_ctx, NULL);
    if (ret < 0) {
        fprintf(stderr, "flush avcodec_send_frame failed: %s\n", av_err2str(ret));
        return -1;
    }

    return write_encoded_packets(enc);
}

static int capture_and_encode(struct capture_context *cap, struct encode_context *enc,
                              unsigned int target_frames)
{
    unsigned int captured = 0;

    while (captured < target_frames) {
        fd_set fds;
        struct timeval tv;
        int ret;
        struct v4l2_buffer buf;

        FD_ZERO(&fds);
        FD_SET(cap->fd, &fds);
        tv.tv_sec = 2;
        tv.tv_usec = 0;

        ret = select(cap->fd + 1, &fds, NULL, NULL, &tv);
        if (ret < 0) {
            if (errno == EINTR) {
                continue;
            }
            perror("select");
            return -1;
        }
        if (ret == 0) {
            fprintf(stderr, "select timeout\n");
            return -1;
        }

        memset(&buf, 0, sizeof(buf));
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;

        if (xioctl(cap->fd, VIDIOC_DQBUF, &buf) < 0) {
            if (errno == EAGAIN) {
                continue;
            }
            perror("VIDIOC_DQBUF");
            return -1;
        }

        if (buf.index >= cap->buffer_count) {
            fprintf(stderr, "Driver returned invalid buffer index %u\n", buf.index);
            return -1;
        }

        printf("frame=%u bytes=%u index=%u ts=%ld.%06ld\n",
               captured,
               buf.bytesused,
               buf.index,
               (long)buf.timestamp.tv_sec,
               (long)buf.timestamp.tv_usec);

        if (encode_one_frame(enc, (const uint8_t *)cap->buffers[buf.index].start,
                             cap->width, cap->height) < 0) {
            return -1;
        }

        if (xioctl(cap->fd, VIDIOC_QBUF, &buf) < 0) {
            perror("VIDIOC_QBUF recycle");
            return -1;
        }

        ++captured;
    }

    return 0;
}

int main(int argc, char *argv[])
{
    struct capture_context cap;
    struct encode_context enc;
    unsigned int target_frames = DEFAULT_FRAMES;
    const char *output_path = DEFAULT_OUTPUT;

    memset(&cap, 0, sizeof(cap));
    cap.fd = -1;
    cap.width = DEFAULT_WIDTH;
    cap.height = DEFAULT_HEIGHT;
    cap.fps = DEFAULT_FPS;
    snprintf(cap.device, sizeof(cap.device), "%s", DEFAULT_DEVICE);

    if (argc > 1) {
        snprintf(cap.device, sizeof(cap.device), "%s", argv[1]);
    }
    if (argc > 2) {
        output_path = argv[2];
    }
    if (argc > 3) {
        cap.width = (unsigned int)strtoul(argv[3], NULL, 10);
    }
    if (argc > 4) {
        cap.height = (unsigned int)strtoul(argv[4], NULL, 10);
    }
    if (argc > 5) {
        cap.fps = (unsigned int)strtoul(argv[5], NULL, 10);
    }
    if (argc > 6) {
        target_frames = (unsigned int)strtoul(argv[6], NULL, 10);
    }

    if (cap.width == 0 || cap.height == 0 || cap.fps == 0 || target_frames == 0) {
        usage(argv[0]);
        return EXIT_FAILURE;
    }

    if ((cap.width & 1U) || (cap.height & 1U)) {
        fprintf(stderr, "Width and height must be even for YUV420P\n");
        return EXIT_FAILURE;
    }

    if (init_capture(&cap) < 0) {
        close_capture(&cap);
        return EXIT_FAILURE;
    }

    if (init_encoder(&enc, cap.width, cap.height, cap.fps, output_path) < 0) {
        close_capture(&cap);
        close_encoder(&enc);
        return EXIT_FAILURE;
    }

    if (capture_and_encode(&cap, &enc, target_frames) < 0) {
        close_capture(&cap);
        close_encoder(&enc);
        return EXIT_FAILURE;
    }

    if (flush_encoder(&enc) < 0) {
        close_capture(&cap);
        close_encoder(&enc);
        return EXIT_FAILURE;
    }

    close_capture(&cap);
    close_encoder(&enc);

    printf("Done. Encoded %u frames into %s\n", target_frames, output_path);
    return EXIT_SUCCESS;
}
