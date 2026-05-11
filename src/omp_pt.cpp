// omp_pt.cpp - Path tracer paralelo con OpenMP.
//
// Uso: ./omp_pt <scene.txt> <output.ppm> [W H D N threads]
//   N: caminos por pixel. Default: 64.
//   threads: numero de hilos OpenMP. Si se omite, usa OMP_NUM_THREADS/runtime.

#include "pt.hpp"

#include <omp.h>

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Uso: " << argv[0] << " <scene.txt> <output.ppm> [W H D N threads]\n";
        return 1;
    }

    const std::string scene_file  = argv[1];
    const std::string output_file = argv[2];
    const int W         = (argc > 3) ? std::stoi(argv[3]) : 800;
    const int H         = (argc > 4) ? std::stoi(argv[4]) : 600;
    const int MAX_DEPTH = (argc > 5) ? std::stoi(argv[5]) : 8;
    const int SAMPLES   = (argc > 6) ? std::stoi(argv[6]) : 64;
    const int THREADS   = (argc > 7) ? std::stoi(argv[7]) : 0;

    if (THREADS > 0) omp_set_num_threads(THREADS);

    Scene  sc  = load_scene(scene_file);
    Camera cam({0, 0.5, 3.8}, {0, 0, 0}, {0, 1, 0}, 55.0, W, H);

    std::vector<Vec3> pixels(W * H);
    const int total_pixels = W * H;

    double t0 = omp_get_wtime();

    // Cada pixel es independiente. Aplanar (j,i) a idx hace que el chunksize
    // represente pixeles, no filas completas, y mejora el balance si hay carga irregular.
    #pragma omp parallel for schedule(static)
    for (int idx = 0; idx < total_pixels; ++idx) {
        const int j = idx / W;
        const int i = idx - j * W;
        RNG rng(static_cast<uint64_t>(idx) + 1);
        Vec3 color(0, 0, 0);

        for (int s = 0; s < SAMPLES; ++s) {
            double u = (i + rng.uniform()) / W;
            double v = (j + rng.uniform()) / H;
            color += trace_path(cam.get_ray(u, v), sc, MAX_DEPTH, rng);
        }
        pixels[idx] = color / static_cast<double>(SAMPLES);
    }

    double elapsed = omp_get_wtime() - t0;

    if (output_file != "-") save_ppm(output_file, pixels, W, H);

    int used_threads = 1;
    #pragma omp parallel
    {
        #pragma omp single
        used_threads = omp_get_num_threads();
    }

    std::cerr << "Resolucion  : " << W << "x" << H << "\n"
              << "Prof. maxima: " << MAX_DEPTH << " rebotes\n"
              << "Muestras/px : " << SAMPLES << "\n"
              << "Rayos total : " << (long long)W*H*SAMPLES << "\n"
              << "Esferas     : " << sc.spheres.size() << "\n"
              << "Threads     : " << used_threads << "\n"
              << "Schedule    : static\n"
              << "Tiempo      : " << elapsed << " s\n"
              << "Imagen      : " << (output_file == "-" ? "(omitida)" : output_file) << "\n"
              << "RESULT,omp_pt," << scene_file << "," << W << "," << H << ","
              << MAX_DEPTH << "," << SAMPLES << "," << used_threads
              << ",static,0," << elapsed << "\n";

    return 0;
}
