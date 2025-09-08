import fs from 'fs';
import path from 'path';
import { DBPFPackage, ResourceTypes, StringTableLocales, hexU32, hexU64 } from './dbpf-parser.js';

/**
 * Enhanced Sims 4 Package Parser using custom DBPF implementation
 * 
 * This replaces the @s4tk/models dependency with our own DBPF parser
 * that can handle compressed and binary package files properly.
 */

/**
 * Read and parse a package file
 */
export function readPackageFile(packageFilepath) {
    const absPath = path.isAbsolute(packageFilepath) ? packageFilepath : path.resolve(process.cwd(), packageFilepath);
    
    if (!fs.existsSync(absPath)) {
        throw new Error(`Package file not found: ${absPath}`);
    }
    
    return DBPFPackage.fromFile(absPath);
}

/**
 * List all resources in the package
 */
export function listResources(pkg) {
    return pkg.entries.map(entry => ({
        type: entry.type,
        group: entry.group,
        instance: entry.instance,
        typeHex: hexU32(entry.type),
        groupHex: hexU32(entry.group),
        instanceHex: hexU64(entry.instance),
        typeName: pkg._getResourceTypeName(entry.type),
        size: entry.size,
        compressed: entry.isCompressed,
        offset: entry.offset
    }));
}

/**
 * Build name mapping index from package (using NameMapResource)
 */
export function buildStblIndex(pkg) {
    return pkg.getNameMappings();
}

/**
 * List name mappings with filtering (using NameMapResource)
 */
export function listStringTableValues(pkg, localeFilter = null, valueIncludes = null) {
    const nameMappings = pkg.getNameMappings();
    const result = [];
    
    for (const [instance, name] of nameMappings.entries()) {
        if (valueIncludes && !name.toLowerCase().includes(valueIncludes.toLowerCase())) continue;
        
        result.push({
            locale: 'Default', // NameMapResource doesn't have locales
            key: Number(instance), // Convert BigInt to Number for consistency
            keyHex: hexU64(instance),
            value: name.trim()
        });
    }
    
    return result;
}

/**
 * List CAS Parts in the package
 */
export function listCasParts(pkg) {
    const casEntries = pkg.getCASParts();
    
    return casEntries.map(entry => ({
        type: entry.type,
        group: entry.group,
        instance: entry.instance,
        typeHex: hexU32(entry.type),
        groupHex: hexU32(entry.group),
        instanceHex: hexU64(entry.instance),
        name: null, // Will be populated by matching with string tables
        size: entry.size,
        compressed: entry.isCompressed
    }));
}

/**
 * Find hair style candidates from name mappings
 */
export function listHairStyleCandidates(pkg, locale = 'English') {
    const values = listStringTableValues(pkg, null, null); // locale is ignored for NameMapResource
    const hairTerms = [
        'hair', 'hairstyle', 'bangs', 'afro', 'braid', 'curly', 'wavy', 'straight', 
        'buzz', 'mohawk', 'ponytail', 'pigtail', 'bob', 'pixie', 'shag', 'updo',
        'dreadlock', 'cornrow', 'fade', 'undercut', 'fringe', 'waves', 'coils'
    ];
    
    const candidates = values.filter(v => 
        hairTerms.some(term => v.value.toLowerCase().includes(term))
    );
    
    // Remove duplicates
    const seen = new Set();
    const names = [];
    
    for (const { value } of candidates) {
        const key = value.trim();
        if (!seen.has(key) && key.length > 0) {
            seen.add(key);
            names.push(key);
        }
    }
    
    return names.sort();
}

/**
 * Build CAS hair index with enhanced matching using NameMapResource
 */
export function buildCasHairIndex(pkg, locale = 'English') {
    const casParts = listCasParts(pkg);
    const hairNames = listHairStyleCandidates(pkg, locale);
    const nameMappings = pkg.getNameMappings();
    
    // Try to match CAS parts with name mappings
    const enhancedCasParts = casParts.map(part => {
        let matchedName = null;
        
        // Look for name mapping that matches this CAS part instance
        const partInstance = typeof part.instance === 'bigint' ? part.instance : BigInt(part.instance);
        
        if (nameMappings.has(partInstance)) {
            matchedName = nameMappings.get(partInstance).trim();
        }
        
        return {
            ...part,
            name: matchedName
        };
    });
    
    return {
        casPartInstances: enhancedCasParts.map(c => ({
            instance: c.instance,
            instanceHex: c.instanceHex,
            name: c.name,
            size: c.size,
            compressed: c.compressed
        })),
        hairNames,
        totalCasParts: casParts.length,
        namedCasParts: enhancedCasParts.filter(p => p.name).length,
        totalNameMappings: nameMappings.size
    };
}

/**
 * Get detailed package information
 */
export function getPackageInfo(pkg) {
    const stats = pkg.getStats();
    const nameMappings = pkg.getNameMappings();
    const casPartCount = pkg.getCASParts().length;
    
    return {
        version: pkg.header.version,
        totalResources: stats.totalResources,
        packageSize: stats.packageSize,
        typeBreakdown: stats.typeBreakdown,
        nameMapCount: nameMappings.size,
        casPartCount,
        createdDate: new Date(pkg.header.createdDate * 1000).toISOString(),
        modifiedDate: new Date(pkg.header.modifiedDate * 1000).toISOString(),
        isCompressedPackage: pkg.entries.some(e => e.isCompressed)
    };
}

