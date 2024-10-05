#include <iostream>
#include <Eigen/Dense>
#include "simulator.h"

using namespace std;
using namespace Eigen;
using namespace std::chrono;

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <config_file_path> <simulation_duration> <output_file_path> <stats_file_path>" << std::endl;
        return 1;
    }

    const char* config_file_path = argv[1];
    int T = std::stoi(argv[2]); // Simulation duration
    const char* output_file_path = argv[3];
    const char* stats_file_path = argv[4];

    std::cout << "Solving multi-robot motion planning problem..." << std::endl;

    std::ifstream my_config_file(config_file_path);
    assert(my_config_file && "Couldn't find the config file");
    std::ofstream stats_file(stats_file_path);
    assert(stats_file && "Couldn't open the stats file");

    Simulator sim(my_config_file, stats_file);

    sim.run(T);

    // Save data to file
    sim.saveDataToFile(output_file_path);

    return 0;
}


