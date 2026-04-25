#include "encoder.h"

#include <libavutil/opt.h>
#include <stdio.h>
#include <string.h>
#include <sys/time.h>

static unsigned long long now_us(void)
{
    struct timeval tv;

    gettimeofday(&tv, NULL);
    return (unsigned long long)tv.tv_sec * 1000000ULL +
           (unsigned long long)tv.tv_usec;
}


static int encoder_drain_packets(struct encoder_context *enc,
                                 encoder_packet_callback cb, void *opaque,
                                struct encoder_stage_stats *stats)
{
    int ret;

    while (1) {
        unsigned long long t0 = now_us();

        ret = avcodec_receive_packet(enc->codec_ctx, enc->pkt);
        if (stats) {
            stats->receive_us += now_us() - t0;
        }

        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return 0;
        }
        if (ret < 0) {
            fprintf(stderr, "avcodec_receive_packet failed: %d\n", ret);
            return -1;
        }

        t0 = now_us();
        if (cb(enc->pkt, opaque) < 0) {
            if (stats) {
                stats->write_us += now_us() - t0;
            }
            av_packet_unref(enc->pkt);
            return -1;
        }
        if (stats) {
            stats->write_us += now_us() - t0;
            stats->packet_count++;
        }

        av_packet_unref(enc->pkt);
    }
}

int encoder_init(struct encoder_context *enc, unsigned int width,
                 unsigned int height, unsigned int fps, int global_header)
{
    int ret;

    memset(enc, 0, sizeof(*enc));

    enc->codec = avcodec_find_encoder_by_name("libx264");
    if (!enc->codec) {
        enc->codec = avcodec_find_encoder(AV_CODEC_ID_H264);
    }
    if (!enc->codec) {
        fprintf(stderr, "H.264 encoder not found\n");
        return -1;
    }

    enc->codec_ctx = avcodec_alloc_context3(enc->codec);
    if (!enc->codec_ctx) {
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

    if (global_header) {
        enc->codec_ctx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }

    if (strcmp(enc->codec->name, "libx264") == 0) {
        av_opt_set(enc->codec_ctx->priv_data, "preset", "ultrafast", 0);
        av_opt_set(enc->codec_ctx->priv_data, "tune", "zerolatency", 0);
    }

    ret = avcodec_open2(enc->codec_ctx, enc->codec, NULL);
    if (ret < 0) {
        fprintf(stderr, "avcodec_open2 failed: %d\n", ret);
        return -1;
    }

    enc->frame = av_frame_alloc();
    enc->pkt = av_packet_alloc();
    if (!enc->frame || !enc->pkt) {
        return -1;
    }

    enc->frame->format = enc->codec_ctx->pix_fmt;
    enc->frame->width = enc->codec_ctx->width;
    enc->frame->height = enc->codec_ctx->height;

    ret = av_frame_get_buffer(enc->frame, 32);
    if (ret < 0) {
        fprintf(stderr, "av_frame_get_buffer failed: %d\n", ret);
        return -1;
    }

    return 0;
}

int encoder_send_yuyv_frame(struct encoder_context *enc, const unsigned char *yuyv,
                            unsigned int width, unsigned int height,
                            void (*convert_fn)(const unsigned char *, AVFrame *,
                                               unsigned int, unsigned int),
                            encoder_packet_callback cb, void *opaque,
                            struct encoder_stage_stats *stats)

{
    int ret;
    unsigned long long t0;

    t0 = now_us();

    ret = av_frame_make_writable(enc->frame);
    if (ret < 0) {
        return -1;
    }

    t0 = now_us();

    convert_fn(yuyv, enc->frame, width, height);
    if (stats) {
        stats->convert_us += now_us() - t0;
    }

    enc->frame->pts = enc->next_pts++;

    t0 = now_us();
    ret = avcodec_send_frame(enc->codec_ctx, enc->frame);
    if (stats) {
        stats->send_us += now_us() - t0;
    }

    if (ret < 0) {
        fprintf(stderr, "avcodec_send_frame failed: %d\n", ret);
        return -1;
    }

    return encoder_drain_packets(enc, cb, opaque, stats);

}

int encoder_flush(struct encoder_context *enc, encoder_packet_callback cb,
                  void *opaque)
{
    int ret;

    ret = avcodec_send_frame(enc->codec_ctx, NULL);
    if (ret < 0) {
        return -1;
    }
    return encoder_drain_packets(enc, cb, opaque, NULL);

}

void encoder_close(struct encoder_context *enc)
{
    if (!enc) {
        return;
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
