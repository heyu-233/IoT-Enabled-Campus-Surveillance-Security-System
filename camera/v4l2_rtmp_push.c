#include "capture.h"
#include "encoder.h"
#include "rtmp.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#include <pthread.h>
#include <unistd.h>



#define DEFAULT_DEVICE "/dev/video0"
#define DEFAULT_URL "rtmp://192.168.1.10:1935/myapp/stream"
#define DEFAULT_WIDTH 320
#define DEFAULT_HEIGHT 240
#define DEFAULT_FPS 15
#define DEFAULT_FRAMES 0
#define REPORT_EVERY 30
#define QUEUE_SIZE 4

static unsigned long long now_us(void);


struct queued_frame {
    unsigned char *data;
    unsigned int capacity;
    unsigned int bytesused;
    long tv_sec;
    long tv_usec;
    int ready;
};

struct frame_queue {
    struct queued_frame frames[QUEUE_SIZE];
    unsigned int read_pos;
    unsigned int write_pos;
    unsigned int count;
    int stop;
    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
};

struct app_context {
    struct capture_context cap;
    struct encoder_context enc;
    struct rtmp_output out;
    struct frame_queue queue;
    unsigned int max_frames;
    unsigned int captured_frames;
    unsigned int processed_frames;
    int capture_done;
};


struct pipeline_stats {
    unsigned long long capture_wait_us;
    unsigned long long encode_total_us;
    unsigned long long requeue_us;
    struct encoder_stage_stats encoder;
    unsigned int frames;
    unsigned long long report_start_us;
};

static void stats_begin(struct pipeline_stats *stats);
static void stats_report_and_reset(const struct pipeline_stats *stats,
                                   unsigned int total_frames);

static int frame_queue_init(struct frame_queue *q, unsigned int frame_bytes)
{
    unsigned int i;

    memset(q, 0, sizeof(*q));

    if (pthread_mutex_init(&q->mutex, NULL) != 0) {
        return -1;
    }
    if (pthread_cond_init(&q->not_empty, NULL) != 0) {
        pthread_mutex_destroy(&q->mutex);
        return -1;
    }

    for (i = 0; i < QUEUE_SIZE; ++i) {
        q->frames[i].data = (unsigned char *)malloc(frame_bytes);
        if (!q->frames[i].data) {
            unsigned int j;
            for (j = 0; j < i; ++j) {
                free(q->frames[j].data);
            }
            pthread_cond_destroy(&q->not_empty);
            pthread_mutex_destroy(&q->mutex);
            return -1;
        }
        q->frames[i].capacity = frame_bytes;
        q->frames[i].ready = 0;
    }

    return 0;
}

static void frame_queue_destroy(struct frame_queue *q)
{
    unsigned int i;

    for (i = 0; i < QUEUE_SIZE; ++i) {
        free(q->frames[i].data);
        q->frames[i].data = NULL;
    }

    pthread_cond_destroy(&q->not_empty);
    pthread_mutex_destroy(&q->mutex);
}

static int frame_queue_push(struct frame_queue *q,
                            const unsigned char *data,
                            unsigned int bytesused,
                            long tv_sec,
                            long tv_usec)
{
    struct queued_frame *slot;

    pthread_mutex_lock(&q->mutex);

    if (q->count == QUEUE_SIZE) {
        q->read_pos = (q->read_pos + 1) % QUEUE_SIZE;
        q->count--;
    }

    slot = &q->frames[q->write_pos];
    if (bytesused > slot->capacity) {
        pthread_mutex_unlock(&q->mutex);
        return -1;
    }

    memcpy(slot->data, data, bytesused);
    slot->bytesused = bytesused;
    slot->tv_sec = tv_sec;
    slot->tv_usec = tv_usec;
    slot->ready = 1;

    q->write_pos = (q->write_pos + 1) % QUEUE_SIZE;
    q->count++;

    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->mutex);
    return 0;
}

