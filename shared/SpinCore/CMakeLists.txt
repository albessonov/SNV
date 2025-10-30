cmake_minimum_required(VERSION 3.15)

# Название проекта
project(SpinCore LANGUAGES C)

# Тип сборки по умолчанию — Release
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Исходники
set(SOURCES
    Spin.c
)

# Создаем динамическую библиотеку (.dll)
add_library(SpinCore SHARED ${SOURCES})

# Настройки только для Windows + MSVC
if(MSVC)
    # Оптимизации и предупреждения
    target_compile_options(SpinCore PRIVATE
        /W3           # уровень предупреждений
        /O2           # оптимизация
        /GL           # whole program optimization
        /MD           # использовать DLL runtime
        /utf-8        # кодировка UTF-8
    )

    # Определения препроцессора
    target_compile_definitions(SpinCore PRIVATE
        NDEBUG
        _WINDOWS
        _USRDLL
        SPINCORE_EXPORTS
    )

    # Пути к include и lib
    target_include_directories(SpinCore PRIVATE
        "."
    )

    target_link_directories(SpinCore PRIVATE
        "."
    )

    # Линкуем внешнюю библиотеку
    target_link_libraries(SpinCore PRIVATE
        spinapi64
    )

    # Опции линковщика
    target_link_options(SpinCore PRIVATE
        /DLL
        /SUBSYSTEM:WINDOWS
        /OPT:REF
        /OPT:ICF
        /LTCG
    )
endif()

# Куда положить собранные файлы
set_target_properties(SpinCore PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    LIBRARY_OUTPUT_DIRECTORY "."
)

