import fs from 'fs';
import zlib from 'zlib';

/**
 * DBPF Package Parser for Sims 4
 * Based on the C# implementation from S4Studio
 */

// Compression types from C# DBPFCompressionType enum
export const CompressionType = {
    Uncompressed: 0x0000,
    Streamable: 0x5A42,
    InternalCompression: 0x5A43,
    DeletedRecord: 0xFFE0,
    Zlib: 0x5A44
};

// Index flags from C# IndexFlags enum  
export const IndexFlags = {
    None: 0x00000000,
    ConstantType: 0x00000001,
    ConstantGroup: 0x00000002,
    ConstantInstanceEx: 0x00000004
};

// Common Sims 4 resource types
export const ResourceTypes = {
    StringTable: 0x220557DA, // Keep for compatibility but won't be used
    CasPart: 0x034AEECB,
    SimData: 0x545AC67A,
    Tuning: 0x62E94D38,
    DDS: 0x00B2D882,
    DST: 0x00B552EA,
    NameMap: 0x0166038C, // NameMapResource type - maps instance IDs to names (23462796u in C#)
    // Add more as needed
};

// String table locales mapping
export const StringTableLocales = {
    English: 0x00000000,
    ChineseSimplified: 0x00000001,
    ChineseTraditional: 0x00000002,
    Czech: 0x00000003,
    Danish: 0x00000004,
    Dutch: 0x00000005,
    Finnish: 0x00000006,
    French: 0x00000007,
    German: 0x00000008,
    Italian: 0x00000009,
    Japanese: 0x0000000A,
    Korean: 0x0000000B,
    Norwegian: 0x0000000C,
    Polish: 0x0000000D,
    Portuguese: 0x0000000E,
    Russian: 0x0000000F,
    Spanish: 0x00000010,
    Swedish: 0x00000011
};

// Utility functions
export function hexU32(num) {
    return '0x' + Number(num >>> 0).toString(16).toUpperCase().padStart(8, '0');
}

export function hexU64(big) {
    try {
        const b = typeof big === 'bigint' ? big : BigInt(big);
        return '0x' + b.toString(16).toUpperCase().padStart(16, '0');
    } catch {
        return '0x' + String(big);
    }
}

/**
 * DBPF Header structure
 */
class DBPFHeader {
    constructor() {
        this.signature = '';
        this.majorVersion = 0;
        this.minorVersion = 0;
        this.unknown1 = 0;
        this.unknown2 = 0;
        this.unknown3 = 0;
        this.createdDate = 0;
        this.modifiedDate = 0;
        this.indexMajorVersion = 0;
        this.indexRecordEntryCount = 0;
        this.indexRecordPosition = 0;
        this.indexRecordSize = 0;
        this.trashRecordEntryCount = 0;
        this.trashRecordPosition = 0;
        this.trashRecordSize = 0;
        this.indexMinorVersion = 0;
        this.unknown4 = new Array(32).fill(0);
    }

    read(buffer, offset = 0) {
        const view = new DataView(buffer.buffer || buffer, offset);
        let pos = 0;

        // Read signature (4 bytes)
        this.signature = String.fromCharCode(
            view.getUint8(pos), view.getUint8(pos + 1),
            view.getUint8(pos + 2), view.getUint8(pos + 3)
        );
        pos += 4;

        if (this.signature !== 'DBPF') {
            throw new Error(`Not a DBPF package file. Expected 'DBPF', got '${this.signature}'`);
        }

        // Read version info
        this.majorVersion = view.getUint32(pos, true); pos += 4;
        this.minorVersion = view.getUint32(pos, true); pos += 4;
        this.unknown1 = view.getUint32(pos, true); pos += 4;
        this.unknown2 = view.getUint32(pos, true); pos += 4;
        this.unknown3 = view.getUint32(pos, true); pos += 4;

        // Read dates
        this.createdDate = view.getUint32(pos, true); pos += 4;
        this.modifiedDate = view.getUint32(pos, true); pos += 4;

        // Read index info
        this.indexMajorVersion = view.getUint32(pos, true); pos += 4;
        this.indexRecordEntryCount = view.getUint32(pos, true); pos += 4;
        this.indexRecordPosition = view.getUint32(pos, true); pos += 4;
        this.indexRecordSize = view.getUint32(pos, true); pos += 4;

        // Read trash info
        this.trashRecordEntryCount = view.getUint32(pos, true); pos += 4;
        this.trashRecordPosition = view.getUint32(pos, true); pos += 4;
        this.trashRecordSize = view.getUint32(pos, true); pos += 4;

        // Read minor version
        this.indexMinorVersion = view.getUint32(pos, true); pos += 4;

        // Read unknown bytes (32 bytes)
        for (let i = 0; i < 32; i++) {
            this.unknown4[i] = view.getUint8(pos + i);
        }
        pos += 32;

        return pos;
    }

    get version() {
        return `${this.majorVersion}.${this.minorVersion}`;
    }
}

/**
 * DBPF Resource Entry
 */
