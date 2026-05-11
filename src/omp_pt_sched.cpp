// omp_pt_sched.cpp - Path tracer OpenMP con schedule configurable.
//
// Uso:
//   ./omp_pt_sched <scene.txt> <output.ppm> [W H D N threads schedule chunk]
//
// schedule puede ser: runtime, static, dynamic, guided, auto.
// Si se usa runtime, el schedule se toma desde OMP_SCHEDULE.

#include "pt.hpp"

#include <omp.h>

#include <algorithm>
#include <cstdlib>

namespace {

std::string schedule_name(omp_sched_t kind) {
    switch (kind & ~omp_sched_monotonic) {
        case omp_sched_static:  return "static";
        case omp_sched_dynamic: return "dynamic";
        case omp_sched_guided:  return "guided";
        case omp_sched_auto:    return "auto";
        default:                return "unknown";
    }
}

bool parse_schedule(const std::string& name, omp_sched_t& kind) {
    if (name == "static")  { kind = omp_sched_static;  return true; }
    if (name == "dynamic") { kind = omp_sched_dynamic; return true; }
    if (name == "guided")  { kind = omp_sched_guided;  return true; }
    if (name == "auto")    { kind = omp_sched_auto;    return true; }
    return false;
}

}  // namespace

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Uso: " << argv[0]
                  << " <scene.txt> <output.ppm> [W H D N threads schedule chunk]\n";
        return 1;
    }

    const std::string scene_file  = argv[1];
    const std::string output_file = argv[2];
    const int W         = (argc > 3) ? std::stoi(argv[3]) : 800;
    const int H         = (argc > 4) ? std::stoi(argv[4]) : 600;
    const int MAX_DEPTH = (argc > 5) ? std::stoi(argv[5]) : 8;
    const int SAMPLES   = (argc > 6) ? std::stoi(argv[6]) : 64;
    const int THREADS   = (argc > 7) ? std::stoi(argv[7]) : 0;
    const std::string requested_schedule = (argc > 8) ? argv[8] : "runtime";
    const int CHUNK = (argc > 9) ? std::stoi(argv[9]) : 1;

    if (THREADS > 0) omp_set_num_threads(THREADS);

    if (requested_schedule != "runtime") {
        omp_sched_t kind;
        if (!parse_schedule(requested_schedule, kind)) {
            std::cerr << "Error: schedule desconocido '" << requested_schedule
                      << "'. Use runtime, static, dynamic, guided o auto.\n";
            return 1;
        }
        omp_set_schedule(kind, std::max(1, CHUNK));
    }

    omp_sched_t active_kind;
    int active_chunk = 0;
    omp_get_schedule(&active_kind, &active_chunk);

    Scene  sc  = load_scene(scene_file);
    Camera cam({0, 0.5, 3.8}, {0, 0, 0}, {0, 1, 0}, 55.0, W, H);

    std::vector<Vec3> pixels(W * H);
    const int total_pixels = W * H;

    double t0 = omp_get_wtime();

    #pragma omp parallel for schedule(runtime)
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

    const std::string active_schedule = schedule_name(active_kind);

    std::cerr << "Resolucion  : " << W << "x" << H << "\n"
              << "Prof. maxima: " << MAX_DEPTH << " rebotes\n"
              << "Muestras/px : " << SAMPLES << "\n"
              << "Rayos total : " << (long long)W*H*SAMPLES << "\n"
              << "Esferas     : " << sc.spheres.size() << "\n"
              << "Threads     : " << used_threads << "\n"
              << "Schedule    : " << active_schedule << "\n"
              << "Chunk       : " << active_chunk << "\n"
              << "Tiempo      : " << elapsed << " s\n"
              << "Imagen      : " << (output_file == "-" ? "(omitida)" : output_file) << "\n"
              << "RESULT,omp_pt_sched," << scene_file << "," << W << "," << H << ","
              << MAX_DEPTH << "," << SAMPLES << "," << used_threads << ","
              << active_schedule << "," << active_chunk << "," << elapsed << "\n";

    return 0;
}
