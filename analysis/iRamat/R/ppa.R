# Install if necessary
# install.packages("imager")
library(imager)
library(spatstat.geom)
library(spatstat)

# Load image
root <- "https://raw.githubusercontent.com/zoometh/iramat-test-functions/master/analysis/iRamat/R/inst/extdata/"
img.paths <- c("clustered_distribution.png", "random_distribution.png", "regular_distribution.png")
for (i in seq(1, length(img.paths))){
  # i <- 3
  print(paste0("Read: ", img.paths[i]))
  img.path <- paste0(root, img.paths[i])
  img <- load.image(img.path)
  
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
  
  # Tests
  quadrat.test(pp, nx = 5, ny = 5) # If p < 0.05 → the pattern is likely non-random (either clustered or regular).
  #
  K <- Kest(pp)
  plot(K)
  #
  G <- Gest(pp)
  plot(G)
}

#   | Method       | Random      | Clustered | Regular   |
#   | ------------ | ----------- | --------- | --------- |
#   | Quadrat Test | p > 0.05    | p < 0.05  | p < 0.05  |
#   | Ripley’s K   | Matches CSR | Above CSR | Below CSR |
#   | G-function   | Matches CSR | Steeper   | Flatter   |
  

