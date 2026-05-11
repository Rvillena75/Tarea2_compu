#include <iostream>
#include <vector>
#include <limits>
#include <cstdlib>
#include <omp.h>

static const long N    = 20000;  // matriz triangular N x N
static const int  REPS = 3;

int main() {
    int n_threads = omp_get_max_threads();
    const char* sched = std::getenv("OMP_SCHEDULE");
    if (!sched) sched = "static";

    // Almacenamiento compacto: fila i empieza en i*(i+1)/2
    long total = N * (N + 1) / 2;
    std::vector<double> data(total);
    std::vector<double> result(N);

    // Inicializar: data[i][j] = j + 1
    for (long i = 0; i < N; i++) {
        long offset = i * (i + 1) / 2;
        for (long j = 0; j <= i; j++)
            data[offset + j] = static_cast<double>(j + 1);
    }

    // Benchmark: suma de cada fila con schedule(runtime)
    double best = std::numeric_limits<double>::max();
    for (int r = 0; r < REPS; r++) {
        double t0 = omp_get_wtime();

        #pragma omp parallel for schedule(runtime)
        for (long i = 0; i < N; i++) {
            long offset = i * (i + 1) / 2;
            double sum = 0.0;
            for (long j = 0; j <= i; j++)
                sum += data[offset + j];
            result[i] = sum;
        }

        double elapsed = omp_get_wtime() - t0;
        if (elapsed < best) best = elapsed;
    }

    // Prevenir eliminación por el compilador
    double checksum = 0.0;
    for (int i = 0; i < 10; i++) checksum += result[i];
    if (checksum < 0) std::cerr << checksum;

    std::cout << n_threads << "," << sched << "," << best * 1000.0 << "\n";
    return 0;
}
