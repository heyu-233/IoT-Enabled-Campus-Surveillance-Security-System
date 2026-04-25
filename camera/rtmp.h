#ifndef RTMP_H
#define RTMP_H

#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>

struct rtmp_output {
    AVFormatContext *fmt_ctx;
    AVStream *video_stream;
    AVRational encoder_time_base;
    char url[512];
};

int rtmp_output_init(struct rtmp_output *out, const char *url,
                     const AVCodecContext *codec_ctx);

int rtmp_output_write_packet(AVPacket *pkt, void *opaque);

int rtmp_output_write_trailer(struct rtmp_output *out);

void rtmp_output_close(struct rtmp_output *out);

#endif