class DBPFResourceEntry {
    constructor() {
        this.type = 0;
        this.group = 0;
        this.instance = 0n;
        this.offset = 0;
        this.size = 0;
        this.sizeDecompressed = 0;
        this.compressionType = CompressionType.Uncompressed;
        this.committed = 0;
    }

    get isCompressed() {
        return this.compressionType !== CompressionType.Uncompressed && 
               this.compressionType !== CompressionType.DeletedRecord;
    }

    get isDeleted() {
        return this.compressionType === CompressionType.DeletedRecord;
    }

    equals(other) {
        return this.type === other.type &&
               this.group === other.group &&
               this.instance === other.instance;
    }

    toString() {
        return `${hexU32(this.type)}:${hexU32(this.group)}:${hexU64(this.instance)}`;
    }
}

/**
 * Main DBPF Package class
 */
export class DBPFPackage {
    constructor(buffer) {
        this.buffer = buffer;
        this.header = new DBPFHeader();
        this.entries = [];
        this.resourceCache = new Map();
        
        if (buffer) {
            this._parseHeader();
            this._parseIndexTable();
        }
    }

    static fromFile(filePath) {
        const buffer = fs.readFileSync(filePath);
        return new DBPFPackage(buffer);
    }

    _parseHeader() {
        try {
            this.header.read(this.buffer, 0);
        } catch (error) {
            throw new Error(`Failed to parse DBPF header: ${error.message}`);
        }
    }

    _parseIndexTable() {
        const view = new DataView(this.buffer.buffer || this.buffer);
        let pos = this.header.indexRecordPosition;

        // Read index flags
        const indexFlags = view.getUint32(pos, true);
        pos += 4;

        // Static key for constant fields
        const staticKey = {
            type: 0,
            group: 0,
            instance: 0n
        };

        // Read constant values based on flags
        if (indexFlags & IndexFlags.ConstantType) {
            staticKey.type = view.getUint32(pos, true);
            pos += 4;
        }

        if (indexFlags & IndexFlags.ConstantGroup) {
            staticKey.group = view.getUint32(pos, true);
            pos += 4;
        }

        if (indexFlags & IndexFlags.ConstantInstanceEx) {
            staticKey.instance |= BigInt(view.getUint32(pos, true)) << 32n;
            pos += 4;
        }

        // Parse entries
        const hasConstantType = !!(indexFlags & IndexFlags.ConstantType);
        const hasConstantGroup = !!(indexFlags & IndexFlags.ConstantGroup);
        const hasConstantInstanceEx = !!(indexFlags & IndexFlags.ConstantInstanceEx);

        for (let i = 0; i < this.header.indexRecordEntryCount; i++) {
            const entry = new DBPFResourceEntry();

            // Read type (or use constant)
            entry.type = hasConstantType ? staticKey.type : view.getUint32(pos, true);
            if (!hasConstantType) pos += 4;

            // Read group (or use constant)
            entry.group = hasConstantGroup ? staticKey.group : view.getUint32(pos, true);
            if (!hasConstantGroup) pos += 4;

            // Read instance (64-bit)
            const instanceHigh = hasConstantInstanceEx ? 
                Number(staticKey.instance >> 32n) : view.getUint32(pos, true);
            if (!hasConstantInstanceEx) pos += 4;

            const instanceLow = view.getUint32(pos, true);
            pos += 4;

            entry.instance = (BigInt(instanceHigh) << 32n) + BigInt(instanceLow);

            // Read offset and size
            entry.offset = view.getUint32(pos, true);
            pos += 4;

            const sizeField = view.getUint32(pos, true);
            pos += 4;
            
            entry.size = sizeField & 0x7FFFFFFF;
            entry.sizeDecompressed = view.getUint32(pos, true);
            pos += 4;

            // Read compression info if present
            if (sizeField & 0x80000000) {
                entry.compressionType = view.getUint16(pos, true);
                pos += 2;
                entry.committed = view.getUint16(pos, true);
                pos += 2;
            }

            // Skip deleted records
            if (entry.compressionType !== CompressionType.DeletedRecord) {
                this.entries.push(entry);
            }
        }
    }

    /**
     * Decompress resource data based on compression type
     */
    _decompressData(data, expectedSize, compressionType) {
        switch (compressionType) {
            case CompressionType.Uncompressed:
                return data;

            case CompressionType.Zlib:
                // Check for internal compression marker (from C# line 423-426)
                if (data[0] !== 0x78 && data[1] === 0xFB) {
                    // This is actually internal compression, not zlib
                    return this._decompressInternal(data, expectedSize);
                }
                try {
                    return zlib.inflateSync(data);
                } catch (error) {
                    throw new Error(`Zlib decompression failed: ${error.message}`);
                }

            case CompressionType.InternalCompression:
                return this._decompressInternal(data, expectedSize);

            case CompressionType.Streamable:
                // For now, treat as uncompressed
                console.warn('Streamable compression not fully implemented');
                return data;

            default:
                throw new Error(`Unsupported compression type: ${compressionType}`);
        }
    }

    /**
     * Decompress internal compression format
     * This is a simplified implementation - the actual algorithm is more complex
     */
    _decompressInternal(data, expectedSize) {
        // This is a placeholder for internal compression
        // The actual EA compression algorithm would need to be implemented here
        console.warn('Internal compression decompression is not fully implemented');
        return data;
    }

