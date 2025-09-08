#!/usr/bin/env node
import { 
    readPackageFile, 
    listResources, 
    listCasParts, 
    listHairStyleCandidates, 
    buildCasHairIndex,
    getPackageInfo,
    validatePackage,
    searchResources,
    listStringTableValues,
    ResourceTypes 
} from './ts4-package-parser-custom.js';
import JSONbig from "json-bigint";

function printHelp() {
    console.log('Usage: node test-custom-parser.js <path-to-package> [options]');
    console.log('');
    console.log('Options:');
    console.log('  --info       Show detailed package information');
    console.log('  --validate   Validate package integrity');
    console.log('  --resources  List all resources (first 20)');
    console.log('  --hair       List CASP entries (hair CAS parts)');
    console.log('  --names      List hair-like names from string tables');
    console.log('  --stbl       List string table values (first 20)');
    console.log('  --search     Search resources (use with --type, --name, etc.)');
    console.log('  --type <hex> Filter by resource type (e.g., 0x220557DA for STBL)');
    console.log('  --name <str> Search by name pattern');
    console.log('  --verbose    Show detailed output');
    console.log('');
    console.log('Examples:');
    console.log('  node test-custom-parser.js package.package --info');
    console.log('  node test-custom-parser.js package.package --hair --names');
    console.log('  node test-custom-parser.js package.package --search --type 0x220557DA');
    console.log('  node test-custom-parser.js package.package --search --name "hair"');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
        printHelp();
        process.exit(args.length === 0 ? 1 : 0);
    }
    
    const filepath = args[0];
    const options = {
        info: args.includes('--info'),
        validate: args.includes('--validate'),
        resources: args.includes('--resources'),
        hair: args.includes('--hair'),
        names: args.includes('--names'),
        stbl: args.includes('--stbl'),
        search: args.includes('--search'),
        verbose: args.includes('--verbose'),
        type: null,
        name: null
    };
    
    // Parse additional options
    const typeIndex = args.indexOf('--type');
    if (typeIndex !== -1 && typeIndex + 1 < args.length) {
        const typeStr = args[typeIndex + 1];
        options.type = typeStr.startsWith('0x') ? parseInt(typeStr, 16) : parseInt(typeStr);
    }
    
    const nameIndex = args.indexOf('--name');
    if (nameIndex !== -1 && nameIndex + 1 < args.length) {
        options.name = args[nameIndex + 1];
    }

    console.log(`🔍 Parsing package: ${filepath}`);
    console.log('📦 Using custom DBPF parser (supports compression & binary files)');
    console.log('');

    try {
        // Read the package file
        const startTime = Date.now();
        const pkg = readPackageFile(filepath);
        const parseTime = Date.now() - startTime;
        
        console.log(`✅ Package parsed successfully in ${parseTime}ms`);
        console.log('');

        // Show package info
        if (options.info) {
            console.log('📋 Package Information:');
            const info = getPackageInfo(pkg);
            console.log(`   Version: ${info.version}`);
            console.log(`   Total Resources: ${info.totalResources}`);
            console.log(`   Package Size: ${formatBytes(info.packageSize)}`);
            console.log(`   CAS Parts: ${info.casPartCount}`);
            console.log(`   String Table Locales: ${info.stringTableLocales.join(', ')}`);
            console.log(`   Contains Compressed Resources: ${info.isCompressedPackage ? 'Yes' : 'No'}`);
            console.log(`   Created: ${info.createdDate}`);
            console.log(`   Modified: ${info.modifiedDate}`);
            console.log('');
            
            console.log('📊 Resource Type Breakdown:');
            for (const [type, count] of Object.entries(info.typeBreakdown)) {
                console.log(`   ${type}: ${count}`);
            }
            console.log('');
        }

        // Validate package
        if (options.validate) {
            console.log('🔍 Validating package integrity...');
            const validation = validatePackage(pkg);
            
            if (validation.valid) {
                console.log('✅ Package is valid');
            } else {
                console.log('⚠️  Package has issues:');
                for (const issue of validation.issues) {
                    console.log(`   - ${issue}`);
                }
            }
            
            console.log(`📊 Validation stats:`);
            console.log(`   Total resources: ${validation.stats.totalResources}`);
            console.log(`   Invalid entries: ${validation.stats.invalidEntries}`);
            console.log(`   Decompression errors: ${validation.stats.decompressionErrors}`);
            console.log('');
        }

        // List resources
        if (options.resources) {
            console.log('📄 Resources (first 20):');
            const resources = listResources(pkg).slice(0, 20);
            for (const resource of resources) {
                const compressed = resource.compressed ? ' [COMPRESSED]' : '';
                console.log(`   ${resource.typeName} - ${resource.typeHex}:${resource.groupHex}:${resource.instanceHex} (${formatBytes(resource.size)})${compressed}`);
            }
            if (pkg.entries.length > 20) {
                console.log(`   ... and ${pkg.entries.length - 20} more resources`);
            }
            console.log('');
        }

        // Search resources
        if (options.search) {
            console.log('🔍 Searching resources...');
            const searchOptions = {};
            if (options.type) searchOptions.type = options.type;
            if (options.name) searchOptions.namePattern = options.name;
            
            const results = searchResources(pkg, searchOptions);
            
            // Get name mappings for displaying resource names
            const nameMappings = pkg.getNameMappings();
            
            console.log(`Found ${results.length} matching resources:`);
            
            const displayResults = results.slice(0, options.verbose ? 50 : 20);
            for (const resource of displayResults) {
                const compressed = resource.compressed ? ' [COMPRESSED]' : '';
                
                // Look up name from NameMapResource
                const resourceInstance = typeof resource.instance === 'bigint' ? resource.instance : BigInt(resource.instance);
                const resourceName = nameMappings.get(resourceInstance);
                const nameDisplay = resourceName ? ` - "${resourceName}"` : '';
                
                console.log(`   ${resource.typeName} - ${resource.instanceHex} (${formatBytes(resource.size)})${compressed}${nameDisplay}`);
            }
            
            if (results.length > displayResults.length) {
                console.log(`   ... and ${results.length - displayResults.length} more results`);
            }
            console.log('');
        }

        // Show CAS parts
        if (options.hair) {
            console.log('💇 CAS Parts (potential hair items):');
            const casParts = listCasParts(pkg);
            const displayParts = casParts.slice(0, options.verbose ? 50 : 10);
            
            for (const part of displayParts) {
                const compressed = part.compressed ? ' [COMPRESSED]' : '';
                const name = part.name ? ` - ${part.name}` : '';
                console.log(`   CASP ${part.instanceHex} (${formatBytes(part.size)})${compressed}${name}`);
            }
            
            if (casParts.length > displayParts.length) {
                console.log(`   ... and ${casParts.length - displayParts.length} more CAS parts`);
            }
            console.log('');
        }

        // Show hair names
        if (options.names) {
            console.log('💇 Hair Style Names (from string tables):');
            const hairNames = listHairStyleCandidates(pkg);
            const displayNames = hairNames.slice(0, options.verbose ? 100 : 20);
            
            for (const name of displayNames) {
                console.log(`   "${name}"`);
            }
            
            if (hairNames.length > displayNames.length) {
                console.log(`   ... and ${hairNames.length - displayNames.length} more hair names`);
            }
            console.log('');
        }

        // Show string tables
        if (options.stbl) {
            console.log('📝 String Table Values (first 20):');
            const stblValues = listStringTableValues(pkg, null, null).slice(0, 20);
            
            for (const entry of stblValues) {
                console.log(`   [${entry.locale}] ${entry.keyHex}: "${entry.value}"`);
            }
            console.log('');
        }

        // Build hair index if requested
        if (options.hair && options.names) {
            console.log('🔗 Building CAS Hair Index...');
            const index = buildCasHairIndex(pkg);
            console.log(`   Total CAS Parts: ${index.totalCasParts}`);
            console.log(`   Named CAS Parts: ${index.namedCasParts}`);
            console.log(`   Hair Names Found: ${index.hairNames.length}`);
            
            if (options.verbose) {
                console.log('   Sample matched parts:');
                const namedParts = index.casPartInstances.filter(p => p.name).slice(0, 5);
                for (const part of namedParts) {
                    console.log(`     ${part.instanceHex}: "${part.name}"`);
                }
            }
            console.log('');
        }

        // If no specific options were provided, show a summary
        if (!options.info && !options.validate && !options.resources && !options.hair && !options.names && !options.stbl && !options.search) {
            console.log('📋 Package Summary:');
            const info = getPackageInfo(pkg);
            console.log(`   📦 ${info.totalResources} resources in ${formatBytes(info.packageSize)} package`);
            console.log(`   💇 ${info.casPartCount} CAS parts found`);
            console.log(`   🌍 ${info.stringTableLocales.length} locales: ${info.stringTableLocales.join(', ')}`);
            console.log(`   🗜️  Compression: ${info.isCompressedPackage ? 'Yes' : 'No'}`);
            console.log('');
            console.log('💡 Use --help to see all available options');
        }

    } catch (error) {
        console.error('❌ Error parsing package:', error.message);
        if (options.verbose) {
            console.error('Stack trace:', error.stack);
        }
        process.exit(1);
    }
}

main().catch(err => {
    console.error('❌ Unexpected error:', err.message);
    process.exit(1);
});
