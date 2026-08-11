/*
 * The apply path.
 *
 * A batch arrives from the config layer as a list of settings, in the order
 * that layer produced them. That layer restates whole rails, so most of what a
 * batch carries is already in force; what the part is asked for here is only
 * the difference between where it stands and where the batch's last word on
 * each register puts it.
 *
 * Nothing else on the sled touches the part and the reset state is in the
 * datasheet, so the apply path knows every register without reading one back.
 * That leaves four things to spend on: the writes that actually change
 * something, the mode moves those writes have to sit inside, the settling each
 * mode move costs, and the frames that carry several writes for the price of
 * two. A batch is resolved to a per-rail target first and then put on the wire
 * in at most three windows:
 *
 *   A  out of program mode  drop the rails the batch leaves under their own
 *                           limit, because nothing else can be done to them
 *                           while they are up
 *   B  in program mode      the trims: pair words first, then the voltages and
 *                           the limits of the rails a pair word cannot describe
 *   C  out of program mode  every remaining enable move
 *
 * Window A is only opened for a rail on its way out of service, so a batch
 * normally costs one mode move for its trims and one for its enables -- or
 * none at all, when it touches only one of the two and the part is already
 * held the right way. The mode is never moved back for its own sake: whichever
 * way a batch leaves the part is where the next one starts.
 *
 * Two things about the part decide the shape of window B. The first is that a
 * pair word lands both halves of a rail's trim in the same beat, so it is
 * checked against itself and nothing else: a live rail can be walked straight
 * down without ever coming out of service, and a rail whose batch moves only
 * one half is written by restating the other. That leaves the pair bank
 * carrying nearly every trim in the batch, which is what makes frames worth
 * having. The rails it cannot describe are the ones the rack leaves parked
 * under their own limit; those want their voltage first and their limit after
 * it, and the limits go last of all because that pass is what puts a rail
 * under its own voltage.
 *
 * The second is settling. A mode move leaves the part unable to take a single
 * write until it has answered two looks at its status register, but a frame
 * carries its own preamble and is taken straight away. So the first thing in a
 * window is worth two transactions more as a single write than as a frame, and
 * the cover below is told which case it is in.
 *
 * Inside a window the writes of one bank are gathered into frames, a frame
 * being billed two whatever it carries. Rails the batch left alone may ride
 * along inside one, rewritten with the value they already hold, but only where
 * that rewrite cannot be refused: a restated pair word faces PAIR_INVERTED and
 * a restated voltage faces VSET_OVER_ILIM, so a rail sitting under its own
 * limit stays out of both. A restated limit and a restated enable are always
 * safe.
 */
#include "sled.h"

#define MAXR SLED_MAX_RAILS

/* Which bank a pass is covering, so the shadow can be kept in step. */
enum bank { BANK_PAIR, BANK_VSET, BANK_ILIM, BANK_CFG };

static int rail_count;
static int in_program;
static int unsettled;           /* a mode move nobody has waited out yet */

/* What the part holds, tracked rather than read back. */
static int cur_v[MAXR];
static int cur_i[MAXR];
static int cur_e[MAXR];

/* The batch, resolved: the last word on each register, and whether the batch
 * said anything about it at all. */
static int say_v[MAXR], say_i[MAXR], say_e[MAXR];
static int tgt_v[MAXR], tgt_i[MAXR], tgt_e[MAXR];

/* The passes. Each is a bank's worth of "this register wants this value". */
static int want[4][MAXR];
static unsigned value[4][MAXR];
#define P_PAIR  0
#define P_VSET  1
#define P_ILIM  2
#define P_CFG   3

static int first_down[MAXR];
static unsigned first_down_val[MAXR];

/* Scratch for the cover below. */
static int pad_ok[MAXR];
static unsigned pad_word[MAXR];
static int best[MAXR + 1][2];
static int how_kind[MAXR + 1][2];       /* 0 skip, 1 single write, 2 frame */
static int how_len[MAXR + 1][2];

static void settle(void)
{
    int look;

    if (!unsettled) {
        return;
    }
    /* The part answers 0 while it is still settling and 1 once it is not. */
    for (look = 0; look < 8; look++) {
        if (sled_bus_read(SLED_STATUS) == 1) {
            break;
        }
    }
    unsettled = 0;
}

static void hold(int program)
{
    if (in_program == program) {
        return;
    }
    sled_bus_write(SLED_MODE, program ? 1u : 0u);
    in_program = program;
    unsettled = 1;
}

