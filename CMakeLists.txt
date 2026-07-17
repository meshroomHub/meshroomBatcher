CMAKE_MINIMUM_REQUIRED(VERSION 3.16)

include(RezBuild)

# Don't have to rely on any compiler
project($ENV{REZ_BUILD_PROJECT_NAME} NONE)

# Info
message(STATUS "Installing ${REZ_BUILD_PROJECT_NAME}")

# Check if the install path is on the local packages or not.
# If we install on the local packages it will install via symlinks
# so that we can still develop without having to rebuild systematically.
# Handle cases where we can have multiple packages in REZ_LOCAL_PACKAGES_PATH.
set(LOCAL_RELEASE 0)
string(REPLACE ":" ";" LOCAL_PACKAGES_PATHS "$ENV{REZ_LOCAL_PACKAGES_PATH}")
foreach(LOCAL_PATH ${LOCAL_PACKAGES_PATHS})
    string(FIND "${CMAKE_INSTALL_PREFIX}" "${LOCAL_PATH}" _pos)
    if(_pos GREATER_EQUAL 0)
        set(LOCAL_RELEASE 1)
        break()
    endif()
endforeach()

if(LOCAL_RELEASE EQUAL 1)
    message(STATUS "Local release")
else()
    message(STATUS "Global release")
endif()


# Local build : create symlinks to python and resources
# Global build : copy files
if(LOCAL_RELEASE EQUAL 1)
    rez_install_dirs(python DESTINATION . LOCAL_SYMLINK)
    rez_install_dirs(mock DESTINATION . LOCAL_SYMLINK)
    rez_install_dirs(resources DESTINATION . LOCAL_SYMLINK)
    rez_install_files($ENV{REZ_BUILD_SOURCE_PATH}/.coveragerc DESTINATION . LOCAL_SYMLINK)
else()
    install(DIRECTORY $ENV{REZ_BUILD_SOURCE_PATH}/python DESTINATION ${CMAKE_INSTALL_PREFIX})
    install(DIRECTORY $ENV{REZ_BUILD_SOURCE_PATH}/mock DESTINATION ${CMAKE_INSTALL_PREFIX})
    install(DIRECTORY $ENV{REZ_BUILD_SOURCE_PATH}/resources USE_SOURCE_PERMISSIONS DESTINATION ${CMAKE_INSTALL_PREFIX})
    install(FILES $ENV{REZ_BUILD_SOURCE_PATH}/.coveragerc DESTINATION ${CMAKE_INSTALL_PREFIX})
endif()


# Copy Tests files only if build (local) (and not release (central))
if($ENV{REZ_BUILD_TYPE} STREQUAL "local")
    if(LOCAL_RELEASE EQUAL 1)
        rez_install_dirs(tests DESTINATION . LOCAL_SYMLINK)
        install(
            FILES $ENV{REZ_BUILD_SOURCE_PATH}/pyproject.toml
            DESTINATION ${CMAKE_INSTALL_PREFIX}
        )
    endif()
endif()
