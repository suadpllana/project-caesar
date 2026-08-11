/*
 * The apply path.
 *
 * A batch arrives from the config layer as a list of settings, in the order
 * that layer produced them, and this walks it and puts each one on the wire.
 * Trim registers are only accepted while the part is held in program mode and
 * config registers are only accepted outside it, so the mode is moved whenever
 * the next setting needs the other one, and the part is polled until it says
 * it has settled behind the move.
 *
 * This is the version that shipped with the rack. Every batch it has ever been
 * handed lands, and the part has never faulted in the field.
 */
#include "sled.h"

static int rail_count;
static int in_program;

/* Moving the mode costs a write, and the part will refuse anything at all
 * until it answers a look at its status register with a 1. */
static void hold(int program)
{
    if (in_program == program) {
        return;
    }
    sled_bus_write(SLED_MODE, program ? 1u : 0u);
    while (sled_bus_read(SLED_STATUS) != 1) {
        /* still settling */
    }
    in_program = program;
}

void sled_open(int rails)
{
    rail_count = rails;
    in_program = 0;
}

void sled_apply(const sled_request *reqs, int count)
{
    int i;

    for (i = 0; i < count; i++) {
        const sled_request *r = &reqs[i];
        if (r->rail < 0 || r->rail >= rail_count) {
            continue;
        }
        switch (r->kind) {
        case SLED_VOLTAGE:
            hold(1);
            sled_bus_write(SLED_VSET + (unsigned)r->rail, (unsigned)r->value);
            break;
        case SLED_LIMIT:
            hold(1);
            sled_bus_write(SLED_ILIM + (unsigned)r->rail, (unsigned)r->value);
            break;
        case SLED_ENABLE:
            hold(0);
            sled_bus_write(SLED_CFG + (unsigned)r->rail, (unsigned)r->value);
            break;
        }
    }
}