/**
 * Extract specific resource data
 */
export function extractResourceData(pkg, type, group, instance) {
    const entry = pkg.findResource(type, group, instance);
    if (!entry) {
        return null;
    }
    
    const data = pkg.getResourceData(entry);
    return {
        entry: {
            type: entry.type,
            group: entry.group,
            instance: entry.instance,
            typeHex: hexU32(entry.type),
            groupHex: hexU32(entry.group),
            instanceHex: hexU64(entry.instance),
            size: entry.size,
            compressed: entry.isCompressed
        },
        data: data
    };
}

/**
 * Find resources by type with additional metadata
 */
export function findResourcesByType(pkg, resourceType) {
    const entries = pkg.findResourcesByType(resourceType);
    
    return entries.map(entry => ({
        type: entry.type,
        group: entry.group,
        instance: entry.instance,
        typeHex: hexU32(entry.type),
        groupHex: hexU32(entry.group),
        instanceHex: hexU64(entry.instance),
        typeName: pkg._getResourceTypeName(entry.type),
        size: entry.size,
        compressed: entry.isCompressed,
        offset: entry.offset
    }));
}

/**
 * Search for resources by pattern
 */
export function searchResources(pkg, options = {}) {
    const { type, group, instancePattern, namePattern } = options;
    let results = pkg.entries;
    
    // Filter by type if specified
    if (type !== undefined) {
        results = results.filter(entry => entry.type === type);
    }
    
    // Filter by group if specified
    if (group !== undefined) {
        results = results.filter(entry => entry.group === group);
    }
    
    // Filter by instance pattern if specified
    if (instancePattern) {
        const pattern = new RegExp(instancePattern, 'i');
        results = results.filter(entry => 
            pattern.test(entry.instance.toString(16)) ||
            pattern.test(entry.instance.toString())
        );
    }
    
    // If searching by name, get name mappings and match
    if (namePattern) {
        const nameMappings = pkg.getNameMappings();
        const pattern = new RegExp(namePattern, 'i');
        const matchingInstances = new Set();
        
        for (const [instance, name] of nameMappings.entries()) {
            if (pattern.test(name)) {
                matchingInstances.add(instance);
                matchingInstances.add(Number(instance)); // Also add as number for comparison
            }
        }
        
        results = results.filter(entry => {
            const entryInstance = typeof entry.instance === 'bigint' ? entry.instance : BigInt(entry.instance);
            return matchingInstances.has(entryInstance) || 
                   matchingInstances.has(Number(entryInstance));
        });
    }
    
    return results.map(entry => ({
        type: entry.type,
        group: entry.group,
        instance: entry.instance,
        typeHex: hexU32(entry.type),
        groupHex: hexU32(entry.group),
        instanceHex: hexU64(entry.instance),
        typeName: pkg._getResourceTypeName(entry.type),
        size: entry.size,
        compressed: entry.isCompressed
    }));
}

/**
 * Validate package integrity
 */
export function validatePackage(pkg) {
    const issues = [];
    
    // Check header
    if (!pkg.header) {
        issues.push('Missing or invalid package header');
        return { valid: false, issues };
    }
    
    // Check entries
    if (pkg.entries.length === 0) {
        issues.push('No resources found in package');
    }
    
    // Check for invalid entries
    let invalidEntries = 0;
    for (const entry of pkg.entries) {
        if (entry.offset === 0 || entry.size === 0) {
            invalidEntries++;
        }
        
        // Check if offset is within file bounds
        if (entry.offset + entry.size > pkg.buffer.length) {
            issues.push(`Resource extends beyond file: ${hexU64(entry.instance)}`);
        }
    }
    
    if (invalidEntries > 0) {
        issues.push(`Found ${invalidEntries} entries with invalid offset/size`);
    }
    
    // Try to read a few resources to test decompression
    const testEntries = pkg.entries.slice(0, Math.min(5, pkg.entries.length));
    let decompressionErrors = 0;
    
    for (const entry of testEntries) {
        try {
            pkg.getResourceData(entry);
        } catch (error) {
            decompressionErrors++;
        }
    }
    
    if (decompressionErrors > 0) {
        issues.push(`${decompressionErrors} resources failed to decompress properly`);
    }
    
    return {
        valid: issues.length === 0,
        issues,
        stats: {
            totalResources: pkg.entries.length,
            invalidEntries,
            decompressionErrors,
            packageSize: pkg.buffer.length
        }
    };
}

// Export the ResourceTypes and StringTableLocales for convenience
export { ResourceTypes, StringTableLocales };

// Default export with all functions
export default {
    readPackageFile,
    listResources,
    buildStblIndex,
    listStringTableValues,
    listCasParts,
    listHairStyleCandidates,
    buildCasHairIndex,
    getPackageInfo,
    extractResourceData,
    findResourcesByType,
    searchResources,
    validatePackage,
    ResourceTypes,
    StringTableLocales
};
