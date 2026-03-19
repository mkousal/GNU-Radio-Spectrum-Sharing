find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_SPECTRUMSHARING gnuradio-spectrumSharing)

FIND_PATH(
    GR_SPECTRUMSHARING_INCLUDE_DIRS
    NAMES gnuradio/spectrumSharing/api.h
    HINTS $ENV{SPECTRUMSHARING_DIR}/include
        ${PC_SPECTRUMSHARING_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_SPECTRUMSHARING_LIBRARIES
    NAMES gnuradio-spectrumSharing
    HINTS $ENV{SPECTRUMSHARING_DIR}/lib
        ${PC_SPECTRUMSHARING_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-spectrumSharingTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_SPECTRUMSHARING DEFAULT_MSG GR_SPECTRUMSHARING_LIBRARIES GR_SPECTRUMSHARING_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_SPECTRUMSHARING_LIBRARIES GR_SPECTRUMSHARING_INCLUDE_DIRS)
