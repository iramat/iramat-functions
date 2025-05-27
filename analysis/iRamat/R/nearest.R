# pour le fer puddlé

pathFolder <- "C:/Users/TH282424/Rprojects/iramat-test-functions/analysis/iRamat/R/"
fileTauxInc <- "Taux d'inclusions-R217-3-macrox5.xlsx"

classes <- list(c(0, 100), c(101, 200), c(201, 300), c(301, 400), c(401, 500), c(501, 600), c(601, 700), c(701, 800), c(801, 900), c(901, 1000), c(1001, 1100), c(1101, 1200), c(1201, 1300), c(1301, 1400), c(1401, 1500), c(1501, 1600), c(1601, 1700), c(1701, 1800), c(1801, 1900), c(1901, 2000), c(2001, 2100), c(2101, 2200), c(2201, 2300), c(2301, 2400), c(2401, 2500), c(2501, 2600), c(2601, 2700), c(2701, 2800), c(2801, 2900), c(2901, 3000), c(3001, 3100), c(3101, 3200), c(3201, 3300), c(3301, 3400), c(3401, 3500), c(3501, 3600), c(3601, 3700), c(3701, 3800), c(3801, 3900), c(3901, 4000), c(4001, 4100), c(4101, 4200), c(4201, 4300), c(4301, 4400), c(4401, 4500), c(4501, 4600), c(4601, 4700), c(4701, 4800), c(4801, 4900), c(4901, 5000), c(5001, 5100), c(5101, 5200), c(5201, 5300), c(5301, 5400), c(5401, 5500), c(5501, 5600), c(5601, 5700), c(5701, 5800), c(5801, 5900), c(5901, 6000), c(6001, 6100), c(6101, 6200), c(6201, 6300), c(6301, 6400), c(6401, 6500), c(6501, 6600), c(6601, 6700), c(6701, 6800), c(6801, 6900), c(6900, 7000), c(7001, 7100), c(7101, 7200), c(7201, 7300), c(7301, 7400), c(7401, 7500))

df <- openxlsx::read.xlsx(paste0(pathFolder, fileTauxInc))
df.simple <- df[, c("X", "Nearest.Neighbor.Distance")]
df.simple$nnd <- df.simple$Nearest.Neighbor.Distance
df.simple$Nearest.Neighbor.Distance <- NULL

class_labels <- sapply(classes, function(x) paste0("X_", x[1], "_", x[2]))

# Add class label to df.simple
df.simple$X_class <- NA
for (i in seq_along(classes)) {
  range <- classes[[i]]
  label <- class_labels[i]
  idx <- !is.na(df.simple$X) & df.simple$X >= range[1] & df.simple$X <= range[2]
  df.simple$X_class[idx] <- label
}

# Aggregate mean NND by X class
library(dplyr)
library(stringr)

df.nnd_means <- df.simple %>%
  filter(!is.na(X_class) & !is.na(nnd)) %>%
  group_by(X_class) %>%
  summarise(mean_nnd = mean(nnd), .groups = "drop")

# View result
head(df.nnd_means)
df.nnd_means$from <- NA
df.nnd_means$to <- NA

for(i in seq(1, nrow(df.nnd_means))){
  a <- df.nnd_means[i, "X_class"]
  a <- gsub("X_", "", a)
  a <- str_split(a, "_")[[1]]
  df.nnd_means[i, "X_class"] <- paste0(a[1], "-", a[2], "µm")
  df.nnd_means[i, "from"] <- as.integer(a[1])
  df.nnd_means[i, "to"] <- as.integer(a[2])
}
df.sorted <- df.nnd_means %>%
  arrange(from, to)
df.sorted$from <- df.sorted$to <- NULL
print(df.sorted, n = 50)

library(ggplot2)

# Ensure X_class is an ordered factor to keep the x-axis in class order
df.sorted$X_class <- factor(df.sorted$X_class, levels = df.sorted$X_class)

# Plot
ggplot(df.sorted, aes(x = X_class, y = mean_nnd, group = 1)) +
  geom_line(color = "steelblue") +
  geom_point(color = "darkred") +
  theme_minimal() +
  labs(
    title = "Mean NND by X Class",
    x = "X Class (µm)",
    y = "Mean Nearest Neighbor Distance"
  ) +
  theme(
    axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)
  )

###################################

class_labels <- sapply(classes, function(x) paste0("_", x[1], "_", x[2], "µm"))

# 2. Create an empty list to store compacted vectors
compact_columns <- list()

# 3. For each class, extract valid X values and store in list
for (i in seq_along(classes)) {
  range <- classes[[i]]
  col_name <- class_labels[i]
  
  valid_vals <- df$X[!is.na(df$X) & df$X >= range[1] & df$X <= range[2]]
  compact_columns[[col_name]] <- valid_vals
}

# 4. Determine the maximum length to pad columns
max_len <- max(sapply(compact_columns, length))

# 5. Pad each column with NAs so they align
compact_padded <- lapply(compact_columns, function(col) {
  length(col) <- max_len  # extends with NAs automatically
  return(col)
})

# 6. Bind into a new dataframe
df_compact <- as.data.frame(compact_padded)

# 7. View result
head(df_compact)

#########


colMeans(df_compact, na.rm = TRUE)
