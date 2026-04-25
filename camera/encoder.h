#ifndef ENCODER_H
#define ENCODER_H

#include <libavcodec/avcodec.h>

struct encoder_context {
    const AVCodec *codec;
    AVCodecContext *codec_ctx;
    AVFrame *frame;
    AVPacket *pkt;
    int64_t next_pts;
};

struct encoder_stage_stats {
    unsigned long long convert_us;
    unsigned long long send_us;
    unsigned long long receive_us;
    unsigned long long write_us;
    unsigned int packet_count;
};


typedef int (*encoder_packet_callback)(AVPacket *pkt, void *opaque);

int encoder_init(struct encoder_context *enc, unsigned int width,
                 unsigned int height, unsigned int fps, int global_header);

int encoder_send_yuyv_frame(struct encoder_context *enc, const unsigned char *yuyv,
                            unsigned int width, unsigned int height,
                            void (*convert_fn)(const unsigned char *, AVFrame *,
                                               unsigned int, unsigned int),
                            encoder_packet_callback cb, void *opaque,
                        struct encoder_stage_stats *stats);

int encoder_flush(struct encoder_context *enc, encoder_packet_callback cb,
                  void *opaque);

void encoder_close(struct encoder_context *enc);

#endif
