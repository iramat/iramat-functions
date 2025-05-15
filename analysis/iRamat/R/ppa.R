# Install if necessary
install.packages("imager")
library(spatstat.geom)
library(spatstat.core)

library(imager)

# Load image
img <- load.image("path/to/your/image.png")

# Convert to grayscale if needed
img_gray <- grayscale(img)

# Threshold to binary (assuming black points on white background)
img_bin <- img_gray < 0.5

# Extract black pixel coordinates
coords <- which(img_bin, arr.ind = TRUE)
points_df <- data.frame(x = coords[, 2], y = coords[, 1])  # Swap due to matrix order

# Define window (image is 100x100)
window <- owin(xrange = c(0, 100), yrange = c(0, 100))

# Create point pattern object
pp <- ppp(points_df$x, points_df$y, window = window)