    /**
     * Get raw resource data for an entry
     */
    getResourceData(entry) {
        const cacheKey = entry.toString();
        
        if (this.resourceCache.has(cacheKey)) {
            return this.resourceCache.get(cacheKey);
        }

        // Read raw data from buffer
        const rawData = new Uint8Array(this.buffer, entry.offset, entry.size);
        
        // Decompress if needed
        let data;
        if (entry.isCompressed) {
            data = this._decompressData(rawData, entry.sizeDecompressed, entry.compressionType);
            
            // Validate decompressed size
            if (data.length !== entry.sizeDecompressed) {
                throw new Error(
                    `Decompression size mismatch for ${entry.toString()}: ` +
                    `expected ${entry.sizeDecompressed}, got ${data.length}`
                );
            }
        } else {
            data = rawData;
        }

        // Cache the result
        this.resourceCache.set(cacheKey, data);
        return data;
    }

    /**
     * Find a specific resource by type, group, and instance
     */
    findResource(type, group, instance) {
        const targetInstance = typeof instance === 'bigint' ? instance : BigInt(instance);
        
        return this.entries.find(entry => 
            entry.type === type &&
            entry.group === group &&
            entry.instance === targetInstance
        );
    }

    /**
     * Find all resources of a specific type
     */
    findResourcesByType(type) {
        return this.entries.filter(entry => entry.type === type);
    }

    /**
     * Get name mappings from NameMapResource entries in the package
     */
    getNameMappings() {
        const nameMappings = new Map();
        const nameMapEntries = this.findResourcesByType(ResourceTypes.NameMap);

        for (const entry of nameMapEntries) {
            try {
                const data = this.getResourceData(entry);
                const nameMap = this._parseNameMapResource(data);
                
                // Merge all name mappings into a single map
                for (const [instance, name] of nameMap.entries()) {
                    nameMappings.set(instance, name);
                }
            } catch (error) {
                console.warn(`Failed to parse name map ${entry.toString()}: ${error.message}`);
            }
        }

        return nameMappings;
    }

    /**
     * Parse NameMapResource data based on C# implementation
     */
    _parseNameMapResource(data) {
        const nameMap = new Map();
        const view = new DataView(data.buffer || data);
        
        if (data.length < 8) return nameMap;
        
        try {
            let pos = 0;
            
            // Read version (uint32)
            const version = view.getUint32(pos, true);
            pos += 4;
            
            if (version !== 1) {
                console.warn(`Unexpected NameMapResource version: ${version}, expected 1`);
            }
            
            // Read entry count (int32)
            const entryCount = view.getInt32(pos, true);
            pos += 4;
            
            // Read entries
            for (let i = 0; i < entryCount && pos < data.length; i++) {
                // Read instance (uint64)
                const instanceLow = view.getUint32(pos, true);
                pos += 4;
                const instanceHigh = view.getUint32(pos, true);
                pos += 4;
                const instance = (BigInt(instanceHigh) << 32n) + BigInt(instanceLow);
                
                // Read name (Pascal32 string - length prefix + string)
                if (pos + 4 > data.length) break;
                
                const nameLength = view.getUint32(pos, true);
                pos += 4;
                
                if (pos + nameLength > data.length) break;
                
                // Read string bytes
                const nameBytes = new Uint8Array(data, pos, nameLength);
                const name = new TextDecoder('utf-8').decode(nameBytes);
                pos += nameLength;
                
                // Store the mapping
                nameMap.set(instance, name.replace(/\0/g, ''));
            }
        } catch (error) {
            console.warn(`Error parsing NameMapResource: ${error.message}`);
        }
        
        return nameMap;
    }

    /**
     * Get CAS parts from the package
     */
    getCASParts() {
        return this.findResourcesByType(ResourceTypes.CasPart);
    }

    /**
     * Get locale name from group ID
     */
    _getLocaleNameFromGroup(group) {
        for (const [name, value] of Object.entries(StringTableLocales)) {
            if (value === group) return name;
        }
        return 'Unknown';
    }

    /**
     * Get resource type name
     */
    _getResourceTypeName(type) {
        for (const [name, value] of Object.entries(ResourceTypes)) {
            if (value === type) return name;
        }
        return 'Unknown';
    }

    /**
     * Get package statistics
     */
    getStats() {
        const typeBreakdown = new Map();
        let totalSize = 0;

        for (const entry of this.entries) {
            const typeName = this._getResourceTypeName(entry.type);
            if (!typeBreakdown.has(typeName)) {
                typeBreakdown.set(typeName, { count: 0, size: 0 });
            }
            
            const stats = typeBreakdown.get(typeName);
            stats.count++;
            stats.size += entry.size;
            totalSize += entry.size;
        }

        return {
            totalResources: this.entries.length,
            packageSize: this.buffer.length,
            dataSize: totalSize,
            typeBreakdown: Object.fromEntries(typeBreakdown)
        };
    }

    /**
     * Clear resource cache
     */
    clearCache() {
        this.resourceCache.clear();
    }
}

export default DBPFPackage;