static int frame_queue_pop(struct frame_queue *q,
                           unsigned char *dst,
                           unsigned int capacity,
                           unsigned int *bytesused,
                           long *tv_sec,
                           long *tv_usec)
{
    struct queued_frame *slot;

    pthread_mutex_lock(&q->mutex);

    while (q->count == 0 && !q->stop) {
        pthread_cond_wait(&q->not_empty, &q->mutex);
    }

    if (q->count == 0 && q->stop) {
        pthread_mutex_unlock(&q->mutex);
        return -1;
    }

    slot = &q->frames[q->read_pos];
    if (slot->bytesused > capacity) {
        pthread_mutex_unlock(&q->mutex);
        return -1;
    }

    memcpy(dst, slot->data, slot->bytesused);
    *bytesused = slot->bytesused;
    *tv_sec = slot->tv_sec;
    *tv_usec = slot->tv_usec;
    q->read_pos = (q->read_pos + 1) % QUEUE_SIZE;
    q->count--;

    pthread_mutex_unlock(&q->mutex);
    return 0;
}

static void *capture_thread_func(void *arg)
{
    struct app_context *app = (struct app_context *)arg;

    while (app->max_frames == 0 || app->captured_frames < app->max_frames) {
        unsigned int index = 0;
        unsigned int bytesused = 0;
        long tv_sec = 0;
        long tv_usec = 0;
        int dq;

        dq = capture_dequeue(&app->cap, &index, &bytesused, &tv_sec, &tv_usec);
        if (dq > 0) {
            continue;
        }
        if (dq < 0) {
            break;
        }

        if (frame_queue_push(&app->queue,
                             (const unsigned char *)app->cap.buffers[index].start,
                             bytesused, tv_sec, tv_usec) < 0) {
            capture_requeue(&app->cap, index);
            break;
        }

        if (capture_requeue(&app->cap, index) < 0) {
            break;
        }

        app->captured_frames++;
    }

    pthread_mutex_lock(&app->queue.mutex);
    app->queue.stop = 1;
    pthread_cond_broadcast(&app->queue.not_empty);
    pthread_mutex_unlock(&app->queue.mutex);

    app->capture_done = 1;
    return NULL;
}

static void *process_thread_func(void *arg)
{
    struct app_context *app = (struct app_context *)arg;
    struct pipeline_stats stats;
    unsigned char *local_data;
    unsigned int frame_bytes = app->cap.width * app->cap.height * 2;
    unsigned int bytesused = 0;
    long tv_sec = 0;
    long tv_usec = 0;

    local_data = (unsigned char *)malloc(frame_bytes);
    if (!local_data) {
        perror("malloc local_data");
        return NULL;
    }

    stats_begin(&stats);

    while (1) {
        unsigned long long t0;

        if (frame_queue_pop(&app->queue,
                            local_data,
                            frame_bytes,
                            &bytesused,
                            &tv_sec,
                            &tv_usec) < 0) {
            break;
        }

        printf("frame=%u bytes=%u ts=%ld.%06ld\n",
               app->processed_frames,
               bytesused,
               tv_sec,
               tv_usec);

        t0 = now_us();
        if (encoder_send_yuyv_frame(&app->enc,
                                    local_data,
                                    app->cap.width, app->cap.height,
                                    capture_yuyv_to_yuv420p,
                                    rtmp_output_write_packet, &app->out,
                                    &stats.encoder) < 0) {
            break;
        }
        stats.encode_total_us += now_us() - t0;

        app->processed_frames++;
        stats.frames++;

        if ((stats.frames % REPORT_EVERY) == 0) {
            stats_report_and_reset(&stats, app->processed_frames);
            stats_begin(&stats);
        }
    }

    stats_report_and_reset(&stats, app->processed_frames);
    free(local_data);
    return NULL;
}



static unsigned long long now_us(void)
{
    struct timeval tv;

    gettimeofday(&tv, NULL);
    return (unsigned long long)tv.tv_sec * 1000000ULL +
           (unsigned long long)tv.tv_usec;
}

static void stats_begin(struct pipeline_stats *stats)
{
    memset(stats, 0, sizeof(*stats));
    stats->report_start_us = now_us();
}

