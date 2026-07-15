package main

import "log"

// logErr emits a warning-level line. Kept as a small wrapper so logging
// policy (timestamps, prefixes) can evolve in one place.
func logErr(format string, args ...any) {
	log.Printf("warn: "+format, args...)
}
