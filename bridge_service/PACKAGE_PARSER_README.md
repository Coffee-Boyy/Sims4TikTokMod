# Custom Sims 4 Package Parser

This directory contains a comprehensive custom implementation for parsing Sims 4 package files that handles compressed and binary formats that the `@s4tk/models` library cannot process.

## Overview

The Sims 4 uses the Database Packed File (DBPF) v2.0 format for its package files. These files can contain compressed resources using the RefPack algorithm, which the original `@s4tk/models` library struggles with. Our custom parser provides:

- **Full DBPF v2.0 support** - Handles headers, index tables, and resource extraction
- **RefPack decompression** - Proper decompression of compressed resources
- **Binary resource handling** - Can extract and process binary resource data
- **Fallback integration** - Seamlessly falls back from `@s4tk/models` when it fails
- **Enhanced features** - Better CAS part detection, string table parsing, and validation

## Files

### Core Parser Files

- **`dbpf-parser.js`** - Core DBPF package parser with RefPack decompression
- **`ts4-package-parser-custom.js`** - High-level API matching the original parser interface
- **`ts4-package-parser.js`** - Updated original parser with fallback integration

### Testing and CLI Tools

- **`test-custom-parser.js`** - Comprehensive CLI tool for testing and exploring packages
- **`test-package-cli.js`** - Original CLI tool (still functional)

## Usage

### Basic Usage

```javascript
import { readPackageFile, listResources, getPackageInfo } from './ts4-package-parser-custom.js';

// Read a package file
const pkg = readPackageFile('path/to/package.package');

// Get package information
const info = getPackageInfo(pkg);
console.log(`Package has ${info.totalResources} resources`);

// List all resources
const resources = listResources(pkg);
console.log('Resources:', resources);
```

### Using the Fallback Parser

The updated `ts4-package-parser.js` automatically falls back to the custom parser when `@s4tk/models` fails:

```javascript
import { readPackageFile, listCasParts } from './ts4-package-parser.js';

// This will try @s4tk/models first, then fall back to custom parser
const pkg = readPackageFile('compressed-package.package');
const casParts = listCasParts(pkg);
```

### CLI Usage

The new CLI tool provides comprehensive package analysis:

```bash
# Show package information
npm run pkg:info path/to/package.package

# Validate package integrity
npm run pkg:validate path/to/package.package

# List resources
node test-custom-parser.js package.package --resources

# Find CAS parts and hair names
node test-custom-parser.js package.package --hair --names

# Search for specific resource types
node test-custom-parser.js package.package --search --type 0x220557DA

# Search by name pattern
node test-custom-parser.js package.package --search --name "hair"

# Get detailed verbose output
node test-custom-parser.js package.package --info --verbose
```

## Features

### DBPF Format Support

- **Header parsing** - Extracts package metadata, version, creation dates
- **Index table parsing** - Reads resource entries with type, group, instance IDs
- **Resource extraction** - Extracts raw resource data with proper offset handling
- **Dual index support** - Handles packages with primary and secondary indices

### RefPack Decompression

- **Full RefPack implementation** - Handles the bitstream format used by Sims 4
- **Error recovery** - Gracefully handles partially corrupted compressed data
- **Performance optimized** - Efficient decompression with minimal memory overhead

### Resource Type Support

The parser recognizes and handles these resource types:

- **STBL (0x220557DA)** - String Tables with locale support
- **CASP (0x034AEECB)** - CAS Parts (clothing, hair, etc.)
- **GEOM (0x015A1849)** - Geometry data
- **DDS (0x00B2D882)** - DirectDraw Surface textures
- **PNG (0x2E75C764)** - PNG images
- **OBJD (0xC0DB5AE7)** - Object definitions
- And many more...

### Enhanced CAS Part Detection

- **Hair style detection** - Advanced heuristics to find hair-related items
- **Name matching** - Correlates CAS parts with string table entries
- **Metadata extraction** - Provides size, compression status, and type information

### String Table Processing

- **Multi-locale support** - Handles all Sims 4 language locales
- **Efficient indexing** - Fast lookup and filtering of string values
- **Pattern searching** - Find strings by content or key patterns

### Validation and Diagnostics

- **Package integrity checks** - Validates headers, indices, and resource references
- **Decompression testing** - Tests resource extraction to identify issues
- **Detailed error reporting** - Provides specific information about parsing problems

## Technical Details

### DBPF Structure

```
DBPF Package File:
├── Header (96 bytes)
│   ├── Signature (DBPF)
│   ├── Version (2.0 for Sims 4)
│   ├── Index offset and size
│   └── Creation/modification dates
├── Resource Data Blocks
│   ├── Compressed resources (RefPack)
│   └── Uncompressed resources
└── Index Table
    └── Resource entries (32 bytes each)
        ├── Type ID (4 bytes)
        ├── Group ID (4 bytes)
        ├── Instance ID (8 bytes)
        ├── Data offset (4 bytes)
        ├── Uncompressed size (4 bytes)
        ├── Compressed size (4 bytes)
        └── Compression flags (4 bytes)
```

### RefPack Compression

RefPack uses a control-byte system where each bit indicates whether the following data is:
- **Literal byte** (bit = 1) - Copy directly to output
- **Reference** (bit = 0) - Copy from previous output data

The format includes:
- 1-byte flags
- 1-byte magic number (0xFB)
- 3-byte uncompressed size
- Compressed bitstream data

### Error Handling

The parser includes comprehensive error handling:
- **Graceful degradation** - Continues parsing when individual resources fail
- **Fallback mechanisms** - Uses alternative parsing strategies for edge cases
- **Detailed logging** - Provides warnings and error context for debugging

## Performance

The custom parser is optimized for:
- **Memory efficiency** - Streams data without loading entire package into memory
- **Speed** - Fast index parsing and resource lookup
- **Scalability** - Handles large packages (100MB+) efficiently

## Compatibility

- **Node.js 14+** - Uses modern JavaScript features
- **ES Modules** - Uses import/export syntax
- **Cross-platform** - Works on Windows, macOS, and Linux
- **Sims 4 versions** - Supports all Sims 4 package formats

## Troubleshooting

### Common Issues

1. **"Invalid DBPF signature"** - File is not a valid package or is corrupted
2. **"RefPack decompression failed"** - Compressed resource is corrupted
3. **"No valid index found"** - Package index is missing or corrupted

### Debug Mode

Use the `--verbose` flag with the CLI tool to get detailed parsing information:

```bash
node test-custom-parser.js package.package --info --verbose
```

### Validation

Always validate packages when troubleshooting:

```bash
node test-custom-parser.js package.package --validate
```

## Contributing

When extending the parser:

1. **Add tests** - Use the CLI tool to test with various package files
2. **Handle errors gracefully** - Don't crash on malformed data
3. **Document new features** - Update this README
4. **Maintain compatibility** - Keep the API consistent with the original parser

## License

This parser is part of the Sims 4 TikTok Mod project and follows the same license terms.