/* One register landing, with the shadow kept in step. */
static void landed(enum bank bank, int rail, unsigned word)
{
    switch (bank) {
    case BANK_PAIR:
        cur_i[rail] = (int)((word >> 8) & 0xFFu);
        cur_v[rail] = (int)(word & 0xFFu);
        break;
    case BANK_VSET:
        cur_v[rail] = (int)word;
        break;
    case BANK_ILIM:
        cur_i[rail] = (int)word;
        break;
    case BANK_CFG:
        cur_e[rail] = (int)(word & 1u);
        break;
    }
}

/*
 * Cheapest way to cover one bank's writes.
 *
 * A lone write is billed one, and two more on top when it is the first thing
 * after a mode move, because it has to wait the part out first. A frame of one
 * to SLED_BURST_MAX neighbours is billed two whatever it carries and waits for
 * nothing. need[] marks the registers that have to change; pad_ok[] marks the
 * ones that may be rewritten with what they already hold in order to bridge a
 * gap inside a frame.
 *
 * The pass runs backwards over the bank so that the choice at each register is
 * made against the true cost of the whole tail rather than a greedy guess, and
 * it carries the settling as a second dimension because what is cheapest at
 * the head of a window is not what is cheapest in the middle of one.
 */
static void cover(enum bank bank, unsigned base, const int *need,
                  const unsigned *val)
{
    int n = rail_count;
    int i, j, len, owed, any;

    for (owed = 0; owed < 2; owed++) {
        best[n][owed] = 0;
        how_kind[n][owed] = 0;
        how_len[n][owed] = 1;
    }
    for (i = n - 1; i >= 0; i--) {
        for (owed = 0; owed < 2; owed++) {
            if (need[i]) {
                best[i][owed] = 1 + (owed ? 2 : 0) + best[i + 1][0];
                how_kind[i][owed] = 1;
            } else {
                best[i][owed] = best[i + 1][owed];
                how_kind[i][owed] = 0;
            }
            how_len[i][owed] = 1;
            for (len = 1; len <= SLED_BURST_MAX && i + len <= n; len++) {
                int tail = i + len - 1;
                int cost;
                if (!need[tail] && !pad_ok[tail]) {
                    break;
                }
                any = 0;
                for (j = i; j < i + len; j++) {
                    any |= need[j];
                }
                if (!any) {
                    continue;
                }
                cost = 2 + best[i + len][0];
                if (cost < best[i][owed]) {
                    best[i][owed] = cost;
                    how_kind[i][owed] = 2;
                    how_len[i][owed] = len;
                }
            }
        }
    }

    i = 0;
    owed = unsettled ? 1 : 0;
    while (i < n) {
        int kind = how_kind[i][owed];
        int len = how_len[i][owed];
        if (kind == 2) {
            unsigned words[SLED_BURST_MAX];
            for (j = i; j < i + len; j++) {
                words[j - i] = need[j] ? val[j] : pad_word[j];
            }
            sled_bus_burst(base + (unsigned)i, words, len);
            for (j = i; j < i + len; j++) {
                landed(bank, j, words[j - i]);
            }
            unsettled = 0;
            owed = 0;
        } else if (kind == 1) {
            settle();
            owed = 0;
            sled_bus_write(base + (unsigned)i, val[i]);
            landed(bank, i, val[i]);
        }
        i += len;
    }
}

/* What may be restated inside a frame, and with what, read fresh at the head
 * of every pass because the pass before it may have moved a rail. */
static void pads_for(enum bank bank)
{
    int r;

    for (r = 0; r < rail_count; r++) {
        switch (bank) {
        case BANK_PAIR:
            pad_ok[r] = cur_v[r] <= cur_i[r];
            pad_word[r] = SLED_PAIR_WORD(cur_i[r], cur_v[r]);
            break;
        case BANK_VSET:
            pad_ok[r] = cur_v[r] <= cur_i[r];
            pad_word[r] = (unsigned)cur_v[r];
            break;
        case BANK_ILIM:
            pad_ok[r] = 1;
            pad_word[r] = (unsigned)cur_i[r];
            break;
        case BANK_CFG:
            pad_ok[r] = 1;
            pad_word[r] = (unsigned)cur_e[r];
            break;
        }
    }
}

static int used(const int *need)
{
    int r;

    for (r = 0; r < rail_count; r++) {
        if (need[r]) {
            return 1;
        }
    }
    return 0;
}

