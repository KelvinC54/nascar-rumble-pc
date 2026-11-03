/* Print the unseeded XXH3-64 of each file (same hash DuckStation packs use).
 * Paths come from the arguments, or one per line on stdin when there are none.
 * build: clang -O2 -I <psxrecomp>/runtime/third_party xxh3sum.c -o xxh3sum.exe */
#define XXH_INLINE_ALL
#include "xxhash.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int hash_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return 1; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *buf = malloc(n ? n : 1);
    if (fread(buf, 1, n, f) != (size_t)n) { perror(path); fclose(f); free(buf); return 1; }
    fclose(f);
    printf("%016llX %s\n", (unsigned long long)XXH3_64bits(buf, n), path);
    free(buf);
    return 0;
}

int main(int argc, char **argv) {
    int rc = 0;
    if (argc > 1) {
        for (int i = 1; i < argc; i++) rc |= hash_file(argv[i]);
        return rc;
    }
    char line[4096];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = '\0';
        if (line[0]) rc |= hash_file(line);
    }
    return rc;
}
