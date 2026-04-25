#include "rtmp.h"

#include <stdio.h>
#include <string.h>

int rtmp_output_init(struct rtmp_output *out, const char *url,
                     const AVCodecContext *codec_ctx)
{
    int ret;

    memset(out, 0, sizeof(*out));
    snprintf(out->url, sizeof(out->url), "%s", url);

    ret = avformat_alloc_output_context2(&out->fmt_ctx, NULL, "flv", out->url);
    if (ret < 0 || !out->fmt_ctx) {
        fprintf(stderr, "avformat_alloc_output_context2 failed: %d\n", ret);
        return -1;
    }

    out->video_stream = avformat_new_stream(out->fmt_ctx, NULL);
    if (!out->video_stream) {
        return -1;
    }

    out->encoder_time_base = codec_ctx->time_base;
    out->video_stream->time_base = codec_ctx->time_base;
    out->video_stream->avg_frame_rate = codec_ctx->framerate;

    ret = avcodec_parameters_from_context(out->video_stream->codecpar, codec_ctx);
    if (ret < 0) {
        fprintf(stderr, "avcodec_parameters_from_context failed: %d\n", ret);
        return -1;
    }

    if (!(out->fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        ret = avio_open2(&out->fmt_ctx->pb, out->url, AVIO_FLAG_WRITE, NULL, NULL);
        if (ret < 0) {
            fprintf(stderr, "avio_open2 failed: %d\n", ret);
            return -1;
        }
    }

    ret = avformat_write_header(out->fmt_ctx, NULL);
    if (ret < 0) {
        fprintf(stderr, "avformat_write_header failed: %d\n", ret);
        return -1;
    }

    return 0;
}

int rtmp_output_write_packet(AVPacket *pkt, void *opaque)
{
    struct rtmp_output *out = (struct rtmp_output *)opaque;
    AVPacket local;
    int ret;

    av_init_packet(&local);
    ret = av_packet_ref(&local, pkt);
    if (ret < 0) {
        return -1;
    }

    av_packet_rescale_ts(&local, out->encoder_time_base,
                         out->video_stream->time_base);
    local.stream_index = out->video_stream->index;
    local.duration = 1;
    local.pos = -1;

    ret = av_interleaved_write_frame(out->fmt_ctx, &local);
    av_packet_unref(&local);
    return ret < 0 ? -1 : 0;
}

int rtmp_output_write_trailer(struct rtmp_output *out)
{
    return av_write_trailer(out->fmt_ctx);
}

void rtmp_output_close(struct rtmp_output *out)
{
    if (!out || !out->fmt_ctx) {
        return;
    }

    if (!(out->fmt_ctx->oformat->flags & AVFMT_NOFILE) && out->fmt_ctx->pb) {
        avio_closep(&out->fmt_ctx->pb);
    }
    avformat_free_context(out->fmt_ctx);
    out->fmt_ctx = NULL;
}
