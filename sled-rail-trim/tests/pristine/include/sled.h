/*
 * The frozen surface between the apply path and the rest of the firmware.
 *
 * This header is fingerprinted before the conformance run. The bench harness
 * binds to these names, so it has to survive byte for byte.
 */
#ifndef SLED_H
#define SLED_H

/* Register map of the part. VSET, ILIM, CFG and PAIR are one register per
 * rail, indexed from the base address. */
#define SLED_MODE   0x00u   /* write 1 to hold the part in program mode */
#define SLED_STATUS 0x01u   /* read-only; 0 while settling, 1 once settled */
#define SLED_VSET   0x10u   /* rail voltage code */
#define SLED_ILIM   0x30u   /* rail current limit code */
#define SLED_CFG    0x50u   /* bit 0 is the rail enable */
#define SLED_PAIR   0x70u   /* both halves of a rail's trim in one word */

/* The pair register is sixteen bits: the limit in the high byte, the voltage
 * in the low one. Both halves land together. */
#define SLED_PAIR_WORD(ilim, vset)  ((((unsigned)(ilim) & 0xFFu) << 8) | \
                                     ((unsigned)(vset) & 0xFFu))

#define SLED_MAX_RAILS 32

typedef enum {
    SLED_VOLTAGE = 0,
    SLED_LIMIT   = 1,
    SLED_ENABLE  = 2
} sled_kind;

/* One line out of the batch the config layer hands down. */
typedef struct {
    sled_kind kind;
    int rail;
    int value;
} sled_request;

/* The frame the bus controller can stage in one go. */
#define SLED_BURST_MAX  8

/*
 * The bus.
 *
 * sled_bus_write and sled_bus_read are one transaction each. sled_bus_burst
 * stages up to SLED_BURST_MAX consecutive registers of one bank and costs two
 * transactions whatever its length; the part takes the words in order and
 * checks each one exactly as it would check a single write.
 *
 * All three return 0 when the part accepted everything and -1 when it refused.
 * sled_bus_read returns the register, or -1 if the part refused. A refusal is
 * a fault: the part latches it and the run is over.
 */
int sled_bus_write(unsigned addr, unsigned value);
int sled_bus_read(unsigned addr);
int sled_bus_burst(unsigned addr, const unsigned *values, int count);

/*
 * What the apply path has to provide.
 *
 * sled_open is called once, before any batch, with the number of rails this
 * part carries. sled_apply is called once per batch.
 */
void sled_open(int rails);
void sled_apply(const sled_request *reqs, int count);

#endif /* SLED_H */
