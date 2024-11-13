function logOutput(key, value) {{
    print(key + ": " + value);
    File.append(key + ": " + value, "{output_log_path}");
}}

setBatchMode(true);
run("Bio-Formats Macro Extensions");

print("Initializing file: {input_path}");
Ext.setId("{input_path}");
Ext.getSeriesCount(seriesCount);
print("Series count: " + seriesCount);

if (seriesCount == 0) {{
    logOutput("ERROR", "Failed to read the image file");
    exit("Macro canceled");
}}

Ext.getSizeX(width);
Ext.getSizeY(height);
Ext.getSizeC(channels);
Ext.getSizeZ(slices);
Ext.getSizeT(frames);
Ext.getPixelType(pixelType);
Ext.getImageCreationDate(creationDate);

print("Image dimensions: " + width + "x" + height + "x" + channels + "x" + slices + "x" + frames);

print("Opening image with Bio-Formats");
Ext.openImagePlus("{input_path}");

if (nImages == 0) {{
    logOutput("ERROR", "Failed to open the image with Bio-Formats");
    exit("Macro canceled");
}}

originalID = getImageID();
print("Opened original image with ID: " + originalID);

run("8-bit");

// Generate Maximum Intensity Projection
if (slices > 1) {{
    run("Z Project...", "projection=[Max Intensity]");
}}

// Enhance contrast
for (c = 1; c <= channels; c++) {{
    Stack.setChannel(c);
    run("Enhance Contrast", "saturated=0.35");
}}

if (channels > 1) {{
    run("Make Composite");
}}

// Save the MIP as a TIFF
previewPath = "{output_dir}" + File.separator + "preview_{filename}";

// Remove any existing file extension before appending ".tif"
if (previewPath.contains(".")) {{
    previewPath = previewPath.substring(0, previewPath.lastIndexOf('.'));
}}

previewPath += ".tif";  // Ensuring the correct extension
saveAs("Tiff", previewPath);
logOutput("PREVIEW_PATH", previewPath);

// Save metadata
metadata = "Original File: " + "{filename}" + "\\n" +
        "Dimensions: " + width + "x" + height + "x" + channels + "x" + slices + "x" + frames + "\\n" +
        "Pixel Type: " + pixelType + "\\n" +
        "Creation Date: " + creationDate;
metadataPath = "{output_dir}" + File.separator + "{filename}_metadata.txt";
File.saveString(metadata, metadataPath);
logOutput("METADATA_PATH", metadataPath);

close();

setBatchMode(false);
print("Macro execution completed.");
