#include <stdint.h>

#include <algorithm>
#include <cstring>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "picosha2.h"

#ifdef _WIN32
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT
#endif

const int convertToFlatIndex(const int &rowIdx, const int &colIdx, const int &gridCols)
{
    return gridCols * rowIdx + colIdx;
}

const int countCellNeighbours(const std::vector<uint8_t> &grid, const int &rowIdx,
                              const int &colIdx, const int &gridRows, const int &gridCols)
{
    int neigbourCount = 0;
    std::vector<int> idxDelta = {-1, 0, 1};

    for (int rowDelta : idxDelta)
    {
        for (int colDelta : idxDelta)
        {
            if (rowDelta == 0 && colDelta == 0) continue;
            int neigbourRowIdx = rowIdx + rowDelta;
            int neigbourColIdx = colIdx + colDelta;

            if (neigbourRowIdx >= 0 && neigbourRowIdx < gridRows && neigbourColIdx >= 0 &&
                neigbourColIdx < gridCols)
            {
                int flatIdx = convertToFlatIndex(neigbourRowIdx, neigbourColIdx, gridCols);
                neigbourCount += grid[flatIdx];
            }
        }
    }

    return neigbourCount;
}

const std::string computeGridHash(const std::vector<uint8_t> &grid)
{
    return picosha2::hash256_hex_string(grid);
}

struct StepResult
{
    int populated;
    bool gridsEqual;
};

StepResult runStep(std::vector<uint8_t> &grid, const int &gridRows, const int &gridCols)
{
    int gridSize = gridRows * gridCols;
    std::vector<uint8_t> newGrid(gridSize, 0);
    int populated = 0;

    for (int rowIdx = 0; rowIdx < gridRows; rowIdx++)
    {
        for (int colIdx = 0; colIdx < gridCols; colIdx++)
        {
            int flatIdx = convertToFlatIndex(rowIdx, colIdx, gridCols);
            uint8_t cellValue = grid[flatIdx];
            int numNeighbours = countCellNeighbours(grid, rowIdx, colIdx, gridRows, gridCols);

            if (cellValue == 1 && (numNeighbours == 2 || numNeighbours == 3))
            {
                newGrid[flatIdx] = 1;
            }
            else if (cellValue == 0 && numNeighbours == 3)
            {
                newGrid[flatIdx] = 1;
                populated += 1;
            }
        }
    }

    bool gridsEqual = (grid == newGrid);
    grid = newGrid;
    return {populated, gridsEqual};
}

extern "C" DLL_EXPORT int runFromWord(uint8_t *pInputGrid, int gridRows, int gridCols,
                                      int maxGenerations, int repeatPatternThreshold,
                                      int *pOutGenerations, int *pOutScore, char *pReason,
                                      int reasonBuffSize)
{
    int gridSize = gridRows * gridCols;
    std::vector<uint8_t> grid(pInputGrid, pInputGrid + gridSize);
    std::unordered_map<std::string, int> seenHashmap;

    int totalScore = 0;
    seenHashmap[computeGridHash(grid)] = 0;

    for (int genNum = 1; genNum <= maxGenerations; genNum++)
    {
        StepResult stepResult = runStep(grid, gridRows, gridCols);

        totalScore += stepResult.populated;
        std::string gridHash = computeGridHash(grid);

        bool isExtinct = std::all_of(grid.begin(), grid.end(), [](uint8_t i) { return i == 0; });

        if (isExtinct)
        {
            *pOutGenerations = genNum;
            *pOutScore = totalScore;
            strncpy(pReason, "extinction", reasonBuffSize);
            return 0;
        }

        if (stepResult.gridsEqual)
        {
            *pOutGenerations = genNum;
            *pOutScore = totalScore;
            strncpy(pReason, "persistent_state", reasonBuffSize);
            return 0;
        }

        if (seenHashmap.count(gridHash) == 0)
        {
            seenHashmap[gridHash] = genNum;
            continue;
        }

        int genPeriod = genNum - seenHashmap[gridHash];
        if (genPeriod < repeatPatternThreshold)
        {
            *pOutGenerations = genNum;
            *pOutScore = totalScore;
            strncpy(pReason, "repeated_pattern", reasonBuffSize);
            return 0;
        }

        seenHashmap[gridHash] = genNum;
    }

    return 0;
}
