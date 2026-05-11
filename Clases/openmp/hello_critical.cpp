#include <iostream>
#include <omp.h>

int main() {
    int nthreads, tid;

    #pragma omp parallel private(tid)
    {
        tid = omp_get_thread_num();

        #pragma omp critical
        std::cout << "Hello world! I am thread " << tid << "\n";

        #pragma omp barrier
        if (tid == 0) {
            nthreads = omp_get_num_threads();
            std::cout << "Number of threads = " << nthreads << "\n";
        }
    }
    return 0;
}
