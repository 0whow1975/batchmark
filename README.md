# batchmark

> CLI tool to benchmark shell commands across multiple input sizes and output structured reports

## Installation

```bash
pip install batchmark
```

## Usage

Run a benchmark by specifying a command and a set of input sizes:

```bash
batchmark run "sort input_{size}.txt" --sizes 100,1000,10000 --output report.json
```

batchmark will execute the command for each input size, measure execution time and resource usage, and compile the results into a structured report.

### Example Output

```
Size       Avg Time    Min Time    Max Time
---------  ----------  ----------  ----------
100        0.012s      0.010s      0.015s
1000       0.094s      0.089s      0.102s
10000      1.021s      0.998s      1.047s
```

Export results in different formats:

```bash
batchmark run "grep foo input_{size}.txt" --sizes 500,5000 --format csv --output results.csv
```

### Options

| Flag | Description |
|------|-------------|
| `--sizes` | Comma-separated list of input sizes |
| `--runs` | Number of runs per size (default: 5) |
| `--format` | Output format: `json`, `csv`, or `table` (default: `table`) |
| `--output` | Path to save the report |

## Installation from Source

```bash
git clone https://github.com/yourname/batchmark.git
cd batchmark
pip install -e .
```

## License

This project is licensed under the [MIT License](LICENSE).