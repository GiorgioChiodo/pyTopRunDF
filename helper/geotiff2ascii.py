import sys
import rasterio
import numpy as np

def geotiff_to_ascii(input_tiff, output_ascii):
    # Open the GeoTIFF file
    with rasterio.open(input_tiff) as src:
        # Read metadata
        width = src.width
        height = src.height
        transform = src.transform
        nodata = src.nodata if src.nodata is not None else -9999
        data = src.read(1)  # Read the first band (assuming single-band raster)

        # Replace NaN values with NODATA value
        data = np.where(np.isnan(data), nodata, data)

        # Extract metadata for ASCII header
        ncols = width
        nrows = height
        xllcorner = transform[2]
        yllcorner = transform[5] + transform[4] * height  # Adjust for the lower-left corner
        cellsize = transform[0]

    # Write the ASCII file
    with open(output_ascii, 'w') as f:
        f.write(f"ncols         {ncols}\n")
        f.write(f"nrows         {nrows}\n")
        f.write(f"xllcorner     {xllcorner}\n")
        f.write(f"yllcorner     {yllcorner}\n")
        f.write(f"cellsize      {cellsize}\n")
        f.write(f"NODATA_value  {nodata}\n")

        # Write the raster data row by row
        for row in data:
            f.write(" ".join(map(str, row)) + "\n")

    print(f"ASCII file successfully written to: {output_ascii}")

if __name__ == "__main__":
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 3:
        print("Usage: python geotiff_to_ascii.py <input_tiff> <output_ascii>")
        sys.exit(1)

    # Get the input and output file paths from the command line
    input_tiff = sys.argv[1]
    output_ascii = sys.argv[2]

    # Call the function
    geotiff_to_ascii(input_tiff, output_ascii)