# CLI Tool Documentation

## Prerequisites

- Node.js 18 or higher
- npm or yarn

## Installation

Download the binary from releases page.

Or install via npm:
```bash
npm install -g tool
```

## Usage

Run the command:
```bash
tool --help
```

Example output:
```
Usage: tool [options]

Options:
  --verbose    Enable verbose output
  --quiet      Suppress output
  --config     Specify config file
```

## Options

The following options are available:

- `--verbose` - Enable verbose output
- `--quiet` - Suppress output
- `--config` - Specify config file

## Examples

Basic usage:
```bash
tool --verbose input.txt
```

With config:
```bash
tool --config myconfig.json
```
