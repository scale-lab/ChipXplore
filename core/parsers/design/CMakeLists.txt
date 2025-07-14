cmake_minimum_required(VERSION 3.14)
project(OpenDBProject)

set(CMAKE_CXX_STANDARD 17)

# Specify the path to OpenDB installation
set(OPENDB_DIR $ENV{OPENROAD_HOME} CACHE PATH "Path to OpenDB installation")

# Include directories
include_directories(${OPENDB_DIR}/include)

# Add your source files
add_executable(opendb_parser parser.cpp)

# Link against OpenDB
target_link_libraries(opendb_parser 
    ${OPENDB_DIR}/lib/libodb.a
    ${OPENDB_DIR}/lib/libtcl8.6.a  # OpenDB often requires Tcl
    dl  # Required for dynamic linking
    m   # Math library
    pthread
)

# If you're using any C++17 features that require linking to stdc++fs
if(CMAKE_COMPILER_IS_GNUCXX AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS 9.1)
    target_link_libraries(opendb_parser stdc++fs)
endif()