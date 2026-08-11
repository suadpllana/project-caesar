/*
 * A bench part, so a batch can be watched going down the wire instead of
 * reasoned about in the abstract.
 *
 * The model here follows the datasheet in /app/README.md exactly: the same
 * register map, the same mode gate, the same settling, the same frame, the
 * same ways to fault. It prints every transaction and the total at the end.
 *
 * Build and run it with `make sandbox && ./sandbox` from /app. Nothing in this
 * file is graded, and it is fingerprinted, so copy it somewhere else if you
 * want to change what it pushes through.
 */
#include <stdio.h>
#include <string.h>

#include "sled.h"

#define RAILS 6

/* How many looks at the status register a mode change costs before the part
 * answers 1. */
#define SETTLE_LOOKS 2

static int vset[RAILS];
static int ilim[RAILS];
static int enabled[RAILS];
static int program;
static int settling;
static int faulted;
static long transactions;

static void fault(const char *code, const char *detail)
{
    faulted = 1;
    printf("    !! FAULT %s (%s)\n", code, detail);
}

/* One register landing on the part. The transaction it belongs to has already
 * been counted, because a frame carries several of these for one flat cost. */
static int put(unsigned addr, unsigned value)
{
    char detail[72];

    if (addr == SLED_MODE) {
        if ((int)value != program) {
            program = (int)value;
            settling = SETTLE_LOOKS;
        }
        return 0;
    }
    if (addr == SLED_STATUS) {
        fault("STATUS_READONLY", "status is read only");
        return -1;
    }
    if (settling) {
        fault("NOT_SETTLED", "the part had not answered a 1 yet");
        return -1;
    }
    if (addr >= SLED_VSET && addr < SLED_VSET + RAILS) {
        int r = (int)(addr - SLED_VSET);
        if (!program) {
            fault("TRIM_OUT_OF_PROGRAM", "voltage outside program mode");
            return -1;
        }
        if ((int)value > ilim[r]) {
            snprintf(detail, sizeof detail, "rail %d: %u over limit %d", r, value, ilim[r]);
            fault("VSET_OVER_ILIM", detail);
            return -1;
        }
        vset[r] = (int)value;
        return 0;
    }
    if (addr >= SLED_ILIM && addr < SLED_ILIM + RAILS) {
        int r = (int)(addr - SLED_ILIM);
        if (!program) {
            fault("TRIM_OUT_OF_PROGRAM", "limit outside program mode");
            return -1;
        }
        if ((int)value < vset[r] && enabled[r]) {
            snprintf(detail, sizeof detail, "rail %d: limit %u under live %d", r, value, vset[r]);
            fault("ILIM_UNDER_LOAD", detail);
            return -1;
        }
        ilim[r] = (int)value;
        return 0;
    }
    if (addr >= SLED_PAIR && addr < SLED_PAIR + RAILS) {
        int r = (int)(addr - SLED_PAIR);
        int v = (int)(value & 0xFFu);
        int i = (int)((value >> 8) & 0xFFu);
        if (!program) {
            fault("TRIM_OUT_OF_PROGRAM", "pair outside program mode");
            return -1;
        }
        if (value >> 16) {
            snprintf(detail, sizeof detail, "rail %d: 0x%x is wider than the register", r, value);
            fault("BAD_PAIR", detail);
            return -1;
        }
        if (v > i) {
            snprintf(detail, sizeof detail, "rail %d: voltage %d over limit %d", r, v, i);
            fault("PAIR_INVERTED", detail);
            return -1;
        }
        /* Both halves at once, so there is no instant in between for the part
         * to object to and the rail's enable does not come into it. */
        vset[r] = v;
        ilim[r] = i;
        return 0;
    }
    if (addr >= SLED_CFG && addr < SLED_CFG + RAILS) {
        int r = (int)(addr - SLED_CFG);
        if (program) {
            fault("CFG_IN_PROGRAM", "enable inside program mode");
            return -1;
        }
        if ((value & 1u) && !enabled[r] && ilim[r] < vset[r]) {
            snprintf(detail, sizeof detail, "rail %d: limit %d under voltage %d",
                     r, ilim[r], vset[r]);
            fault("ENABLE_UNDER_LIMIT", detail);
            return -1;
        }
        enabled[r] = (int)(value & 1u);
        return 0;
    }
    fault("BAD_ADDR", "no register there");
    return -1;
}

