#include <iostream>
#include <vector>
#include <limits>
#include <omp.h>

static const long N      = 100'000'000;  // 100M elements
static const int  REPS   = 5;            // repetitions per measurement

int main() {
    int n_threads = omp_get_max_threads();

    // Allocate arrays
    std::vector<double> a(N), b(N), c(N);

    #pragma omp parallel for
    for (long i = 0; i < N; i++) {
        a[i] = static_cast<double>(i) * 0.5;
        b[i] = static_cast<double>(i) * 1.5;
    }

    // Benchmark: take minimum time over REPS runs
    double best = std::numeric_limits<double>::max();
    for (int r = 0; r < REPS; r++) {
        double t0 = omp_get_wtime();

        #pragma omp parallel for
        for (long i = 0; i < N; i++)
            c[i] = a[i] + b[i];

        double elapsed = omp_get_wtime() - t0;
        if (elapsed < best) best = elapsed;
    }

    double checksum = 0.0;
    for (long i = 0; i < 10; i++) checksum += c[i];
    if (checksum < 0) std::cerr << checksum;  // never printed

    std::cout << n_threads << "," << best * 1000.0 << "\n";
    return 0;
}
