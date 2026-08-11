# Fingerprinted. The conformance run builds the apply path its own way; this is
# here so the sandbox can be built and watched.
CC      ?= cc
CFLAGS  ?= -std=c11 -O2 -Wall -Wextra -Iinclude

sandbox: src/sandbox.c src/driver.c include/sled.h
	$(CC) $(CFLAGS) -o sandbox src/sandbox.c src/driver.c

clean:
	rm -f sandbox

.PHONY: clean
