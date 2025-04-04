# Microscope Control Repository

This repository provides comprehensive tools for controlling a microscope system. It streamlines the operation of various hardware components and enables precise imaging workflows.

## Features

### Hardware Integration

- **Microscope Control:**  
  Manage Nikon microscopes with flexible selection of objectives and focus devices (e.g., ZDrive, PFSOffset, MarZ).

- **Camera Interface:**  
  Configure Andor sCMOS cameras with customizable binning and exposure settings for optimal imaging.

- **DMD Management:**  
  Control a Digital Micromirror Device (DMD) to project predefined or custom masks for patterned illumination.

- **Lamp Control:**  
  Support for multiple lamp types, including pE-800, pE-4000, and DiaLamp. Adjust LED selection and intensity, and manage shutter states for precise light delivery.

### Autofocus

- **Multiple Methods:**  
  Choose from various autofocus algorithms such as Squared Gradient, OughtaFocus, and Manual Focus. Automatically optimize focus based on real-time image quality metrics.

- **Integration with Micro-Manager:**  
  Interface with Micro-Manager’s autofocus routines to achieve accurate and reproducible focus.

### Dish Calibration & Well Grid Management

- **Dish Calibration:**  
  Calibrate different dish formats (e.g., 35mm dishes, 96-well plates, Ibidi 8-well dishes) to automatically determine well positions. User prompts guide the process to capture key reference points (center and edge).

- **Well Grid Generation:**  
  Generate precise well grids that define imaging regions. Calculate optimal overlaps and employ efficient stage movement strategies (e.g., serpentine patterns) to cover all regions.

### Configuration & Utilities

- **JSON-Based Configuration:**  
  Load and save configuration and calibration settings using JSON files. Custom serialization and deserialization of key data classes (e.g., stage coordinates, well measurements) ensure consistency.

- **Image Processing:**  
  Utilities for image thresholding, centroid calculation, bounding box extraction, and normalization help prepare images for analysis.

- **Directory Management:**  
  Functions to locate the project root, create timestamped directories, and manage configuration files facilitate organized workflows.
