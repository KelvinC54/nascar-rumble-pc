/* Poor man's sampling profiler: suspend each thread of <pid> every ~1 ms, record RIP.
 * usage: sampler <pid> <seconds> > samples.txt
 * Output: first line "base <hex>" (main module load address), then "<tid> <rip hex>" per sample. */
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: sampler <pid> <seconds>\n"); return 2; }
    DWORD pid = (DWORD)atoi(argv[1]);
    DWORD ms = (DWORD)(atof(argv[2]) * 1000);
    HANDLE proc = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!proc) { fprintf(stderr, "OpenProcess failed %lu\n", GetLastError()); return 1; }
    HMODULE mod; DWORD need;
    if (EnumProcessModules(proc, &mod, sizeof(mod), &need)) printf("base %llx\n", (unsigned long long)mod);
    timeBeginPeriod(1);
    DWORD start = GetTickCount();
    while (GetTickCount() - start < ms) {
        HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        THREADENTRY32 te = { sizeof(te) };
        for (BOOL ok = Thread32First(snap, &te); ok; ok = Thread32Next(snap, &te)) {
            if (te.th32OwnerProcessID != pid) continue;
            HANDLE th = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, te.th32ThreadID);
            if (!th) continue;
            if (SuspendThread(th) != (DWORD)-1) {
                CONTEXT ctx; ctx.ContextFlags = CONTEXT_CONTROL;
                if (GetThreadContext(th, &ctx)) printf("%lu %llx\n", te.th32ThreadID, (unsigned long long)ctx.Rip);
                ResumeThread(th);
            }
            CloseHandle(th);
        }
        CloseHandle(snap);
        Sleep(1);
    }
    return 0;
}
