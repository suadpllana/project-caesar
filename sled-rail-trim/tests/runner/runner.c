/*
 * The runner. It owns the apply path and it decides nothing.
 *
 * The part does not live in this process. Every transaction goes out on stdout
 * and the answer comes back on stdin, so the register file, the fault rules and
 * the transaction count all sit on the other side of a pipe, in the grader.
 * There is nothing here to forge: this process cannot make a write happen
 * without the grader performing it, and cannot make the count smaller than the
 * writes it asked for.
 *
 * It carries no expected values and reaches no verdict.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sled.h"

static int faulted;

static void say(const char *line)
{
    fputs(line, stdout);
    fputc('\n', stdout);
    fflush(stdout);
}

static char *listen_line(char *buf, size_t n)
{
    if (!fgets(buf, (int)n, stdin)) {
        exit(0);            /* the grader closed the pipe; nothing to decide */
    }
    buf[strcspn(buf, "\r\n")] = '\0';
    return buf;
}

int sled_bus_write(unsigned addr, unsigned value)
{
    char line[64];
    char reply[64];

    if (faulted) {
        return -1;
    }
    snprintf(line, sizeof line, "W %u %u", addr, value);
    say(line);
    listen_line(reply, sizeof reply);
    if (strncmp(reply, "FAULT", 5) == 0) {
        faulted = 1;
        return -1;
    }
    return 0;
}

int sled_bus_burst(unsigned addr, const unsigned *values, int count)
{
    char line[256];
    char reply[64];
    size_t at;
    int i;

    if (faulted) {
        return -1;
    }
    if (count < 0 || count > 64 || (count > 0 && !values)) {
        faulted = 1;
        return -1;
    }
    at = (size_t)snprintf(line, sizeof line, "B %u %d", addr, count);
    for (i = 0; i < count && at < sizeof line; i++) {
        at += (size_t)snprintf(line + at, sizeof line - at, " %u", values[i]);
    }
    say(line);
    listen_line(reply, sizeof reply);
    if (strncmp(reply, "FAULT", 5) == 0) {
        faulted = 1;
        return -1;
    }
    return 0;
}

int sled_bus_read(unsigned addr)
{
    char line[64];
    char reply[64];
    int value;

    if (faulted) {
        return -1;
    }
    snprintf(line, sizeof line, "R %u", addr);
    say(line);
    listen_line(reply, sizeof reply);
    if (strncmp(reply, "VAL ", 4) == 0 && sscanf(reply + 4, "%d", &value) == 1) {
        return value;
    }
    faulted = 1;
    return -1;
}

int main(void)
{
    char line[256];
    int rails = 0;
    int count, i;
    sled_request *reqs;

    setvbuf(stdout, NULL, _IONBF, 0);

    listen_line(line, sizeof line);
    if (sscanf(line, "RAILS %d", &rails) != 1 || rails <= 0 ||
        rails > SLED_MAX_RAILS) {
        say("BAD");
        return 0;
    }
    sled_open(rails);

    for (;;) {
        say("NEXT");
        listen_line(line, sizeof line);
        if (strcmp(line, "DONE") == 0) {
            break;
        }
        if (sscanf(line, "BATCH %d", &count) != 1 || count < 0) {
            say("BAD");
            return 0;
        }
        reqs = count ? calloc((size_t)count, sizeof *reqs) : NULL;
        if (count && !reqs) {
            say("BAD");
            return 0;
        }
        for (i = 0; i < count; i++) {
            int kind = 0, rail = 0, value = 0;
            listen_line(line, sizeof line);
            if (sscanf(line, "%d %d %d", &kind, &rail, &value) != 3) {
                say("BAD");
                free(reqs);
                return 0;
            }
            reqs[i].kind = (sled_kind)kind;
            reqs[i].rail = rail;
            reqs[i].value = value;
        }
        sled_apply(reqs, count);
        free(reqs);
        say("END");
    }
    return 0;
}
