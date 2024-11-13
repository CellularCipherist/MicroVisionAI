// Variables will be inserted here by the Python script
// var inputPath = "/path/to/input/file";
// var outputDir = "/path/to/output/directory/";
// var originalFileName = "original_file_name.czi";
// var minSize = 10;
// var maxSize = "Infinity";
// var minCircularity = 0.00;
// var maxCircularity = 1.00;

// Function to log output files and directories
function logOutput(key, value) {
    File.append(key + ": " + value + "\n", outputDir + File.separator + "output_log.txt");
}

// Define subdirectories
imagesDir = "Images";
statisticsDir = "Statistics";
metadataDir = "Metadata";

// Create output directories
File.makeDirectory(outputDir + File.separator + imagesDir);
File.makeDirectory(outputDir + File.separator + statisticsDir);
File.makeDirectory(outputDir + File.separator + metadataDir);

// Log subdirectories
logOutput("IMAGES_DIR", imagesDir);
logOutput("STATISTICS_DIR", statisticsDir);
logOutput("METADATA_DIR", metadataDir);

// Enable Bio-Formats Macro Extensions
run("Bio-Formats Macro Extensions");

// Initialize the file
Ext.setId(inputPath);
Ext.getSeriesCount(seriesCount);
Ext.getSizeX(width);
Ext.getSizeY(height);
Ext.getSizeC(channels);
Ext.getSizeZ(slices);
Ext.getSizeT(frames);
Ext.getPixelType(pixelType);

// Extract essential metadata
Ext.getImageCreationDate(creationDate);

// Open the image
Ext.openImagePlus(inputPath);

// Log image information
IJ.log("IMAGE_INFO_START");
IJ.log(originalFileName + "," + width + "," + height + "," + channels + "," + slices + "," + frames + "," + pixelType);
IJ.log("IMAGE_INFO_END");

// Log metadata
logOutput("WIDTH", width);
logOutput("HEIGHT", height);
logOutput("CHANNELS", channels);
logOutput("SLICES", slices);
logOutput("FRAMES", frames);
logOutput("PIXEL_TYPE", pixelType);
logOutput("CREATION_DATE", creationDate);

// Save metadata to a file
metadataPath = outputDir + File.separator + metadataDir + File.separator + originalFileName + "_metadata.txt";
metadataContent = "Original File: " + originalFileName + "\n" +
                  "Dimensions: " + width + "x" + height + "x" + channels + "x" + slices + "x" + frames + "\n" +
                  "Pixel Type: " + pixelType + "\n" +
                  "Creation Date: " + creationDate + "\n";

// Check if a metadata file with the same content already exists
existingFiles = getFileList(outputDir + File.separator + metadataDir);
metadataExists = false;
for (i = 0; i < existingFiles.length; i++) {
    if (startsWith(existingFiles[i], originalFileName)) {
        existingPath = outputDir + File.separator + metadataDir + File.separator + existingFiles[i];
        if (File.exists(existingPath)) {
            existingContent = File.openAsString(existingPath);
            if (existingContent == metadataContent) {
                metadataExists = true;
                break;
            }
        }
    }
}

if (!metadataExists) {
    File.saveString(metadataContent, metadataPath);
    logOutput("OUTPUT_FILE", metadataPath);
    print("Saved metadata: " + metadataPath);
} else {
    print("Metadata file with same content already exists. Skipping creation.");
}
//


// User-provided macro script starts here
{user_macro}



// Close all images
run("Close All");

IJ.log("MACRO_EXECUTION_COMPLETED");