void sled_open(int rails)
{
    int r;

    rail_count = rails;
    if (rail_count < 0) {
        rail_count = 0;
    }
    if (rail_count > MAXR) {
        rail_count = MAXR;
    }
    in_program = 0;
    unsettled = 0;
    for (r = 0; r < MAXR; r++) {
        cur_v[r] = 50;
        cur_i[r] = 90;
        cur_e[r] = 1;
    }
}

void sled_apply(const sled_request *reqs, int count)
{
    int n = rail_count;
    int r, k, pass;

    for (r = 0; r < n; r++) {
        say_v[r] = say_i[r] = say_e[r] = 0;
        first_down[r] = 0;
        for (pass = 0; pass < 4; pass++) {
            want[pass][r] = 0;
        }
    }

    /* The batch's last word on each register is the whole of what it asks
     * for, and anything already in force asks for nothing. */
    for (k = 0; k < count; k++) {
        const sled_request *q = &reqs[k];
        if (q->rail < 0 || q->rail >= n) {
            continue;
        }
        r = q->rail;
        switch (q->kind) {
        case SLED_VOLTAGE:
            say_v[r] = 1;
            tgt_v[r] = q->value;
            break;
        case SLED_LIMIT:
            say_i[r] = 1;
            tgt_i[r] = q->value;
            break;
        case SLED_ENABLE:
            say_e[r] = 1;
            tgt_e[r] = q->value & 1;
            break;
        }
    }
    for (r = 0; r < n; r++) {
        if (say_v[r] && tgt_v[r] == cur_v[r]) {
            say_v[r] = 0;
        }
        if (say_i[r] && tgt_i[r] == cur_i[r]) {
            say_i[r] = 0;
        }
        if (say_e[r] && tgt_e[r] == cur_e[r]) {
            say_e[r] = 0;
        }
    }

    for (r = 0; r < n; r++) {
        int fin_v, fin_i;

        if (!say_v[r] && !say_i[r]) {
            continue;
        }
        fin_v = say_v[r] ? tgt_v[r] : cur_v[r];
        fin_i = say_i[r] ? tgt_i[r] : cur_i[r];

        if (fin_v <= fin_i) {
            /* One word says all of it, whatever the rail is doing and
             * whichever way its halves are moving. */
            want[P_PAIR][r] = 1;
            value[P_PAIR][r] = SLED_PAIR_WORD(fin_i, fin_v);
            continue;
        }

        /* The batch leaves this rail under its own limit, which no pair word
         * can describe. The voltage goes first and the limit follows it down;
         * where the limit standing over it will not take the voltage, a pair
         * word puts the two level for the price of the voltage write alone. */
        if (fin_v != cur_v[r]) {
            if (cur_i[r] >= fin_v) {
                want[P_VSET][r] = 1;
                value[P_VSET][r] = (unsigned)fin_v;
            } else {
                want[P_PAIR][r] = 1;
                value[P_PAIR][r] = SLED_PAIR_WORD(fin_v, fin_v);
            }
        }
        want[P_ILIM][r] = 1;
        value[P_ILIM][r] = (unsigned)fin_i;

        /* Only a rail whose limit is about to go under its voltage has to be
         * down for it. Every other enable move can wait for the trims. */
        if (cur_e[r]) {
            first_down[r] = 1;
            first_down_val[r] = 0u;
        }
    }

    for (r = 0; r < n; r++) {
        if (say_e[r] && !first_down[r]) {
            want[P_CFG][r] = 1;
            value[P_CFG][r] = (unsigned)tgt_e[r];
        }
    }

    if (used(first_down)) {
        hold(0);
        pads_for(BANK_CFG);
        cover(BANK_CFG, SLED_CFG, first_down, first_down_val);
    }

    if (used(want[P_PAIR]) || used(want[P_VSET]) || used(want[P_ILIM])) {
        hold(1);
        if (used(want[P_PAIR])) {
            pads_for(BANK_PAIR);
            cover(BANK_PAIR, SLED_PAIR, want[P_PAIR], value[P_PAIR]);
        }
        if (used(want[P_VSET])) {
            pads_for(BANK_VSET);
            cover(BANK_VSET, SLED_VSET, want[P_VSET], value[P_VSET]);
        }
        if (used(want[P_ILIM])) {
            /* Last, because this is the pass that leaves a rail sitting under
             * its own voltage, and nothing restated may land after it. */
            pads_for(BANK_ILIM);
            cover(BANK_ILIM, SLED_ILIM, want[P_ILIM], value[P_ILIM]);
        }
    }

    if (used(want[P_CFG])) {
        hold(0);
        pads_for(BANK_CFG);
        cover(BANK_CFG, SLED_CFG, want[P_CFG], value[P_CFG]);
    }
}