static void stats_report_and_reset(const struct pipeline_stats *stats,
                                   unsigned int total_frames)
{
    double frames = (double)stats->frames;
    double elapsed_s;
    double fps;

    if (stats->frames == 0) {
        return;
    }

    elapsed_s = (double)(now_us() - stats->report_start_us) / 1000000.0;
    fps = elapsed_s > 0.0 ? frames / elapsed_s : 0.0;

    printf("[perf] total=%u window=%u fps=%.2f wait=%.2fms convert=%.2fms "
           "send=%.2fms recv=%.2fms write=%.2fms encode_total=%.2fms "
           "requeue=%.2fms packets/frame=%.2f\n",
           total_frames,
           stats->frames,
           fps,
           (double)stats->capture_wait_us / frames / 1000.0,
           (double)stats->encoder.convert_us / frames / 1000.0,
           (double)stats->encoder.send_us / frames / 1000.0,
           (double)stats->encoder.receive_us / frames / 1000.0,
           (double)stats->encoder.write_us / frames / 1000.0,
           (double)stats->encode_total_us / frames / 1000.0,
           (double)stats->requeue_us / frames / 1000.0,
           stats->encoder.packet_count ?
               (double)stats->encoder.packet_count / frames : 0.0);
    fflush(stdout);
}


static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [device] [rtmp_url] [width] [height] [fps] [frames]\n",
            prog);
}

int main(int argc, char *argv[])
{
    struct app_context app;
    pthread_t capture_thread;
    pthread_t process_thread;
    const char *device = DEFAULT_DEVICE;
    const char *url = DEFAULT_URL;
    unsigned int width = DEFAULT_WIDTH;
    unsigned int height = DEFAULT_HEIGHT;
    unsigned int fps = DEFAULT_FPS;
    unsigned int frames = DEFAULT_FRAMES;
    unsigned int frame_bytes;
    int ret = EXIT_FAILURE;
 

    memset(&app, 0, sizeof(app));

    if (argc > 1) {
        device = argv[1];
    }
    if (argc > 2) {
        url = argv[2];
    }
    if (argc > 3) {
        width = (unsigned int)strtoul(argv[3], NULL, 10);
    }
    if (argc > 4) {
        height = (unsigned int)strtoul(argv[4], NULL, 10);
    }
    if (argc > 5) {
        fps = (unsigned int)strtoul(argv[5], NULL, 10);
    }
    if (argc > 6) {
        frames = (unsigned int)strtoul(argv[6], NULL, 10);
    }

    if ((width & 1U) || (height & 1U) || fps == 0) {
        usage(argv[0]);
        return EXIT_FAILURE;
    }

    if (capture_init(&app.cap, device, width, height, fps) < 0) {
        goto out;
    }

    if (encoder_init(&app.enc, app.cap.width, app.cap.height, app.cap.fps, 1) < 0) {
        goto out_capture;
    }

    if (rtmp_output_init(&app.out, url, app.enc.codec_ctx) < 0) {
        goto out_encoder;
    }

    frame_bytes = app.cap.width * app.cap.height * 2;
    if (frame_queue_init(&app.queue, frame_bytes) < 0) {
        goto out_rtmp;
    }

    app.max_frames = frames;




    if (pthread_create(&capture_thread, NULL, capture_thread_func, &app) != 0) {
        perror("pthread_create capture");
        goto out_queue;
    }

    if (pthread_create(&process_thread, NULL, process_thread_func, &app) != 0) {
        perror("pthread_create process");
        pthread_mutex_lock(&app.queue.mutex);
        app.queue.stop = 1;
        pthread_cond_broadcast(&app.queue.not_empty);
        pthread_mutex_unlock(&app.queue.mutex);
        pthread_join(capture_thread, NULL);
        goto out_queue;
    }

    pthread_join(capture_thread, NULL);
    pthread_join(process_thread, NULL);

    if (encoder_flush(&app.enc, rtmp_output_write_packet, &app.out) < 0) {
        goto out_queue;
    }
    if (rtmp_output_write_trailer(&app.out) < 0) {
        goto out_queue;
    }

    printf("Done. Pushed stream to %s\n", url);
    ret = EXIT_SUCCESS;




out_queue:
    frame_queue_destroy(&app.queue);
out_rtmp:
    rtmp_output_close(&app.out);
out_encoder:
    encoder_close(&app.enc);
out_capture:
    capture_close(&app.cap);
out:
    return ret;

}
