cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(MeasurementWithSpheres)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/MeasurementWithSpheres")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "John Doe (AnyWare Corp.), Cagatay Alptekin (Non-Nocere)")
set(EXTENSION_DESCRIPTION "This is an example of a simple extension that creates spheres and calculate length angles at different positions.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/MeasurementWithSpheres.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/MeasurementWithSpheres/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(MeasurementWithSpheres)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