int sled_bus_write(unsigned addr, unsigned value)
{
    transactions++;
    if (faulted) {
        return -1;
    }
    printf("  %3ld  write 0x%02x <- %-6u", transactions, addr, value);
    if (addr == SLED_MODE) {
        printf(" (%s program mode)\n", value ? "enter" : "leave");
    } else if (addr >= SLED_PAIR && addr < SLED_PAIR + RAILS) {
        printf(" (limit %u, voltage %u)\n", (value >> 8) & 0xFFu, value & 0xFFu);
    } else {
        printf("\n");
    }
    return put(addr, value);
}

int sled_bus_burst(unsigned addr, const unsigned *values, int count)
{
    int i;

    transactions += 2;
    if (faulted) {
        return -1;
    }
    printf("  %3ld  frame 0x%02x <-", transactions, addr);
    for (i = 0; i < count; i++) {
        printf(" %u", values[i]);
    }
    printf("   (%d words, two transactions)\n", count);

    if (count < 1 || count > SLED_BURST_MAX) {
        fault("BAD_BURST", "a frame carries one to SLED_BURST_MAX words");
        return -1;
    }
    if (!((addr >= SLED_VSET && addr + (unsigned)count <= SLED_VSET + RAILS) ||
          (addr >= SLED_ILIM && addr + (unsigned)count <= SLED_ILIM + RAILS) ||
          (addr >= SLED_CFG  && addr + (unsigned)count <= SLED_CFG  + RAILS) ||
          (addr >= SLED_PAIR && addr + (unsigned)count <= SLED_PAIR + RAILS))) {
        fault("BAD_ADDR", "a frame has to stay inside one bank");
        return -1;
    }
    /* The controller shifts the address and the length out ahead of the first
     * word, which is time enough for the part to settle. */
    settling = 0;
    for (i = 0; i < count; i++) {
        if (put(addr + (unsigned)i, values[i]) != 0) {
            return -1;
        }
    }
    return 0;
}

int sled_bus_read(unsigned addr)
{
    transactions++;
    if (faulted) {
        return -1;
    }
    printf("  %3ld  read  0x%02x", transactions, addr);
    if (addr == SLED_STATUS) {
        if (settling) {
            settling--;
        }
        printf("   -> %s\n", settling ? "0, still settling" : "1, settled");
        return settling ? 0 : 1;
    }
    if (addr >= SLED_VSET && addr < SLED_VSET + RAILS) {
        printf("   -> %d\n", vset[addr - SLED_VSET]);
        return vset[addr - SLED_VSET];
    }
    if (addr >= SLED_ILIM && addr < SLED_ILIM + RAILS) {
        printf("   -> %d\n", ilim[addr - SLED_ILIM]);
        return ilim[addr - SLED_ILIM];
    }
    if (addr >= SLED_PAIR && addr < SLED_PAIR + RAILS) {
        int r = (int)(addr - SLED_PAIR);
        printf("   -> limit %d, voltage %d\n", ilim[r], vset[r]);
        return (ilim[r] << 8) | vset[r];
    }
    if (addr >= SLED_CFG && addr < SLED_CFG + RAILS) {
        printf("   -> %d\n", enabled[addr - SLED_CFG]);
        return enabled[addr - SLED_CFG];
    }
    printf("\n");
    fault("BAD_ADDR", "no register there");
    return -1;
}

static void show(const char *label)
{
    int r;
    printf("%s\n   ", label);
    for (r = 0; r < RAILS; r++) {
        printf("rail%d[v=%d i=%d %s]  ", r, vset[r], ilim[r], enabled[r] ? "on" : "off");
    }
    printf("\n");
}

int main(void)
{
    /* Power-on defaults, straight out of the datasheet. */
    int r;
    static const sled_request batch[] = {
        { SLED_LIMIT,   0, 95 },
        { SLED_VOLTAGE, 0, 80 },
        { SLED_ENABLE,  1, 0 },
        { SLED_VOLTAGE, 2, 44 },
        { SLED_LIMIT,   3, 96 },
        { SLED_VOLTAGE, 3, 88 },
        { SLED_ENABLE,  4, 0 },
        { SLED_VOLTAGE, 4, 30 },
        { SLED_LIMIT,   4, 20 },
        { SLED_LIMIT,   5, 70 },
    };

    for (r = 0; r < RAILS; r++) {
        vset[r] = 50;
        ilim[r] = 90;
        enabled[r] = 1;
    }
    program = 0;
    settling = 0;

    show("before:");
    printf("\nthe config layer sends a rail at a time, the way it always does:\n");
    sled_open(RAILS);
    sled_apply(batch, (int)(sizeof batch / sizeof batch[0]));
    printf("\n");
    show("after:");
    printf("\n%ld transactions%s\n", transactions, faulted ? ", and it faulted" : "");
    return 0;
}
